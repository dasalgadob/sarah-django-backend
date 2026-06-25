"""Shared tax calculation based on an Item's configured tax rates."""

from decimal import Decimal


def calculate_taxes(item, amount):
    """Returns (iva, excise_tax, total) for a base amount, using the item's tax rates."""
    iva_rate = item.iva_rate.value if item.iva_rate_id else Decimal('0')
    excise_rate = item.excise_tax_rate.value if item.excise_tax_rate_id else Decimal('0')
    iva = (amount * iva_rate / Decimal('100')).quantize(Decimal('0.01'))
    excise_tax = (amount * excise_rate / Decimal('100')).quantize(Decimal('0.01'))
    total = (amount + iva + excise_tax).quantize(Decimal('0.01'))
    return iva, excise_tax, total
