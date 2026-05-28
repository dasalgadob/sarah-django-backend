"""
Reference tables app models.

Contains lookup/catalogue tables:
  ColombianDepartment, ColombianCity, DianEconomicActivity,
  DocumentType, ExciseTaxType, ExciseTaxRate, IvaType, IvaRate, UnitMeasure,
  SaleTypeOrder, PaymentMethodOrder.
"""

from django.db import models
from safedelete.models import SafeDeleteModel, SOFT_DELETE_CASCADE
from simple_history.models import HistoricalRecords


class ColombianDepartment(SafeDeleteModel):
    _safedelete_policy = SOFT_DELETE_CASCADE

    code = models.CharField(max_length=10, unique=True)
    name = models.CharField(max_length=255, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    history = HistoricalRecords()

    class Meta:
        db_table = 'colombian_departments'

    def __str__(self):
        return f'{self.code} - {self.name}'


class ColombianCity(SafeDeleteModel):
    _safedelete_policy = SOFT_DELETE_CASCADE

    code = models.CharField(max_length=10)
    name = models.CharField(max_length=255)
    colombian_department = models.ForeignKey(
        ColombianDepartment,
        on_delete=models.PROTECT,
        related_name='cities',
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    history = HistoricalRecords()

    class Meta:
        db_table = 'colombian_cities'

    def __str__(self):
        return f'{self.code} - {self.name}'


class DianEconomicActivity(SafeDeleteModel):
    _safedelete_policy = SOFT_DELETE_CASCADE

    code = models.CharField(max_length=20)
    name = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    history = HistoricalRecords()

    class Meta:
        db_table = 'dian_economic_activities'

    def __str__(self):
        return f'{self.code} - {self.name}'


class DocumentType(SafeDeleteModel):
    _safedelete_policy = SOFT_DELETE_CASCADE

    code = models.IntegerField()
    name = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    history = HistoricalRecords()

    class Meta:
        db_table = 'document_types'

    def __str__(self):
        return f'{self.code} - {self.name}'


class ExciseTaxType(SafeDeleteModel):
    _safedelete_policy = SOFT_DELETE_CASCADE

    name = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    history = HistoricalRecords()

    class Meta:
        db_table = 'excise_tax_types'

    def __str__(self):
        return self.name


class ExciseTaxRate(SafeDeleteModel):
    _safedelete_policy = SOFT_DELETE_CASCADE

    value = models.DecimalField(max_digits=4, decimal_places=2)
    excise_tax_type = models.ForeignKey(
        ExciseTaxType,
        on_delete=models.PROTECT,
        related_name='rates',
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    history = HistoricalRecords()

    class Meta:
        db_table = 'excise_tax_rates'

    def __str__(self):
        return f'{self.value}% ({self.excise_tax_type})'


class IvaType(SafeDeleteModel):
    _safedelete_policy = SOFT_DELETE_CASCADE

    name = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    history = HistoricalRecords()

    class Meta:
        db_table = 'iva_types'

    def __str__(self):
        return self.name


class IvaRate(SafeDeleteModel):
    _safedelete_policy = SOFT_DELETE_CASCADE

    value = models.DecimalField(max_digits=4, decimal_places=2)
    iva_type = models.ForeignKey(
        IvaType,
        on_delete=models.PROTECT,
        related_name='rates',
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    history = HistoricalRecords()

    class Meta:
        db_table = 'iva_rates'

    def __str__(self):
        return f'{self.value}% ({self.iva_type})'


class UnitMeasure(SafeDeleteModel):
    _safedelete_policy = SOFT_DELETE_CASCADE

    abbreviation = models.CharField(max_length=20)
    name = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    history = HistoricalRecords()

    class Meta:
        db_table = 'unit_measures'

    def __str__(self):
        return f'{self.abbreviation} - {self.name}'


class SaleTypeOrder(SafeDeleteModel):
    _safedelete_policy = SOFT_DELETE_CASCADE

    name = models.CharField(max_length=255, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    history = HistoricalRecords()

    class Meta:
        db_table = 'sale_type_orders'

    def __str__(self):
        return self.name


class PaymentMethodOrder(SafeDeleteModel):
    _safedelete_policy = SOFT_DELETE_CASCADE

    name = models.CharField(max_length=255, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    history = HistoricalRecords()

    class Meta:
        db_table = 'payment_method_orders'

    def __str__(self):
        return self.name
