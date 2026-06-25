"""Serializers used to document the Item Excel import/export endpoints in OpenAPI."""

from rest_framework import serializers


class ItemUploadRequestSerializer(serializers.Serializer):
    file = serializers.FileField(help_text='Archivo .xlsx con las columnas de Item a importar.')


class ItemImportRowErrorSerializer(serializers.Serializer):
    row = serializers.IntegerField()
    errors = serializers.DictField(child=serializers.CharField())


class ItemImportResultSerializer(serializers.Serializer):
    created = serializers.IntegerField()
    updated = serializers.IntegerField()
    errors = ItemImportRowErrorSerializer(many=True)
