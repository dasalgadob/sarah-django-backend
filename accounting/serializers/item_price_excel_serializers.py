"""Serializers used to document the ItemPrice Excel import/export endpoints in OpenAPI."""

from rest_framework import serializers


class ItemPriceUploadRequestSerializer(serializers.Serializer):
    file = serializers.FileField(help_text='Archivo .xlsx con las columnas de ItemPrice a importar.')


class ItemPriceImportRowErrorSerializer(serializers.Serializer):
    row = serializers.IntegerField()
    errors = serializers.DictField(child=serializers.CharField())


class ItemPriceImportResultSerializer(serializers.Serializer):
    created = serializers.IntegerField()
    updated = serializers.IntegerField()
    errors = ItemPriceImportRowErrorSerializer(many=True)
