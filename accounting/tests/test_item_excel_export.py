import io

import openpyxl
import pytest

from accounting.models import Item
from accounting.services.item_excel_columns import HEADER_ROW
from accounting.services.item_excel_export import ItemExcelExporter


@pytest.mark.django_db
class TestItemExcelExporter:
    def test_build_workbook_writes_header_row(self, company, item_group, unit_measure):
        exporter = ItemExcelExporter(Item.objects.filter(company=company))
        sheet = exporter.build_workbook().active

        header = [cell.value for cell in sheet[1]]

        assert header == HEADER_ROW

    def test_build_workbook_writes_item_row_with_resolved_tax_names(
        self, company, item_group, unit_measure, iva_type, iva_rate, excise_tax_type, excise_tax_rate,
    ):
        Item.objects.create(
            base_code='TSHIRT001',
            base_name='Cotton T-Shirt',
            name='Cotton T-Shirt',
            item_group=item_group,
            unit_measure=unit_measure,
            company=company,
            iva_type=iva_type,
            iva_rate=iva_rate,
            excise_tax_type=excise_tax_type,
            excise_tax_rate=excise_tax_rate,
        )

        exporter = ItemExcelExporter(Item.objects.filter(company=company))
        sheet = exporter.build_workbook().active
        row = [cell.value for cell in sheet[2]]

        assert row == [
            'TSHIRT001',
            'Cotton T-Shirt',
            'Cotton T-Shirt',
            item_group.name,
            unit_measure.abbreviation,
            iva_type.name,
            19.0,
            excise_tax_type.name,
            10.0,
        ]

    def test_build_workbook_leaves_null_tax_fields_blank(self, company, item_group, unit_measure):
        Item.objects.create(
            base_code='NOTAX001',
            base_name='Tax Free Item',
            name='Tax Free Item',
            item_group=item_group,
            unit_measure=unit_measure,
            company=company,
        )

        exporter = ItemExcelExporter(Item.objects.filter(company=company))
        sheet = exporter.build_workbook().active
        row = [cell.value for cell in sheet[2]]

        assert row[5:] == [None, None, None, None]

    def test_as_http_response_returns_xlsx_attachment(self, company, item_group, unit_measure, item):
        exporter = ItemExcelExporter(Item.objects.filter(company=company))
        response = exporter.as_http_response(filename='items.xlsx')

        assert response['Content-Type'] == (
            'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        assert response['Content-Disposition'] == 'attachment; filename="items.xlsx"'

        workbook = openpyxl.load_workbook(filename=io.BytesIO(response.content))
        assert workbook.active['A1'].value == HEADER_ROW[0]


@pytest.mark.django_db
class TestItemExcelExporterReferenceSheets:
    def test_includes_one_reference_sheet_per_lookup_table(self, company, item_group, unit_measure):
        workbook = ItemExcelExporter(Item.objects.filter(company=company)).build_workbook()

        assert workbook.sheetnames == [
            'Productos',
            'Grupos',
            'Unidades de medida',
            'Tipos de IVA',
            'Tarifas de IVA',
            'Tipos de imp. al consumo',
            'Tarifas de imp. al consumo',
        ]
        assert workbook.active.title == 'Productos'

    def test_grupos_sheet_lists_item_group_names(self, company, item_group, unit_measure):
        workbook = ItemExcelExporter(Item.objects.filter(company=company)).build_workbook()
        sheet = workbook['Grupos']

        assert [cell.value for cell in sheet[1]] == ['Grupo / Categoría']
        assert [cell.value for cell in sheet[2]] == [item_group.name]

    def test_unidades_sheet_lists_abbreviation_and_name(self, company, item_group, unit_measure):
        workbook = ItemExcelExporter(Item.objects.filter(company=company)).build_workbook()
        sheet = workbook['Unidades de medida']

        assert [cell.value for cell in sheet[1]] == ['Unidad de medida', 'Nombre']
        assert [cell.value for cell in sheet[2]] == [unit_measure.abbreviation, unit_measure.name]

    def test_tarifas_iva_sheet_lists_type_rate_pairs_as_float(
        self, company, item_group, unit_measure, iva_type, iva_rate,
    ):
        workbook = ItemExcelExporter(Item.objects.filter(company=company)).build_workbook()
        sheet = workbook['Tarifas de IVA']

        assert [cell.value for cell in sheet[1]] == ['Tipo de IVA', 'Tarifa de IVA']
        assert [cell.value for cell in sheet[2]] == [iva_type.name, 19.0]

    def test_tarifas_consumo_sheet_lists_type_rate_pairs_as_float(
        self, company, item_group, unit_measure, excise_tax_type, excise_tax_rate,
    ):
        workbook = ItemExcelExporter(Item.objects.filter(company=company)).build_workbook()
        sheet = workbook['Tarifas de imp. al consumo']

        assert [cell.value for cell in sheet[1]] == ['Tipo de impuesto al consumo', 'Tarifa de impuesto al consumo']
        assert [cell.value for cell in sheet[2]] == [excise_tax_type.name, 10.0]
