"""Order related serializers."""

from rest_framework import serializers
from ..models import Order, OrderItem, ItemPropertyType, ItemPropertyValue, ItemProperty


class OrderItemCreateSerializer(serializers.Serializer):
    """Serializer for creating order items within order creation."""
    item_price = serializers.IntegerField()
    quantity = serializers.DecimalField(max_digits=10, decimal_places=2)
    unit_price = serializers.DecimalField(max_digits=15, decimal_places=2)
    item_properties = serializers.JSONField(required=False, allow_null=True)
    line_iva = serializers.DecimalField(max_digits=15, decimal_places=2)
    line_total_with_taxes = serializers.DecimalField(max_digits=15, decimal_places=2)
    
    def validate(self, data):
        """Validate that the calculation is correct."""
        quantity = data['quantity']
        unit_price = data['unit_price']
        line_iva = data['line_iva']
        line_total_with_taxes = data['line_total_with_taxes']
        
        # Calculate expected total: (unit_price * quantity) + (quantity * line_iva)
        line_total = quantity * unit_price
        expected_total = line_total + (quantity * line_iva)
        
        if abs(expected_total - line_total_with_taxes) > 0.01:  # Allow for small rounding differences
            raise serializers.ValidationError(
                f"Calculation error: (unit_price * quantity) + (quantity * line_iva) "
                f"should equal line_total_with_taxes. "
                f"Expected: {expected_total}, Got: {line_total_with_taxes}"
            )
        
        return data


