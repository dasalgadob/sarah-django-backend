from decimal import Decimal

import pytest

from accounting.models import Order


@pytest.mark.django_db
class TestOrderCreateEndpoint:
    def test_post_order_computes_taxes_from_item_rates(
        self, api_client, company, third_party, sale_type, payment_method, item_price,
    ):
        payload = {
            'order_type': 'sale',
            'company': company.id,
            'third_party': third_party.id,
            'sale_type': sale_type.id,
            'payment_method': payment_method.id,
            'order_items': [
                {'item_price': item_price.id, 'quantity': '2.00'},
            ],
        }

        response = api_client.post('/api/orders/', payload, format='json')

        assert response.status_code == 201, response.data

        order = Order.objects.get(company=company)
        order_item = order.order_items.get()
        assert order_item.unit_price == item_price.price
        assert order_item.line_iva == Decimal('38000.00')
        assert order.total_amount == Decimal('238000.00')

    def test_post_order_with_unit_price_override(
        self, api_client, company, third_party, sale_type, payment_method, item_price,
    ):
        payload = {
            'order_type': 'sale',
            'company': company.id,
            'third_party': third_party.id,
            'sale_type': sale_type.id,
            'payment_method': payment_method.id,
            'order_items': [
                {'item_price': item_price.id, 'quantity': '1.00', 'unit_price': '80000.00'},
            ],
        }

        response = api_client.post('/api/orders/', payload, format='json')

        assert response.status_code == 201, response.data

        order = Order.objects.get(company=company)
        order_item = order.order_items.get()
        assert order_item.unit_price == Decimal('80000.00')
        assert order_item.line_iva == Decimal('15200.00')

    def test_post_order_requires_authentication(self, company, third_party, sale_type, payment_method, item_price):
        from rest_framework.test import APIClient

        payload = {
            'order_type': 'sale',
            'company': company.id,
            'third_party': third_party.id,
            'sale_type': sale_type.id,
            'payment_method': payment_method.id,
            'order_items': [{'item_price': item_price.id, 'quantity': '1.00'}],
        }

        response = APIClient().post('/api/orders/', payload, format='json')

        assert response.status_code == 401


def _create_order(api_client, company, third_party, sale_type, payment_method, order_items):
    payload = {
        'order_type': 'sale',
        'company': company.id,
        'third_party': third_party.id,
        'sale_type': sale_type.id,
        'payment_method': payment_method.id,
        'order_items': order_items,
    }
    response = api_client.post('/api/orders/', payload, format='json')
    assert response.status_code == 201, response.data
    return Order.objects.get(company=company)


