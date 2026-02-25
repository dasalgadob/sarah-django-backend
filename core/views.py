"""Views for the core app."""

from django.contrib.auth.models import User
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import Role, Company
from .serializers import UserSerializer, RoleSerializer, CompanySerializer
from .pagination import LargeResultsSetPagination, SmallResultsSetPagination
from reference_tables.models import DocumentType


class UserViewSet(viewsets.ModelViewSet):
    """CRUD for Django's built-in User model."""

    queryset = User.objects.all().order_by('id')
    serializer_class = UserSerializer
    pagination_class = SmallResultsSetPagination  # 10 items per page


class RoleViewSet(viewsets.ModelViewSet):
    """CRUD for roles."""

    queryset = Role.objects.all().order_by('id')
    serializer_class = RoleSerializer
    pagination_class = SmallResultsSetPagination  # 10 items per page


class CompanyViewSet(viewsets.ModelViewSet):
    """CRUD for companies."""

    queryset = Company.objects.select_related(
        'document_type', 'country', 'colombian_city',
        'colombian_department', 'dian_economic_activity',
    ).all()
    serializer_class = CompanySerializer
    pagination_class = LargeResultsSetPagination
    serializer_class = CompanySerializer

    def _validate_document_type(self, request_data):
        """Validate required fields based on document type code (mirrors Rails logic)."""
        doc_type_id = request_data.get('document_type')
        if not doc_type_id:
            return None
        try:
            doc_type = DocumentType.objects.get(pk=doc_type_id)
        except DocumentType.DoesNotExist:
            return Response(
                {'error': 'Document type not found.'},
                status=status.HTTP_422_UNPROCESSABLE_ENTITY,
            )
        code = doc_type.code
        if code == 13:
            if not request_data.get('first_name') or not request_data.get('first_lastname'):
                return Response(
                    {'error': 'First name and first lastname are required for this document type.'},
                    status=status.HTTP_422_UNPROCESSABLE_ENTITY,
                )
        if code in (31, 43):
            if not request_data.get('legal_name'):
                return Response(
                    {'error': 'Legal name is required for this document type.'},
                    status=status.HTTP_422_UNPROCESSABLE_ENTITY,
                )
        if code == 42:
            if not request_data.get('legal_name') or not request_data.get('first_name') or not request_data.get('first_lastname'):
                return Response(
                    {'error': 'Legal name or first name and first lastname are required for this document type.'},
                    status=status.HTTP_422_UNPROCESSABLE_ENTITY,
                )
        return None

    def create(self, request, *args, **kwargs):
        error = self._validate_document_type(request.data)
        if error is not None:
            return error
        return super().create(request, *args, **kwargs)

    def update(self, request, *args, **kwargs):
        error = self._validate_document_type(request.data)
        if error is not None:
            return error
        return super().update(request, *args, **kwargs)
