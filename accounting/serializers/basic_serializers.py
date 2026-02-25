"""Basic entity serializers for the accounting app."""

from rest_framework import serializers

from ..models import Country, ItemGroup, Item, ItemPrice, ThirdParty


class CountrySerializer(serializers.ModelSerializer):
    class Meta:
        model = Country
        fields = ['id', 'code', 'name']


class ItemGroupSerializer(serializers.ModelSerializer):
    class Meta:
        model = ItemGroup
        fields = ['id', 'name']


class ItemSerializer(serializers.ModelSerializer):
    item_group_name = serializers.CharField(source='item_group.name', read_only=True)
    unit_measure_abbreviation = serializers.CharField(
        source='unit_measure.abbreviation', read_only=True
    )

    class Meta:
        model = Item
        fields = [
            'id',
            'base_code',
            'variant_code', 
            'code',
            'name',
            'base_name',
            'item_group',
            'item_group_name',
            'unit_measure',
            'unit_measure_abbreviation',
            'company',
            'is_variant',
            'parent_item',
            'material',
            'color',
            'size',
            'iva_type',
            'iva_rate',
            'excise_tax_type',
            'excise_tax_rate',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'code', 'created_at', 'updated_at']


class ItemPriceSerializer(serializers.ModelSerializer):
    item_detail = ItemSerializer(source='item', read_only=True)

    class Meta:
        model = ItemPrice
        fields = [
            'id',
            'price',
            'iva',
            'excise_tax',
            'total',
            'item_price_type',
            'item',
            'item_detail',
            'company',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class ThirdPartySerializer(serializers.ModelSerializer):
    city_name = serializers.CharField(source='colombian_city.name', read_only=True)
    department_name = serializers.CharField(source='colombian_department.name', read_only=True)
    country_name = serializers.CharField(source='country.name', read_only=True)
    document_type_code = serializers.IntegerField(source='document_type.code', read_only=True)
    document_type_name = serializers.CharField(source='document_type.name', read_only=True)

    class Meta:
        model = ThirdParty
        fields = [
            'id',
            'document_type',
            'document_type_code',
            'document_type_name',
            'document_number',
            'email',
            'address',
            'neighborhood',
            'third_party_type',
            'company',
            'phone',
            'country',
            'country_name',
            'colombian_city',
            'city_name',
            'colombian_department',
            'department_name',
            'dian_economic_activity',
            'legal_name',
            'company_name',
            'first_name',
            'middle_name',
            'first_lastname',
            'second_last_name',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']