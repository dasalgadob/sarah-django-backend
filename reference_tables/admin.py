"""Admin registrations for the reference_tables app."""

from django.contrib import admin

from .models import (
    ColombianDepartment,
    ColombianCity,
    DianEconomicActivity,
    DocumentType,
    ExciseTaxType,
    ExciseTaxRate,
    IvaType,
    IvaRate,
    UnitMeasure,
    SaleTypeOrder,
    PaymentMethodOrder,
)

admin.site.register(ColombianDepartment)
admin.site.register(ColombianCity)
admin.site.register(DianEconomicActivity)
admin.site.register(DocumentType)
admin.site.register(ExciseTaxType)
admin.site.register(ExciseTaxRate)
admin.site.register(IvaType)
admin.site.register(IvaRate)
admin.site.register(UnitMeasure)
admin.site.register(SaleTypeOrder)
admin.site.register(PaymentMethodOrder)
