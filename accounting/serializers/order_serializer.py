"""Order related serializers."""

from rest_framework import serializers
from ..models import Order, OrderItem, ItemPropertyType, ItemPropertyValue, ItemProperty, ItemPropertyDataType


def _resolve_order_item_line(item_data):
    """Resolve item_price, the effective unit_price and computed taxes for one order item.

    unit_price is an optional override -- if omitted or equal to the
    referenced ItemPrice.price, the ItemPrice's price is used. IVA, excise
    tax and totals are always computed from the resolved unit_price and the
    item's tax rates, never accepted from the payload.
    """
    from ..models import ItemPrice
    from ..services.tax_calculations import calculate_taxes

    item_price = ItemPrice.objects.select_related('item').get(id=item_data['item_price'])

    override_price = item_data.get('unit_price')
    unit_price = override_price if override_price not in (None, item_price.price) else item_price.price

    line_total = item_data['quantity'] * unit_price
    line_iva, line_excise_tax, line_total_with_taxes = calculate_taxes(item_price.item, line_total)

    return item_price, unit_price, line_total, line_iva, line_excise_tax, line_total_with_taxes


class OrderItemCreateSerializer(serializers.Serializer):
    """Serializer for creating order items within order creation.

    unit_price is an optional override -- if omitted or equal to the
    referenced ItemPrice.price, the ItemPrice's price is used. IVA, excise
    tax and totals are never accepted here; they're always computed from
    the resolved unit_price and the item's tax rates in OrderCreateSerializer.
    """
    item_price = serializers.IntegerField()
    quantity = serializers.DecimalField(max_digits=10, decimal_places=2)
    unit_price = serializers.DecimalField(max_digits=15, decimal_places=2, required=False)
    item_properties = serializers.JSONField(required=False, allow_null=True)


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
        """Create order with items; unit_price may be overridden but taxes/totals are always computed."""
        from ..models import OrderItem

        order_items_data = validated_data.pop('order_items', [])

        # Create order (order_number will be auto-generated in save method)
        order = Order.objects.create(**validated_data)

        total_subtotal = 0
        total_iva = 0
        total_excise_tax = 0
        total_amount = 0

        for item_data in order_items_data:
            item_price, unit_price, line_total, line_iva, line_excise_tax, line_total_with_taxes = (
                _resolve_order_item_line(item_data)
            )

            OrderItem.objects.create(
                order=order,
                item_price=item_price,
                quantity=item_data['quantity'],
                unit_price=unit_price,
                line_total=line_total,
                item_properties=item_data.get('item_properties'),
                line_iva=line_iva,
                line_excise_tax=line_excise_tax,
                line_total_with_taxes=line_total_with_taxes,
            )

            total_subtotal += line_total
            total_iva += line_iva
            total_excise_tax += line_excise_tax
            total_amount += line_total_with_taxes

        # Update order totals
        order.subtotal = total_subtotal
        order.total_iva = total_iva
        order.total_excise_tax = total_excise_tax
        order.total_amount = total_amount
        order.save()

        return order


class OrderItemUpdateSerializer(OrderItemCreateSerializer):
    """Order item entry within an order update.

    Adds an optional 'id': if it matches an existing OrderItem on this
    order, that line is updated; if omitted, a new line is created.
    """
    id = serializers.IntegerField(required=False)


class OrderUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating orders, including a full-replace of order_items.

    When order_items is provided: entries with 'id' update that existing
    line, entries without 'id' create a new line, and any existing line
    on the order NOT referenced by id in the payload is deleted. Pricing
    and tax computation mirrors OrderCreateSerializer.
    """
    order_items = OrderItemUpdateSerializer(many=True, required=False, write_only=True)

    class Meta:
        model = Order
        fields = [
            'order_type', 'status', 'delivery_date',
            'company', 'third_party', 'sale_type', 'payment_method',
            'notes', 'order_items',
        ]
        extra_kwargs = {
            'order_type': {'required': False},
            'company': {'required': False},
            'third_party': {'required': False},
            'sale_type': {'required': False},
            'payment_method': {'required': False},
        }

    def validate_order_items(self, order_items_data):
        from ..models import ItemPrice

        item_price_ids = [item['item_price'] for item in order_items_data]
        existing_item_price_ids = set(ItemPrice.objects.filter(id__in=item_price_ids).values_list('id', flat=True))
        missing_item_price_ids = set(item_price_ids) - existing_item_price_ids
        if missing_item_price_ids:
            raise serializers.ValidationError(f"ItemPrice IDs not found: {list(missing_item_price_ids)}")

        if self.instance is not None:
            existing_order_item_ids = set(self.instance.order_items.values_list('id', flat=True))
            provided_ids = {item['id'] for item in order_items_data if item.get('id')}
            unknown_ids = provided_ids - existing_order_item_ids
            if unknown_ids:
                raise serializers.ValidationError(
                    f"order_items ids not found on this order: {list(unknown_ids)}"
                )

        return order_items_data

    def update(self, instance, validated_data):
        from ..models import OrderItem

        order_items_data = validated_data.pop('order_items', None)

        for field, value in validated_data.items():
            setattr(instance, field, value)
        instance.save()

        if order_items_data is not None:
            existing_items = {order_item.id: order_item for order_item in instance.order_items.all()}
            seen_ids = set()

            total_subtotal = 0
            total_iva = 0
            total_excise_tax = 0
            total_amount = 0

            for item_data in order_items_data:
                item_price, unit_price, line_total, line_iva, line_excise_tax, line_total_with_taxes = (
                    _resolve_order_item_line(item_data)
                )

                item_id = item_data.get('id')
                if item_id:
                    order_item = existing_items[item_id]
                    order_item.item_price = item_price
                    order_item.quantity = item_data['quantity']
                    order_item.unit_price = unit_price
                    order_item.line_total = line_total
                    order_item.item_properties = item_data.get('item_properties')
                    order_item.line_iva = line_iva
                    order_item.line_excise_tax = line_excise_tax
                    order_item.line_total_with_taxes = line_total_with_taxes
                    order_item.save()
                    seen_ids.add(item_id)
                else:
                    OrderItem.objects.create(
                        order=instance,
                        item_price=item_price,
                        quantity=item_data['quantity'],
                        unit_price=unit_price,
                        line_total=line_total,
                        item_properties=item_data.get('item_properties'),
                        line_iva=line_iva,
                        line_excise_tax=line_excise_tax,
                        line_total_with_taxes=line_total_with_taxes,
                    )

                total_subtotal += line_total
                total_iva += line_iva
                total_excise_tax += line_excise_tax
                total_amount += line_total_with_taxes

            # Full replace: delete existing lines not referenced by id in the payload.
            for existing_id, existing_item in existing_items.items():
                if existing_id not in seen_ids:
                    existing_item.delete()

            instance.subtotal = total_subtotal
            instance.total_iva = total_iva
            instance.total_excise_tax = total_excise_tax
            instance.total_amount = total_amount
            instance.save()

        return instance


class ItemPropertyValueSerializer(serializers.ModelSerializer):
    """Serializer for ItemPropertyValue model."""
    property_type_name = serializers.CharField(source='property_type.name', read_only=True)
    
    class Meta:
        model = ItemPropertyValue
        fields = ['id', 'property_type', 'property_type_name', 'value', 'created_at']


class ItemPropertyDataTypeSerializer(serializers.ModelSerializer):
    """Serializer for ItemPropertyDataType model."""

    class Meta:
        model = ItemPropertyDataType
        fields = ['id', 'code', 'name', 'name_es']


class ItemPropertyTypeSerializer(serializers.ModelSerializer):
    """Serializer for ItemPropertyType model."""
    possible_values = ItemPropertyValueSerializer(many=True, read_only=True)
    data_type_detail = ItemPropertyDataTypeSerializer(source='data_type', read_only=True)

    class Meta:
        model = ItemPropertyType
        fields = ['id', 'name', 'company', 'data_type', 'data_type_detail', 'is_required', 'possible_values', 'created_at']


class ItemPropertySerializer(serializers.ModelSerializer):
    """Serializer for ItemProperty model."""
    property_type_name = serializers.CharField(source='property_type.name', read_only=True)
    property_type_data_type = serializers.CharField(source='property_type.data_type.code', read_only=True)
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
        data_type = property_type.data_type.code if property_type.data_type else None
        
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