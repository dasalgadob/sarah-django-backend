"""Views for the reference_tables app."""

from rest_framework import viewsets
from rest_framework.response import Response

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
from .serializers import (
    ColombianDepartmentSerializer,
    ColombianCitySerializer,
    DianEconomicActivitySerializer,
    DocumentTypeSerializer,
    ExciseTaxTypeSerializer,
    ExciseTaxRateSerializer,
    IvaTypeSerializer,
    IvaRateSerializer,
    UnitMeasureSerializer,
    SaleTypeOrderSerializer,
    PaymentMethodOrderSerializer,
)


class ColombianDepartmentViewSet(viewsets.ModelViewSet):
    queryset = ColombianDepartment.objects.all()
    serializer_class = ColombianDepartmentSerializer
    pagination_class = None  # No pagination - returns all departments

    def list(self, request, *args, **kwargs):
        """Override list to return all results under 'data' key."""
        queryset = self.filter_queryset(self.get_queryset())
        serializer = self.get_serializer(queryset, many=True)
        return Response({'data': serializer.data})


class ColombianCityViewSet(viewsets.ModelViewSet):
    serializer_class = ColombianCitySerializer
    pagination_class = None  # No pagination - returns all cities

    def get_queryset(self):
        qs = ColombianCity.objects.select_related('colombian_department').all()
        dept_id = self.request.query_params.get('colombian_department_id')
        name = self.request.query_params.get('name')
        code = self.request.query_params.get('code')
        dept_code = self.request.query_params.get('department_code')
        if dept_id:
            qs = qs.filter(colombian_department_id=dept_id)
        if name:
            qs = qs.filter(name__icontains=name)
        if code:
            qs = qs.filter(code__icontains=code)
        if dept_code:
            qs = qs.filter(colombian_department__code=dept_code)
        return qs

    def list(self, request, *args, **kwargs):
        """Override list to return all results under 'data' key."""
        queryset = self.filter_queryset(self.get_queryset())
        serializer = self.get_serializer(queryset, many=True)
        return Response({'data': serializer.data})


class DianEconomicActivityViewSet(viewsets.ModelViewSet):
    queryset = DianEconomicActivity.objects.all()
    serializer_class = DianEconomicActivitySerializer
    pagination_class = None  # No pagination - returns all economic activities

    def list(self, request, *args, **kwargs):
        """Override list to return all results under 'data' key."""
        queryset = self.filter_queryset(self.get_queryset())
        serializer = self.get_serializer(queryset, many=True)
        return Response({'data': serializer.data})


class DocumentTypeViewSet(viewsets.ModelViewSet):
    queryset = DocumentType.objects.all()
    serializer_class = DocumentTypeSerializer

    def perform_destroy(self, instance):
        instance.soft_delete()


class ExciseTaxTypeViewSet(viewsets.ModelViewSet):
    queryset = ExciseTaxType.objects.all()
    serializer_class = ExciseTaxTypeSerializer


class ExciseTaxRateViewSet(viewsets.ModelViewSet):
    queryset = ExciseTaxRate.objects.select_related('excise_tax_type').all()
    serializer_class = ExciseTaxRateSerializer


class IvaTypeViewSet(viewsets.ModelViewSet):
    queryset = IvaType.objects.all()
    serializer_class = IvaTypeSerializer


class IvaRateViewSet(viewsets.ModelViewSet):
    queryset = IvaRate.objects.select_related('iva_type').all()
    serializer_class = IvaRateSerializer


class UnitMeasureViewSet(viewsets.ModelViewSet):
    queryset = UnitMeasure.objects.all()
    serializer_class = UnitMeasureSerializer


class SaleTypeOrderViewSet(viewsets.ModelViewSet):
    queryset = SaleTypeOrder.objects.all()
    serializer_class = SaleTypeOrderSerializer
    pagination_class = None  # No pagination - returns all sale types

    def list(self, request, *args, **kwargs):
        """Override list to return all results under 'data' key."""
        queryset = self.filter_queryset(self.get_queryset())
        serializer = self.get_serializer(queryset, many=True)
        return Response({'data': serializer.data})


class PaymentMethodOrderViewSet(viewsets.ModelViewSet):
    queryset = PaymentMethodOrder.objects.all()
    serializer_class = PaymentMethodOrderSerializer
    pagination_class = None  # No pagination - returns all payment methods

    def list(self, request, *args, **kwargs):
        """Override list to return all results under 'data' key."""
        queryset = self.filter_queryset(self.get_queryset())
        serializer = self.get_serializer(queryset, many=True)
        return Response({'data': serializer.data})
