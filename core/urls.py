"""URL routing for the core app."""

from rest_framework.routers import DefaultRouter
from .views import UserViewSet, RoleViewSet, CompanyViewSet

router = DefaultRouter()
router.register(r'users', UserViewSet, basename='user')
router.register(r'roles', RoleViewSet, basename='role')
router.register(r'companies', CompanyViewSet, basename='company')

urlpatterns = router.urls
