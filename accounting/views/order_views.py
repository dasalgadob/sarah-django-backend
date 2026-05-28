"""Views for Order and Item Properties management."""

from django.db import models
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter

from ..models import Order, OrderItem, ItemPropertyType, ItemPropertyValue, ItemProperty, ItemPropertyDataType
from ..serializers.order_serializer import (
    OrderSerializer, OrderCreateSerializer, OrderItemSerializer,
    ItemPropertyDataTypeSerializer, ItemPropertyTypeSerializer, ItemPropertyValueSerializer, ItemPropertySerializer
)


class OrderViewSet(viewsets.ModelViewSet):
    """ViewSet for Order management."""
    queryset = Order.objects.all()
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['order_type', 'status', 'company', 'third_party']
    search_fields = ['order_number', 'third_party__legal_name', 'third_party__company_name', 'notes']
    ordering_fields = ['order_date', 'order_number', 'total_amount']
    ordering = ['-order_date']

    def get_serializer_class(self):
        """Use different serializers for different actions."""
        if self.action == 'create':
            return OrderCreateSerializer
        return OrderSerializer

    def get_queryset(self):
        """Filter queryset by company if user is associated with one."""
        queryset = Order.objects.select_related('company', 'third_party')
        
        # Add company filtering logic here if needed
        # For example, if user has a company association:
        # if hasattr(self.request.user, 'company_id'):
        #     queryset = queryset.filter(company_id=self.request.user.company_id)
        
        return queryset

    @action(detail=True, methods=['post'])
    def confirm_order(self, request, pk=None):
        """Confirm a draft order."""
        order = self.get_object()
        if order.status != 'draft':
            return Response(
                {'error': 'Only draft orders can be confirmed'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        order.status = 'confirmed'
        order.save()
        
        serializer = self.get_serializer(order)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def cancel_order(self, request, pk=None):
        """Cancel an order."""
        order = self.get_object()
        if order.status in ['completed', 'cancelled']:
            return Response(
                {'error': f'{order.status} orders cannot be cancelled'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        order.status = 'cancelled'
        order.save()
        
        serializer = self.get_serializer(order)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def summary(self, request):
        """Get order summary statistics."""
        queryset = self.get_queryset()
        
        summary = {
            'total_orders': queryset.count(),
            'by_status': {},
            'by_type': {},
            'total_amount_sum': 0
        }
        
        # Count by status
        for status_choice in Order.STATUS_CHOICES:
            status_code, status_name = status_choice
            count = queryset.filter(status=status_code).count()
            summary['by_status'][status_code] = {
                'name': status_name,
                'count': count
            }
        
        # Count by type
        for type_choice in Order.ORDER_TYPE_CHOICES:
            type_code, type_name = type_choice
            count = queryset.filter(order_type=type_code).count()
            summary['by_type'][type_code] = {
                'name': type_name,
                'count': count
            }
        
        # Calculate total amount
        total_amount = queryset.aggregate(total=models.Sum('total_amount'))['total'] or 0
        summary['total_amount_sum'] = total_amount
        
        return Response(summary)

    @action(detail=True, methods=['post'])
    def restore(self, request, pk=None):
        model = self.get_queryset().model
        try:
            obj = model.all_objects.get(pk=pk)
        except model.DoesNotExist:
            return Response({'error': 'Not found.'}, status=status.HTTP_404_NOT_FOUND)
        obj.undelete()
        return Response(self.get_serializer(obj).data)


class OrderItemViewSet(viewsets.ModelViewSet):
    """ViewSet for OrderItem management."""
    queryset = OrderItem.objects.all()
    serializer_class = OrderItemSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['order', 'item_price__item', 'item_price__item__company']
    search_fields = ['item_price__item__name', 'item_price__item__code']
    ordering_fields = ['created_at', 'quantity', 'unit_price', 'line_total_with_taxes']
    ordering = ['-created_at']

    def get_queryset(self):
        """Optimize queries with select_related."""
        return OrderItem.objects.select_related(
            'order', 'item_price', 'item_price__item', 'item_price__item__company'
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


class ItemPropertyDataTypeViewSet(viewsets.ModelViewSet):
    """ViewSet for ItemPropertyDataType — the available data types for item properties."""
    queryset = ItemPropertyDataType.objects.all()
    serializer_class = ItemPropertyDataTypeSerializer
    pagination_class = None  # small, static list — return all

    @action(detail=True, methods=['post'])
    def restore(self, request, pk=None):
        model = self.get_queryset().model
        try:
            obj = model.all_objects.get(pk=pk)
        except model.DoesNotExist:
            return Response({'error': 'Not found.'}, status=status.HTTP_404_NOT_FOUND)
        obj.undelete()
        return Response(self.get_serializer(obj).data)


class ItemPropertyTypeViewSet(viewsets.ModelViewSet):
    """ViewSet for ItemPropertyType management."""
    queryset = ItemPropertyType.objects.all()
    serializer_class = ItemPropertyTypeSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['data_type', 'data_type__code', 'is_required']
    search_fields = ['name']
    ordering_fields = ['name', 'created_at']
    ordering = ['name']

    def get_queryset(self):
        """Include possible values in the queryset."""
        return ItemPropertyType.objects.prefetch_related('possible_values')

    @action(detail=False, methods=['get', 'post'], url_path='company/(?P<company_id>[^/.]+)')
    def by_company(self, request, company_id=None):
        """List or create item property types for a specific company."""
        if request.method == 'POST':
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            serializer.save(company_id=company_id)
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        queryset = self.get_queryset().filter(company_id=company_id)
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def add_value(self, request, pk=None):
        """Add a possible value to a choice-based property type."""
        property_type = self.get_object()
        
        if property_type.data_type and property_type.data_type.code not in ['choice', 'multiple_choice']:
            return Response(
                {'error': 'Values can only be added to choice-based properties'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        value = request.data.get('value')
        if not value:
            return Response(
                {'error': 'Value is required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Check if value already exists
        if ItemPropertyValue.objects.filter(property_type=property_type, value=value).exists():
            return Response(
                {'error': 'Value already exists for this property type'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        property_value = ItemPropertyValue.objects.create(
            property_type=property_type,
            value=value
        )
        
        serializer = ItemPropertyValueSerializer(property_value)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['post'])
    def restore(self, request, pk=None):
        model = self.get_queryset().model
        try:
            obj = model.all_objects.get(pk=pk)
        except model.DoesNotExist:
            return Response({'error': 'Not found.'}, status=status.HTTP_404_NOT_FOUND)
        obj.undelete()
        return Response(self.get_serializer(obj).data)


class ItemPropertyValueViewSet(viewsets.ModelViewSet):
    """ViewSet for ItemPropertyValue management."""
    queryset = ItemPropertyValue.objects.all()
    serializer_class = ItemPropertyValueSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['property_type']
    search_fields = ['value']
    ordering_fields = ['value', 'created_at']
    ordering = ['property_type__name', 'value']

    def get_queryset(self):
        """Optimize queries with select_related."""
        return ItemPropertyValue.objects.select_related('property_type')

    @action(detail=True, methods=['post'])
    def restore(self, request, pk=None):
        model = self.get_queryset().model
        try:
            obj = model.all_objects.get(pk=pk)
        except model.DoesNotExist:
            return Response({'error': 'Not found.'}, status=status.HTTP_404_NOT_FOUND)
        obj.undelete()
        return Response(self.get_serializer(obj).data)


class ItemPropertyViewSet(viewsets.ModelViewSet):
    """ViewSet for ItemProperty management."""
    queryset = ItemProperty.objects.all()
    serializer_class = ItemPropertySerializer
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['item', 'property_type', 'property_type__data_type__code']
    search_fields = ['item__name', 'item__code', 'property_type__name', 'text_value']
    ordering_fields = ['created_at', 'property_type__name']
    ordering = ['item__name', 'property_type__name']

    def get_queryset(self):
        """Optimize queries with select_related."""
        return ItemProperty.objects.select_related(
            'item', 'property_type', 'choice_value', 'choice_value__property_type'
        )

    @action(detail=False, methods=['get'])
    def by_item(self, request):
        """Get all properties for a specific item."""
        item_id = request.query_params.get('item_id')
        if not item_id:
            return Response(
                {'error': 'item_id parameter is required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        properties = self.get_queryset().filter(item_id=item_id)
        serializer = self.get_serializer(properties, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['post'])
    def bulk_create(self, request):
        """Create multiple properties for an item at once."""
        item_id = request.data.get('item_id')
        properties_data = request.data.get('properties', [])
        
        if not item_id or not properties_data:
            return Response(
                {'error': 'item_id and properties are required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        created_properties = []
        errors = []
        
        for prop_data in properties_data:
            prop_data['item'] = item_id
            serializer = self.get_serializer(data=prop_data)
            
            if serializer.is_valid():
                property_obj = serializer.save()
                created_properties.append(serializer.data)
            else:
                errors.append({
                    'property_type': prop_data.get('property_type'),
                    'errors': serializer.errors
                })
        
        response_data = {
            'created': created_properties,
            'errors': errors,
            'created_count': len(created_properties),
            'error_count': len(errors)
        }

        return Response(response_data, status=status.HTTP_201_CREATED if created_properties else status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'])
    def restore(self, request, pk=None):
        model = self.get_queryset().model
        try:
            obj = model.all_objects.get(pk=pk)
        except model.DoesNotExist:
            return Response({'error': 'Not found.'}, status=status.HTTP_404_NOT_FOUND)
        obj.undelete()
        return Response(self.get_serializer(obj).data)