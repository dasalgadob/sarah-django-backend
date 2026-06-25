import io

import openpyxl
import pytest

from accounting.models import ItemPrice
from accounting.services.item_price_excel_columns import HEADER_ROW, ITEM_PRICES_SHEET_NAME
from accounting.services.item_price_excel_export import ItemPriceExcelExporter


@pytest.mark.django_db
class TestItemPriceExcelExporter:
    def test_build_workbook_writes_header_row(self, company):
        exporter = ItemPriceExcelExporter(ItemPrice.objects.filter(company=company))
        sheet = exporter.build_workbook().active

        assert sheet.title == ITEM_PRICES_SHEET_NAME
        assert [cell.value for cell in sheet[1]] == HEADER_ROW

    def test_build_workbook_writes_row_with_spanish_price_type_and_item_name(self, company, item):
        item_price = ItemPrice.objects.create(
            item=item, company=company, item_price_type=ItemPrice.SELLING,
            price='100000.00', iva='19000.00', excise_tax='0.00', total='119000.00',
        )

        exporter = ItemPriceExcelExporter(ItemPrice.objects.filter(company=company))
        sheet = exporter.build_workbook().active
        row = [cell.value for cell in sheet[2]]

        assert row == [
            item_price.id,
            item.id,
            item.name,
            'Venta',
            100000.0,
            19000.0,
            0.0,
            119000.0,
        ]

    def test_build_workbook_maps_buying_to_compra(self, company, item):
        ItemPrice.objects.create(
            item=item, company=company, item_price_type=ItemPrice.BUYING,
            price='50000.00', iva='9500.00', excise_tax='0.00', total='59500.00',
        )

        exporter = ItemPriceExcelExporter(ItemPrice.objects.filter(company=company))
        sheet = exporter.build_workbook().active
        row = [cell.value for cell in sheet[2]]

        assert row[3] == 'Compra'

    def test_as_http_response_returns_xlsx_attachment(self, company, item):
        exporter = ItemPriceExcelExporter(ItemPrice.objects.filter(company=company))
        response = exporter.as_http_response(filename='precios.xlsx')

        assert response['Content-Type'] == (
            'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        assert response['Content-Disposition'] == 'attachment; filename="precios.xlsx"'

        workbook = openpyxl.load_workbook(filename=io.BytesIO(response.content))
        assert workbook.active['A1'].value == HEADER_ROW[0]