class OrderItemSerializer(serializers.ModelSerializer):
    """Serializer for OrderItem model."""
    item_name = serializers.CharField(source='item_price.item.name', read_only=True)
    item_code = serializers.CharField(source='item_price.item.code', read_only=True)
    unit_measure = serializers.CharField(source='item_price.item.unit_measure.name', read_only=True)
    
    class Meta:
        model = OrderItem
        fields = [
            'id', 'quantity', 'unit_price', 'line_total', 'item_properties',
            'line_iva', 'line_excise_tax', 'line_total_with_taxes',
            'item_price', 'item_name', 'item_code', 'unit_measure',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['line_total', 'line_iva', 'line_excise_tax', 'line_total_with_taxes']


class OrderSerializer(serializers.ModelSerializer):
    """Serializer for Order model with order items."""
    order_items = OrderItemSerializer(many=True, read_only=True)
    third_party_name = serializers.CharField(source='third_party.__str__', read_only=True)
    company_name = serializers.CharField(source='company.name', read_only=True)
    sale_type_name = serializers.CharField(source='sale_type.name', read_only=True)
    payment_method_name = serializers.CharField(source='payment_method.name', read_only=True)
    
    class Meta:
        model = Order
        fields = [
            'id', 'order_number', 'order_type', 'status', 'order_date', 'delivery_date',
            'company', 'company_name', 'third_party', 'third_party_name',
            'sale_type', 'sale_type_name', 'payment_method', 'payment_method_name',
            'subtotal', 'total_iva', 'total_excise_tax', 'total_amount',
            'notes', 'order_items', 'created_at', 'updated_at'
        ]
        read_only_fields = ['order_date', 'order_number', 'subtotal', 'total_iva', 'total_excise_tax', 'total_amount']


class OrderCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating orders with items."""
    order_items = OrderItemCreateSerializer(many=True, write_only=True)
    
    class Meta:
        model = Order
        fields = [
            'order_type', 'status', 'delivery_date',
            'company', 'third_party', 'sale_type', 'payment_method',
            'notes', 'order_items'
        ]

    def validate_order_items(self, order_items_data):
        """Validate that order_items is not empty and item_prices exist."""
        if not order_items_data:
            raise serializers.ValidationError("At least one order item is required.")
        
        # Validate that all item_price IDs exist
        from ..models import ItemPrice
        item_price_ids = [item['item_price'] for item in order_items_data]
        existing_ids = set(ItemPrice.objects.filter(id__in=item_price_ids).values_list('id', flat=True))
        missing_ids = set(item_price_ids) - existing_ids
        
        if missing_ids:
            raise serializers.ValidationError(f"ItemPrice IDs not found: {list(missing_ids)}")
        
        return order_items_data

    def create(self, validated_data):
        """Create order with items and calculate totals."""
        from ..models import OrderItem, ItemPrice
        
        order_items_data = validated_data.pop('order_items', [])
        
        # Create order (order_number will be auto-generated in save method)
        order = Order.objects.create(**validated_data)
        
        # Create order items and calculate totals
        total_subtotal = 0
        total_iva = 0
        total_amount = 0
        
        for item_data in order_items_data:
            item_price = ItemPrice.objects.get(id=item_data['item_price'])
            
            # Calculate line total (before taxes)
            line_total = item_data['quantity'] * item_data['unit_price']
            
            order_item = OrderItem.objects.create(
                order=order,
                item_price=item_price,
                quantity=item_data['quantity'],
                unit_price=item_data['unit_price'],
                line_total=line_total,
                item_properties=item_data.get('item_properties'),
                line_iva=item_data['line_iva'],
                line_excise_tax=0,  # Not included in the validation, set to 0
                line_total_with_taxes=item_data['line_total_with_taxes']
            )
            
            # Accumulate totals
            total_subtotal += line_total
            total_iva += item_data['line_iva']
            total_amount += item_data['line_total_with_taxes']
        
        # Update order totals
        order.subtotal = total_subtotal
        order.total_iva = total_iva
        order.total_excise_tax = 0  # No excise tax in this implementation
        order.total_amount = total_amount
        order.save()
        
        return order


class ItemPropertyValueSerializer(serializers.ModelSerializer):
    """Serializer for ItemPropertyValue model."""
    property_type_name = serializers.CharField(source='property_type.name', read_only=True)
    
    class Meta:
        model = ItemPropertyValue
        fields = ['id', 'property_type', 'property_type_name', 'value', 'created_at']


class ItemPropertyTypeSerializer(serializers.ModelSerializer):
    """Serializer for ItemPropertyType model."""
    possible_values = ItemPropertyValueSerializer(many=True, read_only=True)
    
    class Meta:
        model = ItemPropertyType
        fields = ['id', 'name', 'data_type', 'is_required', 'possible_values', 'created_at']


class ItemPropertySerializer(serializers.ModelSerializer):
    """Serializer for ItemProperty model."""
    property_type_name = serializers.CharField(source='property_type.name', read_only=True)
    property_type_data_type = serializers.CharField(source='property_type.data_type', read_only=True)
    display_value = serializers.CharField(source='get_value', read_only=True)
    
    class Meta:
        model = ItemProperty
        fields = [
            'id', 'item', 'property_type', 'property_type_name', 'property_type_data_type',
            'text_value', 'number_value', 'decimal_value', 'boolean_value', 
            'date_value', 'choice_value', 'display_value', 'created_at'
        ]

    def validate(self, data):
        """Ensure only the correct value field is populated based on property type."""
        property_type = data['property_type']
        data_type = property_type.data_type
        
        # Clear all value fields first
        value_fields = ['text_value', 'number_value', 'decimal_value', 'boolean_value', 'date_value', 'choice_value']
        
        # Check that the correct field is provided
        if data_type == 'text' and not data.get('text_value'):
            raise serializers.ValidationError("text_value is required for text properties")
        elif data_type == 'number' and data.get('number_value') is None:
            raise serializers.ValidationError("number_value is required for number properties")
        elif data_type == 'decimal' and data.get('decimal_value') is None:
            raise serializers.ValidationError("decimal_value is required for decimal properties")
        elif data_type == 'boolean' and data.get('boolean_value') is None:
            raise serializers.ValidationError("boolean_value is required for boolean properties")
        elif data_type == 'date' and not data.get('date_value'):
            raise serializers.ValidationError("date_value is required for date properties")
        elif data_type in ['choice', 'multiple_choice'] and not data.get('choice_value'):
            raise serializers.ValidationError("choice_value is required for choice properties")
        
        return data