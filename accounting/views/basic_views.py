"""Basic entity views for the accounting app."""

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response

from ..models import Country, ItemGroup, Item, ItemPrice, ThirdParty
from ..serializers import (
    CountrySerializer,
    ItemGroupSerializer,
    ItemSerializer,
    ItemPriceSerializer,
    ThirdPartySerializer,
)


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

    def perform_create(self, serializer):
        company_id = self.kwargs.get('company_pk')
        if company_id:
            serializer.save(company_id=company_id)
        else:
            serializer.save()

    @action(detail=True, methods=['post'])
    def restore(self, request, pk=None):
        model = self.get_queryset().model
        try:
            obj = model.all_objects.get(pk=pk)
        except model.DoesNotExist:
            return Response({'error': 'Not found.'}, status=status.HTTP_404_NOT_FOUND)
        obj.undelete()
        return Response(self.get_serializer(obj).data)


class ItemPriceViewSet(viewsets.ModelViewSet):
    """
    Item prices scoped to a company via /companies/{company_pk}/item-prices/.

    POST also creates the Item in the same transaction (mirrors Rails behaviour).
    """

    serializer_class = ItemPriceSerializer

    def get_queryset(self):
        company_id = self.kwargs.get('company_pk')
        if company_id:
            return ItemPrice.objects.filter(company_id=company_id).select_related('item')
        return ItemPrice.objects.select_related('item').all()

    def create(self, request, *args, **kwargs):
        from django.db import transaction
        company_id = self.kwargs.get('company_pk')

        item_data = request.data.get('item', {})
        item_price_data = request.data.get('item_price', {})

        with transaction.atomic():
            item_data['company'] = company_id
            item_serializer = ItemSerializer(data=item_data)
            if not item_serializer.is_valid():
                return Response({'errors': item_serializer.errors}, status=status.HTTP_422_UNPROCESSABLE_ENTITY)
            item = item_serializer.save()

            price_data = dict(item_price_data)
            price_data['item'] = item.pk
            price_data['company'] = company_id
            ip_serializer = ItemPriceSerializer(data=price_data)
            if not ip_serializer.is_valid():
                return Response({'errors': ip_serializer.errors}, status=status.HTTP_422_UNPROCESSABLE_ENTITY)
            item_price = ip_serializer.save()

        return Response(
            {'data': {'item': ItemSerializer(item).data, 'item_price': ItemPriceSerializer(item_price).data}},
            status=status.HTTP_201_CREATED,
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