"""URL routing for the accounting app."""

from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import (
    CountryViewSet,
    ItemGroupViewSet,
    ItemViewSet,
    ItemPriceViewSet,
    ThirdPartyViewSet,
    OrderViewSet,
    OrderItemViewSet,
    ItemPropertyTypeViewSet,
    ItemPropertyValueViewSet,
    ItemPropertyViewSet,
)

# Top-level router for non-nested resources
router = DefaultRouter()
router.register(r'countries', CountryViewSet, basename='country')
router.register(r'item-groups', ItemGroupViewSet, basename='item-group')
router.register(r'third-parties', ThirdPartyViewSet, basename='third-party')

# Order and Item Property management (independent resources)
router.register(r'orders', OrderViewSet, basename='order')
router.register(r'order-items', OrderItemViewSet, basename='order-item')
router.register(r'item-property-types', ItemPropertyTypeViewSet, basename='item-property-type')
router.register(r'item-property-values', ItemPropertyValueViewSet, basename='item-property-value')
router.register(r'item-properties', ItemPropertyViewSet, basename='item-property')

# Nested resources under companies (company_pk passed as URL kwarg)
company_items_router = DefaultRouter()
company_items_router.register(r'items', ItemViewSet, basename='company-item')
company_items_router.register(r'item-prices', ItemPriceViewSet, basename='company-item-price')
company_items_router.register(
    r'third-parties', ThirdPartyViewSet, basename='company-third-party'
)

# Company-specific orders
company_orders_router = DefaultRouter()
company_orders_router.register(r'orders', OrderViewSet, basename='company-order')

urlpatterns = router.urls + [
    path(
        'companies/<int:company_pk>/',
        include(company_items_router.urls),
    ),
    path(
        'companies/<int:company_pk>/',
        include(company_orders_router.urls),
    ),
]
