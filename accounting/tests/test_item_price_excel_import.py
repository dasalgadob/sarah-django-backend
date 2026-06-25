import io

import openpyxl
import pytest
from decimal import Decimal

from accounting.models import Item, ItemPrice
from accounting.services.item_price_excel_columns import HEADER_ROW
from accounting.services.item_price_excel_import import InvalidWorkbookError, ItemPriceExcelImporter


def _workbook_file(rows):
    workbook = openpyxl.Workbook()
    sheet = workbook.active
    sheet.append(HEADER_ROW)
    for row in rows:
        sheet.append(row)

    buffer = io.BytesIO()
    workbook.save(buffer)
    buffer.seek(0)
    return buffer


@pytest.mark.django_db
class TestItemPriceExcelImporter:
    def test_creates_new_price_with_taxes_computed_from_price(self, company, item, iva_rate):
        file_obj = _workbook_file([
            [None, item.id, item.name, 'Venta', 100000, None, None, None],
        ])

        result = ItemPriceExcelImporter(company_id=company.id).import_workbook(file_obj)

        assert result.as_dict() == {'created': 1, 'updated': 0, 'errors': []}
        price = ItemPrice.objects.get(company=company, item=item)
        assert price.item_price_type == ItemPrice.SELLING
        assert price.price == Decimal('100000.00')
        assert price.iva == Decimal('19000.00')
        assert price.excise_tax == Decimal('0.00')
        assert price.total == Decimal('119000.00')

    def test_maps_compra_to_buying(self, company, item):
        file_obj = _workbook_file([
            [None, item.id, item.name, 'Compra', 50000, None, None, None],
        ])

        result = ItemPriceExcelImporter(company_id=company.id).import_workbook(file_obj)

        assert result.as_dict()['created'] == 1
        price = ItemPrice.objects.get(company=company, item=item)
        assert price.item_price_type == ItemPrice.BUYING

    def test_includes_excise_tax_when_item_has_excise_rate(self, company, item, excise_tax_rate):
        item.excise_tax_type = excise_tax_rate.excise_tax_type
        item.excise_tax_rate = excise_tax_rate
        item.save()

        file_obj = _workbook_file([
            [None, item.id, item.name, 'Venta', 100000, None, None, None],
        ])

        result = ItemPriceExcelImporter(company_id=company.id).import_workbook(file_obj)

        assert result.as_dict()['created'] == 1
        price = ItemPrice.objects.get(company=company, item=item)
        assert price.excise_tax == Decimal('10000.00')
        assert price.total == Decimal('129000.00')

    def test_updates_existing_price_matched_by_id(self, company, item, iva_rate):
        existing = ItemPrice.objects.create(
            item=item, company=company, item_price_type=ItemPrice.BUYING,
            price='1.00', iva='0.19', excise_tax='0.00', total='1.19',
        )
        file_obj = _workbook_file([
            [existing.id, item.id, item.name, 'Venta', 200000, None, None, None],
        ])

        result = ItemPriceExcelImporter(company_id=company.id).import_workbook(file_obj)

        assert result.as_dict() == {'created': 0, 'updated': 1, 'errors': []}
        existing.refresh_from_db()
        assert existing.item_price_type == ItemPrice.SELLING
        assert existing.price == Decimal('200000.00')
        assert existing.iva == Decimal('38000.00')

    def test_ignores_typed_iva_excise_total_and_recomputes_them(self, company, item, iva_rate):
        file_obj = _workbook_file([
            [None, item.id, item.name, 'Venta', 100000, 999999, 999999, 999999],
        ])

        ItemPriceExcelImporter(company_id=company.id).import_workbook(file_obj)

        price = ItemPrice.objects.get(company=company, item=item)
        assert price.iva == Decimal('19000.00')
        assert price.excise_tax == Decimal('0.00')
        assert price.total == Decimal('119000.00')

    def test_rejects_item_id_belonging_to_another_company(self, company, other_company, item_group, unit_measure):
        other_item = Item.objects.create(
            base_code='OTHER001', base_name='Other', name='Other',
            item_group=item_group, unit_measure=unit_measure, company=other_company,
        )
        file_obj = _workbook_file([
            [None, other_item.id, other_item.name, 'Venta', 100000, None, None, None],
        ])

        result = ItemPriceExcelImporter(company_id=company.id).import_workbook(file_obj)

        assert result.as_dict() == {
            'created': 0, 'updated': 0,
            'errors': [{
                'row': 2,
                'errors': {'item_id': f'El producto con id {other_item.id} no existe o no pertenece a esta empresa.'},
            }],
        }

    def test_rejects_price_id_belonging_to_another_company(self, company, other_company, item):
        other_price = ItemPrice.objects.create(
            item=item, company=other_company, item_price_type=ItemPrice.SELLING,
            price='1.00', iva='0.19', excise_tax='0.00', total='1.19',
        )
        file_obj = _workbook_file([
            [other_price.id, item.id, item.name, 'Venta', 100000, None, None, None],
        ])

        result = ItemPriceExcelImporter(company_id=company.id).import_workbook(file_obj)

        assert result.as_dict()['errors'] == [{
            'row': 2,
            'errors': {'id': f'El precio con id {other_price.id} no existe o no pertenece a esta empresa.'},
        }]

    def test_requires_item_id(self, company):
        file_obj = _workbook_file([
            [None, None, None, 'Venta', 100000, None, None, None],
        ])

        result = ItemPriceExcelImporter(company_id=company.id).import_workbook(file_obj)

        assert result.as_dict()['errors'] == [
            {'row': 2, 'errors': {'item_id': 'Este campo es obligatorio.'}},
        ]

    def test_requires_price(self, company, item):
        file_obj = _workbook_file([
            [None, item.id, item.name, 'Venta', None, None, None, None],
        ])

        result = ItemPriceExcelImporter(company_id=company.id).import_workbook(file_obj)

        assert result.as_dict()['errors'] == [
            {'row': 2, 'errors': {'price': 'Este campo es obligatorio.'}},
        ]

    def test_rejects_invalid_price_type_label(self, company, item):
        file_obj = _workbook_file([
            [None, item.id, item.name, 'Mayorista', 100000, None, None, None],
        ])

        result = ItemPriceExcelImporter(company_id=company.id).import_workbook(file_obj)

        assert result.as_dict()['errors'] == [
            {'row': 2, 'errors': {'item_price_type': '"Mayorista" no es válido. Use "Venta" o "Compra".'}},
        ]

    def test_skips_blank_rows(self, company):
        file_obj = _workbook_file([
            [None, None, None, None, None, None, None, None],
        ])

        result = ItemPriceExcelImporter(company_id=company.id).import_workbook(file_obj)

        assert result.as_dict() == {'created': 0, 'updated': 0, 'errors': []}

    def test_invalid_file_raises_invalid_workbook_error(self, company):
        bad_file = io.BytesIO(b'this is not an xlsx file')

        with pytest.raises(InvalidWorkbookError):
            ItemPriceExcelImporter(company_id=company.id).import_workbook(bad_file)
