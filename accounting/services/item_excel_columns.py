"""Single source of truth for the Item Excel import/export column layout."""

ITEMS_SHEET_NAME = 'Productos'

ID = 'id'
BASE_CODE = 'base_code'
BASE_NAME = 'base_name'
NAME = 'name'
ITEM_GROUP = 'item_group'
UNIT_MEASURE = 'unit_measure'
IVA_TYPE = 'iva_type'
IVA_RATE = 'iva_rate'
EXCISE_TAX_TYPE = 'excise_tax_type'
EXCISE_TAX_RATE = 'excise_tax_rate'

COLUMN_ORDER = [
    ID,
    BASE_CODE,
    BASE_NAME,
    NAME,
    ITEM_GROUP,
    UNIT_MEASURE,
    IVA_TYPE,
    IVA_RATE,
    EXCISE_TAX_TYPE,
    EXCISE_TAX_RATE,
]

COLUMN_HEADERS = {
    ID: 'Id (Solo Lectura)',
    BASE_CODE: 'Código base / Código de producto',
    BASE_NAME: 'Nombre base / Nombre del producto',
    NAME: 'Nombre detallado',
    ITEM_GROUP: 'Grupo / Categoría',
    UNIT_MEASURE: 'Unidad de medida',
    IVA_TYPE: 'Tipo de IVA',
    IVA_RATE: 'Tarifa de IVA',
    EXCISE_TAX_TYPE: 'Tipo de impuesto al consumo',
    EXCISE_TAX_RATE: 'Tarifa de impuesto al consumo',
}

HEADER_ROW = [COLUMN_HEADERS[key] for key in COLUMN_ORDER]
