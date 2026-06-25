"""Basic entity views for the accounting app."""

from django_filters import rest_framework as django_filters
from drf_spectacular.utils import extend_schema
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.filters import OrderingFilter
from rest_framework.response import Response

from ..models import Country, ItemGroup, Item, ItemPrice, ThirdParty
from ..serializers import (
    ChoiceSerializer,
    CountrySerializer,
    ItemGroupSerializer,
    ItemSerializer,
    ItemSelectSerializer,
    ItemPriceSerializer,
    ThirdPartySerializer,
)


class ItemFilter(django_filters.FilterSet):
    base_code = django_filters.CharFilter(lookup_expr='icontains')
    name = django_filters.CharFilter(lookup_expr='icontains')
    base_name = django_filters.CharFilter(lookup_expr='icontains')

    class Meta:
        model = Item
        fields = ['base_code', 'name', 'base_name', 'item_group']


class CountryViewSet(viewsets.ModelViewSet):
    queryset = Country.objects.all()
    serializer_class = CountrySerializer
    pagination_class = None  # No pagination - returns all countries

    def list(self, request, *args, **kwargs):
        """Override list to return all results under 'data' key."""
        queryset = self.filter_queryset(self.get_queryset())
        serializer = self.get_serializer(queryset, many=True)
        return Response({'data': serializer.data})

    @action(detail=True, methods=['post'])
    def restore(self, request, pk=None):
        model = self.get_queryset().model
        try:
            obj = model.all_objects.get(pk=pk)
        except model.DoesNotExist:
            return Response({'error': 'Not found.'}, status=status.HTTP_404_NOT_FOUND)
        obj.undelete()
        return Response(self.get_serializer(obj).data)


class ItemGroupViewSet(viewsets.ModelViewSet):
    queryset = ItemGroup.objects.all()
    serializer_class = ItemGroupSerializer

    @action(detail=True, methods=['post'])
    def restore(self, request, pk=None):
        model = self.get_queryset().model
        try:
            obj = model.all_objects.get(pk=pk)
        except model.DoesNotExist:
            return Response({'error': 'Not found.'}, status=status.HTTP_404_NOT_FOUND)
        obj.undelete()
        return Response(self.get_serializer(obj).data)


class ItemViewSet(viewsets.ModelViewSet):
    """Items scoped to a company via /companies/{company_id}/items/."""

    serializer_class = ItemSerializer
    filter_backends = [django_filters.DjangoFilterBackend, OrderingFilter]
    filterset_class = ItemFilter
    ordering_fields = [
        'code', 'name', 'base_code', 'base_name',
        'item_group__name', 'unit_measure__abbreviation',
        'material', 'color', 'size', 'is_variant',
        'created_at', 'updated_at',
    ]
    ordering = ['created_at']

    def get_queryset(self):
        company_id = self.kwargs.get('company_pk')
        if company_id:
            return Item.objects.filter(company_id=company_id).select_related(
                'item_group', 'unit_measure', 'company',
                'iva_type', 'iva_rate', 'excise_tax_type', 'excise_tax_rate',
            )
        return Item.objects.select_related(
            'item_group', 'unit_measure', 'company',
            'iva_type', 'iva_rate', 'excise_tax_type', 'excise_tax_rate',
        ).all()

    def create(self, request, *args, **kwargs):
        company_id = self.kwargs.get('company_pk')
        data = request.data.copy()
        if company_id:
            data['company'] = company_id
        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    def perform_create(self, serializer):
        company_id = self.kwargs.get('company_pk')
        if company_id:
            serializer.save(company_id=company_id)
        else:
            serializer.save()

    @extend_schema(responses=ItemSelectSerializer(many=True))
    @action(detail=False, methods=['get'], url_path='select-list', pagination_class=None)
    def select_list(self, request, **kwargs):
        """Lightweight, unpaginated list of items (id, code, name) for filter/select inputs."""
        queryset = self.filter_queryset(self.get_queryset())
        serializer = ItemSelectSerializer(queryset, many=True)
        return Response({'data': serializer.data})

    @action(detail=True, methods=['post'])
    def restore(self, request, pk=None):
        model = self.get_queryset().model
        try:
            obj = model.all_objects.get(pk=pk)
        except model.DoesNotExist:
            return Response({'error': 'Not found.'}, status=status.HTTP_404_NOT_FOUND)
        obj.undelete()
        return Response(self.get_serializer(obj).data)


