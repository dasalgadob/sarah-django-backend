"""Serializers for the reference_tables app."""

from rest_framework import serializers

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


class ColombianDepartmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = ColombianDepartment
        fields = ['id', 'code', 'name']


class ColombianCitySerializer(serializers.ModelSerializer):
    colombian_department = ColombianDepartmentSerializer(read_only=True)
    colombian_department_id = serializers.PrimaryKeyRelatedField(
        queryset=ColombianDepartment.objects.all(),
        source='colombian_department',
        write_only=True,
    )

    class Meta:
        model = ColombianCity
        fields = ['id', 'code', 'name', 'colombian_department', 'colombian_department_id']


class DianEconomicActivitySerializer(serializers.ModelSerializer):
    class Meta:
        model = DianEconomicActivity
        fields = ['id', 'code', 'name']


class DocumentTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = DocumentType
        fields = ['id', 'code', 'name']


class ExciseTaxTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = ExciseTaxType
        fields = ['id', 'name']


class ExciseTaxRateSerializer(serializers.ModelSerializer):
    excise_tax_type = ExciseTaxTypeSerializer(read_only=True)
    excise_tax_type_id = serializers.PrimaryKeyRelatedField(
        queryset=ExciseTaxType.objects.all(),
        source='excise_tax_type',
        write_only=True,
    )

    class Meta:
        model = ExciseTaxRate
        fields = ['id', 'value', 'excise_tax_type', 'excise_tax_type_id']


class IvaTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = IvaType
        fields = ['id', 'name']


class IvaRateSerializer(serializers.ModelSerializer):
    iva_type = IvaTypeSerializer(read_only=True)
    iva_type_id = serializers.PrimaryKeyRelatedField(
        queryset=IvaType.objects.all(),
        source='iva_type',
        write_only=True,
    )

    class Meta:
        model = IvaRate
        fields = ['id', 'value', 'iva_type', 'iva_type_id']


class UnitMeasureSerializer(serializers.ModelSerializer):
    class Meta:
        model = UnitMeasure
        fields = ['id', 'abbreviation', 'name']


class SaleTypeOrderSerializer(serializers.ModelSerializer):
    class Meta:
        model = SaleTypeOrder
        fields = ['id', 'name', 'created_at', 'updated_at']


class PaymentMethodOrderSerializer(serializers.ModelSerializer):
    class Meta:
        model = PaymentMethodOrder
        fields = ['id', 'name', 'created_at', 'updated_at']
