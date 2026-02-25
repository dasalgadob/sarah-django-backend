"""URL configuration for the Django application."""

from django.contrib import admin
from django.urls import path, include
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
    TokenVerifyView,
    TokenBlacklistView,
)
from rest_framework.routers import DefaultRouter
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView, SpectacularRedocView

# Create a router for API root view
router = DefaultRouter()
# The router will automatically create an API root at /api/

urlpatterns = [
    # Django admin
    path('admin/', admin.site.urls),

    # JWT Authentication endpoints
    path('api/auth/login/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/auth/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('api/auth/verify/', TokenVerifyView.as_view(), name='token_verify'),
    path('api/auth/logout/', TokenBlacklistView.as_view(), name='token_blacklist'),

    # App routers
    path('api/', include('core.urls')),
    path('api/', include('reference_tables.urls')),
    path('api/', include('accounting.urls')),
    
    # API Root (shows available endpoints)
    path('api/', include(router.urls)),

    # OpenAPI schema endpoints
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/schema/swagger-ui/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/schema/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
]