@pytest.mark.django_db
class TestOrderUpdateEndpoint:
    def test_patch_updates_existing_item_by_id(
        self, api_client, company, third_party, sale_type, payment_method, item_price,
    ):
        order = _create_order(
            api_client, company, third_party, sale_type, payment_method,
            [{'item_price': item_price.id, 'quantity': '1.00'}],
        )
        order_item = order.order_items.get()

        response = api_client.patch(f'/api/orders/{order.id}/', {
            'order_items': [
                {'id': order_item.id, 'item_price': item_price.id, 'quantity': '3.00'},
            ],
        }, format='json')

        assert response.status_code == 200, response.data
        order_item.refresh_from_db()
        assert order_item.quantity == Decimal('3.00')
        assert order_item.line_total == Decimal('300000.00')
        assert order_item.line_iva == Decimal('57000.00')
        order.refresh_from_db()
        assert order.total_amount == Decimal('357000.00')

    def test_patch_adds_new_item_without_id(
        self, api_client, company, third_party, sale_type, payment_method, item_price,
        item_group, unit_measure,
    ):
        from accounting.models import Item, ItemPrice

        order = _create_order(
            api_client, company, third_party, sale_type, payment_method,
            [{'item_price': item_price.id, 'quantity': '1.00'}],
        )
        existing_item = order.order_items.get()

        second_item = Item.objects.create(
            base_code='PANTS001', base_name='Pants', name='Pants',
            item_group=item_group, unit_measure=unit_measure, company=company,
        )
        second_price = ItemPrice.objects.create(
            item=second_item, company=company, item_price_type=ItemPrice.SELLING,
            price='50000.00', iva='0.00', excise_tax='0.00', total='50000.00',
        )

        response = api_client.patch(f'/api/orders/{order.id}/', {
            'order_items': [
                {'id': existing_item.id, 'item_price': item_price.id, 'quantity': '1.00'},
                {'item_price': second_price.id, 'quantity': '2.00'},
            ],
        }, format='json')

        assert response.status_code == 200, response.data
        order.refresh_from_db()
        assert order.order_items.count() == 2
        assert order.subtotal == Decimal('200000.00')  # 100000 + (50000*2)

    def test_patch_omitting_existing_item_deletes_it(
        self, api_client, company, third_party, sale_type, payment_method, item_price,
        item_group, unit_measure,
    ):
        from accounting.models import Item, ItemPrice

        second_item = Item.objects.create(
            base_code='PANTS001', base_name='Pants', name='Pants',
            item_group=item_group, unit_measure=unit_measure, company=company,
        )
        second_price = ItemPrice.objects.create(
            item=second_item, company=company, item_price_type=ItemPrice.SELLING,
            price='50000.00', iva='0.00', excise_tax='0.00', total='50000.00',
        )
        order = _create_order(
            api_client, company, third_party, sale_type, payment_method,
            [
                {'item_price': item_price.id, 'quantity': '1.00'},
                {'item_price': second_price.id, 'quantity': '1.00'},
            ],
        )
        assert order.order_items.count() == 2
        kept_item = order.order_items.get(item_price=item_price)

        response = api_client.patch(f'/api/orders/{order.id}/', {
            'order_items': [
                {'id': kept_item.id, 'item_price': item_price.id, 'quantity': '1.00'},
            ],
        }, format='json')

        assert response.status_code == 200, response.data
        order.refresh_from_db()
        assert order.order_items.count() == 1
        assert order.order_items.get().id == kept_item.id
        assert order.subtotal == Decimal('100000.00')

    def test_patch_recomputes_taxes_on_unit_price_override(
        self, api_client, company, third_party, sale_type, payment_method, item_price,
    ):
        order = _create_order(
            api_client, company, third_party, sale_type, payment_method,
            [{'item_price': item_price.id, 'quantity': '1.00'}],
        )
        order_item = order.order_items.get()

        response = api_client.patch(f'/api/orders/{order.id}/', {
            'order_items': [
                {'id': order_item.id, 'item_price': item_price.id, 'quantity': '1.00', 'unit_price': '80000.00'},
            ],
        }, format='json')

        assert response.status_code == 200, response.data
        order_item.refresh_from_db()
        assert order_item.unit_price == Decimal('80000.00')
        assert order_item.line_iva == Decimal('15200.00')

    def test_patch_ignores_payload_tax_fields(
        self, api_client, company, third_party, sale_type, payment_method, item_price,
    ):
        order = _create_order(
            api_client, company, third_party, sale_type, payment_method,
            [{'item_price': item_price.id, 'quantity': '1.00'}],
        )
        order_item = order.order_items.get()

        response = api_client.patch(f'/api/orders/{order.id}/', {
            'order_items': [
                {
                    'id': order_item.id, 'item_price': item_price.id, 'quantity': '1.00',
                    'line_iva': '1.00', 'line_total_with_taxes': '1.00',
                },
            ],
        }, format='json')

        assert response.status_code == 200, response.data
        order_item.refresh_from_db()
        assert order_item.line_iva == Decimal('19000.00')

    def test_patch_without_order_items_leaves_items_untouched(
        self, api_client, company, third_party, sale_type, payment_method, item_price,
    ):
        order = _create_order(
            api_client, company, third_party, sale_type, payment_method,
            [{'item_price': item_price.id, 'quantity': '1.00'}],
        )

        response = api_client.patch(f'/api/orders/{order.id}/', {'status': 'confirmed'}, format='json')

        assert response.status_code == 200, response.data
        order.refresh_from_db()
        assert order.status == 'confirmed'
        assert order.order_items.count() == 1

    def test_patch_rejects_order_item_id_not_on_this_order(
        self, api_client, company, third_party, sale_type, payment_method, item_price,
    ):
        order = _create_order(
            api_client, company, third_party, sale_type, payment_method,
            [{'item_price': item_price.id, 'quantity': '1.00'}],
        )

        response = api_client.patch(f'/api/orders/{order.id}/', {
            'order_items': [
                {'id': 999999, 'item_price': item_price.id, 'quantity': '1.00'},
            ],
        }, format='json')

        assert response.status_code == 400
        assert 'order_items' in response.data

    def test_patch_response_includes_full_order_representation(
        self, api_client, company, third_party, sale_type, payment_method, item_price,
    ):
        order = _create_order(
            api_client, company, third_party, sale_type, payment_method,
            [{'item_price': item_price.id, 'quantity': '1.00'}],
        )

        response = api_client.patch(f'/api/orders/{order.id}/', {'status': 'confirmed'}, format='json')

        assert response.status_code == 200, response.data
        assert response.data['id'] == order.id
        assert response.data['status'] == 'confirmed'
        assert len(response.data['order_items']) == 1
        assert response.data['total_amount'] is not None

    def test_patch_requires_authentication(self, company, third_party, sale_type, payment_method, item_price):
        from rest_framework.test import APIClient

        order = _create_order_via_orm(company, third_party, sale_type, payment_method, item_price)

        response = APIClient().patch(f'/api/orders/{order.id}/', {'status': 'confirmed'}, format='json')

        assert response.status_code == 401


def _create_order_via_orm(company, third_party, sale_type, payment_method, item_price):
    from accounting.models import Order, OrderItem

    order = Order.objects.create(
        order_type='sale', company=company, third_party=third_party,
        sale_type=sale_type, payment_method=payment_method,
    )
    OrderItem.objects.create(
        order=order, item_price=item_price, quantity='1.00', unit_price=item_price.price,
        line_total=item_price.price, line_iva='19000.00', line_excise_tax='0.00',
        line_total_with_taxes='119000.00',
    )
    return order
