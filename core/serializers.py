"""Serializers for the core app."""

from django.contrib.auth.models import User
from rest_framework import serializers

from .models import Role, Company


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'is_active', 'date_joined']
        read_only_fields = ['id', 'date_joined']


class RoleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Role
        fields = ['id', 'name', 'users']


class CompanySerializer(serializers.ModelSerializer):
    # Nested read-only detail fields
    document_type_name = serializers.CharField(source='document_type.name', read_only=True)
    country_name = serializers.CharField(source='country.name', read_only=True)
    city_name = serializers.CharField(source='colombian_city.name', read_only=True)
    department_name = serializers.CharField(source='colombian_department.name', read_only=True)
    dian_economic_activity_name = serializers.CharField(
        source='dian_economic_activity.name', read_only=True
    )

    class Meta:
        model = Company
        fields = [
            'id',
            'document_type',
            'document_type_name',
            'document_number',
            'dv',
            'legal_name',
            'company_name',
            'first_name',
            'middle_name',
            'first_lastname',
            'second_last_name',
            'country',
            'country_name',
            'colombian_city',
            'city_name',
            'colombian_department',
            'department_name',
            'main_address',
            'email',
            'phone',
            'dian_economic_activity',
            'dian_economic_activity_name',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
