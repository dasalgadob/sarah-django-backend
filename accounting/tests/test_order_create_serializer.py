from decimal import Decimal

import pytest

from accounting.models import ItemPrice, OrderItem
from accounting.serializers.order_serializer import OrderCreateSerializer


def _order_payload(company, third_party, sale_type, payment_method, order_items):
    return {
        'order_type': 'sale',
        'company': company.id,
        'third_party': third_party.id,
        'sale_type': sale_type.id,
        'payment_method': payment_method.id,
        'order_items': order_items,
    }


@pytest.mark.django_db
class TestOrderCreateSerializerTaxComputation:
    def test_uses_item_price_when_no_unit_price_override_given(
        self, company, third_party, sale_type, payment_method, item_price,
    ):
        payload = _order_payload(company, third_party, sale_type, payment_method, [
            {'item_price': item_price.id, 'quantity': '2.00'},
        ])
        serializer = OrderCreateSerializer(data=payload)
        assert serializer.is_valid(), serializer.errors
        order = serializer.save()

        order_item = order.order_items.get()
        assert order_item.unit_price == item_price.price
        assert order_item.line_total == Decimal('200000.00')
        assert order_item.line_iva == Decimal('38000.00')  # 19% of 200000
        assert order_item.line_excise_tax == Decimal('0.00')
        assert order_item.line_total_with_taxes == Decimal('238000.00')

    def test_uses_item_price_when_unit_price_equals_item_price(
        self, company, third_party, sale_type, payment_method, item_price,
    ):
        payload = _order_payload(company, third_party, sale_type, payment_method, [
            {'item_price': item_price.id, 'quantity': '1.00', 'unit_price': str(item_price.price)},
        ])
        serializer = OrderCreateSerializer(data=payload)
        assert serializer.is_valid(), serializer.errors
        order = serializer.save()

        order_item = order.order_items.get()
        assert order_item.unit_price == item_price.price
        assert order_item.line_iva == Decimal('19000.00')

    def test_applies_unit_price_override_and_recomputes_taxes(
        self, company, third_party, sale_type, payment_method, item_price,
    ):
        payload = _order_payload(company, third_party, sale_type, payment_method, [
            {'item_price': item_price.id, 'quantity': '1.00', 'unit_price': '80000.00'},
        ])
        serializer = OrderCreateSerializer(data=payload)
        assert serializer.is_valid(), serializer.errors
        order = serializer.save()

        order_item = order.order_items.get()
        assert order_item.unit_price == Decimal('80000.00')
        assert order_item.line_total == Decimal('80000.00')
        assert order_item.line_iva == Decimal('15200.00')  # 19% of 80000, not the original 19000
        assert order_item.line_total_with_taxes == Decimal('95200.00')

    def test_ignores_payload_iva_and_total_fields_entirely(
        self, company, third_party, sale_type, payment_method, item_price,
    ):
        """Even if a client tries to send line_iva/line_total_with_taxes, they're not accepted fields."""
        payload = _order_payload(company, third_party, sale_type, payment_method, [
            {
                'item_price': item_price.id, 'quantity': '1.00',
                'line_iva': '999999.00', 'line_total_with_taxes': '999999.00',
            },
        ])
        serializer = OrderCreateSerializer(data=payload)
        assert serializer.is_valid(), serializer.errors
        order = serializer.save()

        order_item = order.order_items.get()
        assert order_item.line_iva == Decimal('19000.00')
        assert order_item.line_total_with_taxes == Decimal('119000.00')

    def test_includes_excise_tax_when_item_has_excise_rate(
        self, company, third_party, sale_type, payment_method, item, excise_tax_rate,
    ):
        item.excise_tax_type = excise_tax_rate.excise_tax_type
        item.excise_tax_rate = excise_tax_rate
        item.save()
        item_price = ItemPrice.objects.create(
            item=item, company=company, item_price_type=ItemPrice.SELLING,
            price='100000.00', iva='19000.00', excise_tax='10000.00', total='129000.00',
        )

        payload = _order_payload(company, third_party, sale_type, payment_method, [
            {'item_price': item_price.id, 'quantity': '1.00'},
        ])
        serializer = OrderCreateSerializer(data=payload)
        assert serializer.is_valid(), serializer.errors
        order = serializer.save()

        order_item = order.order_items.get()
        assert order_item.line_excise_tax == Decimal('10000.00')
        assert order_item.line_total_with_taxes == Decimal('129000.00')

    def test_order_totals_aggregate_across_multiple_items(
        self, company, third_party, sale_type, payment_method, item_price, item, item_group, unit_measure,
    ):
        from accounting.models import Item

        second_item = Item.objects.create(
            base_code='PANTS001', base_name='Pants', name='Pants',
            item_group=item_group, unit_measure=unit_measure, company=company,
        )
        second_price = ItemPrice.objects.create(
            item=second_item, company=company, item_price_type=ItemPrice.SELLING,
            price='50000.00', iva='0.00', excise_tax='0.00', total='50000.00',
        )

        payload = _order_payload(company, third_party, sale_type, payment_method, [
            {'item_price': item_price.id, 'quantity': '1.00'},
            {'item_price': second_price.id, 'quantity': '2.00'},
        ])
        serializer = OrderCreateSerializer(data=payload)
        assert serializer.is_valid(), serializer.errors
        order = serializer.save()

        assert order.subtotal == Decimal('200000.00')  # 100000 + (50000*2)
        assert order.total_iva == Decimal('19000.00')
        assert order.total_amount == Decimal('219000.00')
        assert OrderItem.objects.filter(order=order).count() == 2

    def test_rejects_nonexistent_item_price_id(self, company, third_party, sale_type, payment_method):
        payload = _order_payload(company, third_party, sale_type, payment_method, [
            {'item_price': 999999, 'quantity': '1.00'},
        ])
        serializer = OrderCreateSerializer(data=payload)

        assert not serializer.is_valid()
        assert 'order_items' in serializer.errors

    def test_requires_at_least_one_order_item(self, company, third_party, sale_type, payment_method):
        payload = _order_payload(company, third_party, sale_type, payment_method, [])
        serializer = OrderCreateSerializer(data=payload)

        assert not serializer.is_valid()
        assert 'order_items' in serializer.errors
