"""Admin registrations for the accounting app."""

from django.contrib import admin

from .models import (
    Country, ItemGroup, Item, ItemPrice, ThirdParty,
    Order, OrderItem, OrderCounter, ItemPropertyType, ItemPropertyValue, ItemProperty
)


@admin.register(Item)
class ItemAdmin(admin.ModelAdmin):
    list_display = ['code', 'name', 'company', 'item_group', 'unit_measure', 'is_variant', 'material', 'created_at']
    list_filter = ['company', 'item_group', 'unit_measure', 'is_variant', 'material']
    search_fields = ['code', 'name', 'base_code', 'base_name']
    list_per_page = 50
    ordering = ['company', 'base_code', 'variant_code']
    readonly_fields = ['code', 'created_at', 'updated_at']

    fieldsets = (
        ('Product Information', {
            'fields': ('base_code', 'variant_code', 'code', 'base_name', 'name', 'company', 'item_group', 'unit_measure')
        }),
        ('Variant Details', {
            'fields': ('is_variant', 'parent_item', 'material', 'color', 'size'),
            'classes': ('collapse',)
        }),
        ('Tax Information', {
            'fields': ('iva_type', 'iva_rate', 'excise_tax_type', 'excise_tax_rate'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ['line_total', 'line_iva', 'line_excise_tax', 'line_total_with_taxes']
    fields = ['item_price', 'quantity', 'unit_price', 'line_total', 'line_iva', 'line_excise_tax', 'line_total_with_taxes']


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['order_number', 'order_type', 'status', 'company', 'third_party', 'sale_type', 'payment_method', 'order_date', 'total_amount']
    list_filter = ['order_type', 'status', 'company', 'sale_type', 'payment_method', 'order_date']
    search_fields = ['order_number', 'third_party__legal_name', 'third_party__company_name']
    inlines = [OrderItemInline]
    readonly_fields = ['order_date', 'created_at', 'updated_at']
    
    fieldsets = (
        ('Order Information', {
            'fields': ('order_number', 'order_type', 'status', 'order_date', 'delivery_date')
        }),
        ('Parties', {
            'fields': ('company', 'third_party')
        }),
        ('Sales Information', {
            'fields': ('sale_type', 'payment_method')
        }),
        ('Totals', {
            'fields': ('subtotal', 'total_iva', 'total_excise_tax', 'total_amount'),
            'classes': ('collapse',)
        }),
        ('Additional Information', {
            'fields': ('notes',),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ['order', 'item_price', 'quantity', 'unit_price', 'line_total_with_taxes']
    list_filter = ['order__company', 'order__order_type', 'order__status']
    search_fields = ['order__order_number', 'item_price__item__name', 'item_price__item__code']


class ItemPropertyValueInline(admin.TabularInline):
    model = ItemPropertyValue
    extra = 0


@admin.register(ItemPropertyType)
class ItemPropertyTypeAdmin(admin.ModelAdmin):
    list_display = ['name', 'data_type', 'is_required', 'created_at']
    list_filter = ['data_type', 'is_required']
    search_fields = ['name']
    inlines = [ItemPropertyValueInline]
    ordering = ['name']


@admin.register(ItemPropertyValue)
class ItemPropertyValueAdmin(admin.ModelAdmin):
    list_display = ['property_type', 'value', 'created_at']
    list_filter = ['property_type']
    search_fields = ['value', 'property_type__name']
    ordering = ['property_type__name', 'value']


@admin.register(ItemProperty)
class ItemPropertyAdmin(admin.ModelAdmin):
    list_display = ['item', 'property_type', 'get_value', 'created_at']
    list_filter = ['property_type', 'property_type__data_type', 'item__company']
    search_fields = ['item__name', 'item__code', 'property_type__name', 'text_value']
    ordering = ['item__name', 'property_type__name']
    
    def get_value(self, obj):
        return obj.get_value()
    get_value.short_description = 'Value'


@admin.register(OrderCounter)
class OrderCounterAdmin(admin.ModelAdmin):
    list_display = ['company', 'order_type', 'current_number', 'created_at']
    list_filter = ['order_type', 'company']
    search_fields = ['company__name', 'order_type']
    readonly_fields = ['created_at', 'updated_at']


admin.site.register(Country)
admin.site.register(ItemGroup)
admin.site.register(ItemPrice)
admin.site.register(ThirdParty)
