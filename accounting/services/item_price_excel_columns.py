"""Single source of truth for the ItemPrice Excel import/export column layout."""

from ..models import ItemPrice

ITEM_PRICES_SHEET_NAME = 'Precios'

ID = 'id'
ITEM_ID = 'item_id'
ITEM_NAME = 'item_name'
ITEM_PRICE_TYPE = 'item_price_type'
PRICE = 'price'
IVA = 'iva'
EXCISE_TAX = 'excise_tax'
TOTAL = 'total'

COLUMN_ORDER = [
    ID,
    ITEM_ID,
    ITEM_NAME,
    ITEM_PRICE_TYPE,
    PRICE,
    IVA,
    EXCISE_TAX,
    TOTAL,
]

COLUMN_HEADERS = {
    ID: 'Id (No Editar)',
    ITEM_ID: 'Id producto (No Editar)',
    ITEM_NAME: 'Producto (Solo Lectura)',
    ITEM_PRICE_TYPE: 'Tipo de precio',
    PRICE: 'Precio',
    IVA: 'IVA (Solo Lectura)',
    EXCISE_TAX: 'Impuesto al consumo (Solo Lectura)',
    TOTAL: 'Total (Solo Lectura)',
}

HEADER_ROW = [COLUMN_HEADERS[key] for key in COLUMN_ORDER]

# Spreadsheet uses Spanish labels for item_price_type instead of the raw model values.
PRICE_TYPE_LABELS = {
    ItemPrice.SELLING: 'Venta',
    ItemPrice.BUYING: 'Compra',
}
PRICE_TYPE_VALUES_BY_LABEL = {label.lower(): value for value, label in PRICE_TYPE_LABELS.items()}