class ItemPriceFilter(django_filters.FilterSet):
    code = django_filters.CharFilter(field_name='item__code', lookup_expr='icontains')
    name = django_filters.CharFilter(field_name='item__name', lookup_expr='icontains')

    class Meta:
        model = ItemPrice
        fields = ['code', 'name', 'item_price_type']


class ItemPriceViewSet(viewsets.ModelViewSet):
    """Item prices scoped to a company via /companies/{company_pk}/item-prices/.

    POST expects an existing 'item' id; it does not create the Item.
    """

    serializer_class = ItemPriceSerializer
    filter_backends = [django_filters.DjangoFilterBackend, OrderingFilter]
    filterset_class = ItemPriceFilter
    ordering_fields = [
        'item__code', 'item__name', 'item_price_type',
        'price', 'iva', 'excise_tax', 'total',
        'created_at', 'updated_at',
    ]
    ordering = ['-created_at']

    def get_queryset(self):
        company_id = self.kwargs.get('company_pk')
        if company_id:
            return ItemPrice.objects.filter(company_id=company_id).select_related('item')
        return ItemPrice.objects.select_related('item').all()

    def create(self, request, *args, **kwargs):
        company_id = self.kwargs.get('company_pk')
        data = request.data.copy()
        if company_id:
            data['company'] = company_id
        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    def perform_create(self, serializer):
        company_id = self.kwargs.get('company_pk')
        if company_id:
            serializer.save(company_id=company_id)
        else:
            serializer.save()

    @extend_schema(responses=ChoiceSerializer(many=True))
    @action(detail=False, methods=['get'], url_path='price-types', pagination_class=None)
    def price_types(self, request, **kwargs):
        return Response(
            {'data': [{'value': value, 'label': label} for value, label in ItemPrice.PRICE_TYPE_CHOICES]}
        )

    @action(detail=True, methods=['post'])
    def restore(self, request, pk=None):
        model = self.get_queryset().model
        try:
            obj = model.all_objects.get(pk=pk)
        except model.DoesNotExist:
            return Response({'error': 'Not found.'}, status=status.HTTP_404_NOT_FOUND)
        obj.undelete()
        return Response(self.get_serializer(obj).data)


class ThirdPartyViewSet(viewsets.ModelViewSet):
    serializer_class = ThirdPartySerializer

    def get_queryset(self):
        company_id = self.kwargs.get('company_pk')
        if company_id:
            return ThirdParty.objects.filter(company_id=company_id).select_related(
                'document_type', 'company', 'country',
                'colombian_city', 'colombian_department', 'dian_economic_activity',
            )
        return ThirdParty.objects.select_related(
            'document_type', 'company', 'country',
            'colombian_city', 'colombian_department', 'dian_economic_activity',
        ).all()

    @action(detail=False, methods=['get'], url_path='third-party-types')
    def third_party_types(self, request, **kwargs):
        return Response({'data': [choice[0] for choice in ThirdParty.THIRD_PARTY_TYPE_CHOICES]})

    @action(detail=True, methods=['post'])
    def restore(self, request, pk=None):
        model = self.get_queryset().model
        try:
            obj = model.all_objects.get(pk=pk)
        except model.DoesNotExist:
            return Response({'error': 'Not found.'}, status=status.HTTP_404_NOT_FOUND)
        obj.undelete()
        return Response(self.get_serializer(obj).data)