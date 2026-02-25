"""URL routing for the reference_tables app."""

from rest_framework.routers import DefaultRouter

from .views import (
    ColombianDepartmentViewSet,
    ColombianCityViewSet,
    DianEconomicActivityViewSet,
    DocumentTypeViewSet,
    ExciseTaxTypeViewSet,
    ExciseTaxRateViewSet,
    IvaTypeViewSet,
    IvaRateViewSet,
    UnitMeasureViewSet,
    SaleTypeOrderViewSet,
    PaymentMethodOrderViewSet,
)

router = DefaultRouter()
router.register(r'colombian-departments', ColombianDepartmentViewSet, basename='colombian-department')
router.register(r'colombian-cities', ColombianCityViewSet, basename='colombian-city')
router.register(r'dian-economic-activities', DianEconomicActivityViewSet, basename='dian-economic-activity')
router.register(r'document-types', DocumentTypeViewSet, basename='document-type')
router.register(r'excise-tax-types', ExciseTaxTypeViewSet, basename='excise-tax-type')
router.register(r'excise-tax-rates', ExciseTaxRateViewSet, basename='excise-tax-rate')
router.register(r'iva-types', IvaTypeViewSet, basename='iva-type')
router.register(r'iva-rates', IvaRateViewSet, basename='iva-rate')
router.register(r'unit-measures', UnitMeasureViewSet, basename='unit-measure')
router.register(r'sale-types', SaleTypeOrderViewSet, basename='sale-type')
router.register(r'payment-methods', PaymentMethodOrderViewSet, basename='payment-method')

urlpatterns = router.urls
