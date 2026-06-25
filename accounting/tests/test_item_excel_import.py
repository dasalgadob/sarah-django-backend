import io

import openpyxl
import pytest

from accounting.models import Item
from accounting.services.item_excel_columns import HEADER_ROW
from accounting.services.item_excel_import import InvalidWorkbookError, ItemExcelImporter


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
class TestItemExcelImporter:
    def test_creates_new_item_with_resolved_foreign_keys(
        self, company, item_group, unit_measure, iva_type, iva_rate,
    ):
        file_obj = _workbook_file([
            [None, 'TSHIRT001', 'Cotton T-Shirt', 'Cotton T-Shirt', item_group.name, unit_measure.abbreviation, iva_type.name, 19, None, None],
        ])

        result = ItemExcelImporter(company_id=company.id).import_workbook(file_obj)

        assert result.as_dict() == {'created': 1, 'updated': 0, 'errors': []}
        item = Item.objects.get(company=company, code='TSHIRT001')
        assert item.base_name == 'Cotton T-Shirt'
        assert item.item_group == item_group
        assert item.unit_measure == unit_measure
        assert item.iva_type == iva_type
        assert item.iva_rate == iva_rate
        assert item.excise_tax_type is None
        assert item.excise_tax_rate is None

    def test_updates_existing_item_matched_by_company_and_code(self, company, item, item_group, unit_measure):
        file_obj = _workbook_file([
            [None, 'TSHIRT001', 'Updated Base Name', 'Updated Name', item_group.name, unit_measure.abbreviation, None, None, None, None],
        ])

        result = ItemExcelImporter(company_id=company.id).import_workbook(file_obj)

        assert result.as_dict() == {'created': 0, 'updated': 1, 'errors': []}
        item.refresh_from_db()
        assert item.base_name == 'Updated Base Name'
        assert item.name == 'Updated Name'
        assert item.iva_type is None
        assert item.iva_rate is None

    def test_skips_blank_rows(self, company, item_group, unit_measure):
        file_obj = _workbook_file([
            [None, None, None, None, None, None, None, None, None, None],
        ])

        result = ItemExcelImporter(company_id=company.id).import_workbook(file_obj)

        assert result.as_dict() == {'created': 0, 'updated': 0, 'errors': []}

    def test_reports_required_field_errors_without_raising(self, company, item_group, unit_measure):
        file_obj = _workbook_file([
            [None, None, 'Base Name', 'Name', item_group.name, unit_measure.abbreviation, None, None, None, None],
        ])

        result = ItemExcelImporter(company_id=company.id).import_workbook(file_obj)

        assert result.created == 0
        assert result.updated == 0
        assert result.as_dict()['errors'] == [
            {'row': 2, 'errors': {'base_code': 'Este campo es obligatorio.'}},
        ]

    def test_reports_unresolvable_item_group_by_name(self, company, item_group, unit_measure):
        file_obj = _workbook_file([
            [None, 'TSHIRT001', 'Base Name', 'Name', 'Nonexistent Group', unit_measure.abbreviation, None, None, None, None],
        ])

        result = ItemExcelImporter(company_id=company.id).import_workbook(file_obj)

        assert result.as_dict()['errors'] == [
            {'row': 2, 'errors': {'item_group': '"Nonexistent Group" no encontrado.'}},
        ]
        assert not Item.objects.filter(company=company, code='TSHIRT001').exists()

    def test_reports_iva_rate_not_found_for_given_type(self, company, item_group, unit_measure, iva_type):
        file_obj = _workbook_file([
            [None, 'TSHIRT001', 'Base Name', 'Name', item_group.name, unit_measure.abbreviation, iva_type.name, 99, None, None],
        ])

        result = ItemExcelImporter(company_id=company.id).import_workbook(file_obj)

        assert result.as_dict()['errors'] == [
            {'row': 2, 'errors': {'iva_rate': f'Tarifa "99.00" no encontrada para "{iva_type.name}".'}},
        ]

    def test_requires_iva_type_when_only_rate_given(self, company, item_group, unit_measure):
        file_obj = _workbook_file([
            [None, 'TSHIRT001', 'Base Name', 'Name', item_group.name, unit_measure.abbreviation, None, 19, None, None],
        ])

        result = ItemExcelImporter(company_id=company.id).import_workbook(file_obj)

        assert result.as_dict()['errors'] == [
            {'row': 2, 'errors': {'iva_type': 'Se requiere el tipo para resolver la tarifa.'}},
        ]

    def test_does_not_touch_other_companies_items_with_same_code(self, company, other_company, item_group, unit_measure):
        Item.objects.create(
            base_code='SHARED001', base_name='Other Co Item', name='Other Co Item',
            item_group=item_group, unit_measure=unit_measure, company=other_company,
        )
        file_obj = _workbook_file([
            [None, 'SHARED001', 'My Co Item', 'My Co Item', item_group.name, unit_measure.abbreviation, None, None, None, None],
        ])

        result = ItemExcelImporter(company_id=company.id).import_workbook(file_obj)

        assert result.as_dict() == {'created': 1, 'updated': 0, 'errors': []}
        assert Item.objects.get(company=company, code='SHARED001').base_name == 'My Co Item'
        assert Item.objects.get(company=other_company, code='SHARED001').base_name == 'Other Co Item'

    def test_invalid_file_raises_invalid_workbook_error(self, company):
        bad_file = io.BytesIO(b'this is not an xlsx file')

        with pytest.raises(InvalidWorkbookError):
            ItemExcelImporter(company_id=company.id).import_workbook(bad_file)
