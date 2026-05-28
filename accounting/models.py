"""
Accounting app models.

Contains: Country, ItemGroup, Item, ItemPrice, ThirdParty, Order, OrderCounter.
"""

from django.db import models, transaction
from safedelete.models import SafeDeleteModel, SOFT_DELETE_CASCADE
from simple_history.models import HistoricalRecords


class Country(SafeDeleteModel):
    _safedelete_policy = SOFT_DELETE_CASCADE

    code = models.IntegerField(unique=True)
    name = models.CharField(max_length=255, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    history = HistoricalRecords()

    class Meta:
        db_table = 'countries'

    def __str__(self):
        return self.name


class ItemGroup(SafeDeleteModel):
    _safedelete_policy = SOFT_DELETE_CASCADE

    name = models.CharField(max_length=255, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    history = HistoricalRecords()

    class Meta:
        db_table = 'item_groups'

    def __str__(self):
        return self.name


class Item(SafeDeleteModel):
    _safedelete_policy = SOFT_DELETE_CASCADE

    # Base product information
    base_code = models.CharField(max_length=50, default='DEFAULT')
    variant_code = models.CharField(max_length=50, null=True, blank=True)
    code = models.CharField(max_length=100)
    name = models.CharField(max_length=255)
    base_name = models.CharField(max_length=255, default='Default Item')
    
    item_group = models.ForeignKey(
        ItemGroup,
        on_delete=models.PROTECT,
        related_name='items',
    )
    unit_measure = models.ForeignKey(
        'reference_tables.UnitMeasure',
        on_delete=models.PROTECT,
        related_name='items',
    )
    company = models.ForeignKey(
        'core.Company',
        on_delete=models.PROTECT,
        related_name='items',
    )
    
    # Variant information
    is_variant = models.BooleanField(default=False)
    parent_item = models.ForeignKey(
        'self', 
        on_delete=models.CASCADE, 
        null=True, 
        blank=True, 
        related_name='variants'
    )
    
    # Material/variant specific fields
    material = models.CharField(max_length=100, null=True, blank=True)
    color = models.CharField(max_length=50, null=True, blank=True)
    size = models.CharField(max_length=50, null=True, blank=True)
    iva_type = models.ForeignKey(
        'reference_tables.IvaType',
        on_delete=models.PROTECT,
        related_name='items',
        null=True,
        blank=True,
    )
    iva_rate = models.ForeignKey(
        'reference_tables.IvaRate',
        on_delete=models.PROTECT,
        related_name='items',
        null=True,
        blank=True,
    )
    excise_tax_type = models.ForeignKey(
        'reference_tables.ExciseTaxType',
        on_delete=models.PROTECT,
        related_name='items',
        null=True,
        blank=True,
    )
    excise_tax_rate = models.ForeignKey(
        'reference_tables.ExciseTaxRate',
        on_delete=models.PROTECT,
        related_name='items',
        null=True,
        blank=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    history = HistoricalRecords()

    class Meta:
        db_table = 'items'
        unique_together = [('company', 'code')]

    def save(self, *args, **kwargs):
        # Auto-generate combined code
        if self.variant_code:
            self.code = f"{self.base_code}-{self.variant_code}"
            self.is_variant = True
        else:
            self.code = self.base_code
        super().save(*args, **kwargs)

    def __str__(self):
        return f'{self.code} - {self.name}'


class ItemPrice(SafeDeleteModel):
    _safedelete_policy = SOFT_DELETE_CASCADE

    BUYING = 'buying'
    SELLING = 'selling'
    PRICE_TYPE_CHOICES = [
        (BUYING, 'Buying'),
        (SELLING, 'Selling'),
    ]

    price = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    iva = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    excise_tax = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    total = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    item_price_type = models.CharField(
        max_length=20, choices=PRICE_TYPE_CHOICES, null=True, blank=True
    )
    item = models.ForeignKey(
        Item,
        on_delete=models.PROTECT,
        related_name='prices',
    )
    company = models.ForeignKey(
        'core.Company',
        on_delete=models.CASCADE,
        related_name='item_prices',
        null=True,
        blank=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    history = HistoricalRecords()

    class Meta:
        db_table = 'item_prices'

    def __str__(self):
        return f'ItemPrice #{self.pk} for {self.item}'


class ThirdParty(SafeDeleteModel):
    _safedelete_policy = SOFT_DELETE_CASCADE

    SUPPLIER = 'supplier'
    CLIENT = 'client'
    EMPLOYEE = 'employee'
    PUBLIC_TYPE = 'public_type'
    THIRD_PARTY_TYPE_CHOICES = [
        (SUPPLIER, 'Supplier'),
        (CLIENT, 'Client'),
        (EMPLOYEE, 'Employee'),
        (PUBLIC_TYPE, 'Public Type'),
    ]

    document_type = models.ForeignKey(
        'reference_tables.DocumentType',
        on_delete=models.PROTECT,
        related_name='third_parties',
    )
    document_number = models.BigIntegerField(null=True, blank=True)
    email = models.EmailField(null=True, blank=True)
    address = models.CharField(max_length=255, null=True, blank=True)
    neighborhood = models.CharField(max_length=255)
    third_party_type = models.CharField(max_length=20, choices=THIRD_PARTY_TYPE_CHOICES)
    company = models.ForeignKey(
        'core.Company',
        on_delete=models.PROTECT,
        related_name='third_parties',
    )
    phone = models.CharField(max_length=50, null=True, blank=True)
    country = models.ForeignKey(
        Country,
        on_delete=models.PROTECT,
        related_name='third_parties',
    )
    colombian_city = models.ForeignKey(
        'reference_tables.ColombianCity',
        on_delete=models.PROTECT,
        related_name='third_parties',
    )
    colombian_department = models.ForeignKey(
        'reference_tables.ColombianDepartment',
        on_delete=models.PROTECT,
        related_name='third_parties',
    )
    dian_economic_activity = models.ForeignKey(
        'reference_tables.DianEconomicActivity',
        on_delete=models.PROTECT,
        related_name='third_parties',
        null=True,
        blank=True,
    )
    legal_name = models.CharField(max_length=255, null=True, blank=True)
    company_name = models.CharField(max_length=255, null=True, blank=True)
    first_name = models.CharField(max_length=255, null=True, blank=True)
    middle_name = models.CharField(max_length=255, null=True, blank=True)
    first_lastname = models.CharField(max_length=255, null=True, blank=True)
    second_last_name = models.CharField(max_length=255, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    history = HistoricalRecords()

    class Meta:
        db_table = 'third_parties'

    def __str__(self):
        return (
            self.legal_name
            or self.company_name
            or f'{self.first_name} {self.first_lastname}'
            or str(self.document_number)
        )


class OrderCounter(SafeDeleteModel):
    """Counter for generating sequential order numbers"""
    _safedelete_policy = SOFT_DELETE_CASCADE

    company = models.ForeignKey('core.Company', on_delete=models.CASCADE)
    order_type = models.CharField(max_length=20)
    current_number = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    history = HistoricalRecords()
    
    class Meta:
        db_table = 'order_counters'
        unique_together = [('company', 'order_type')]
    
    @classmethod
    def get_next_number(cls, company, order_type):
        """Thread-safe method to get next sequential number"""
        with transaction.atomic():
            counter, created = cls.objects.select_for_update().get_or_create(
                company=company,
                order_type=order_type,
                defaults={'current_number': 0}
            )
            counter.current_number += 1
            counter.save()
            return counter.current_number
    
    def __str__(self):
        return f'{self.company} - {self.order_type}: {self.current_number}'


class Order(SafeDeleteModel):
    _safedelete_policy = SOFT_DELETE_CASCADE

    ORDER_TYPE_CHOICES = [
        ('purchase', 'Purchase Order'),
        ('sale', 'Sale Order'),
        ('quote', 'Quote'),
    ]
    
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('confirmed', 'Confirmed'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]

    order_number = models.CharField(max_length=50, unique=True, blank=True)
    order_type = models.CharField(max_length=20, choices=ORDER_TYPE_CHOICES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    order_date = models.DateTimeField(auto_now_add=True)
    delivery_date = models.DateTimeField(null=True, blank=True)
    
    # Relationships
    company = models.ForeignKey(
        'core.Company',
        on_delete=models.PROTECT,
        related_name='orders'
    )
    third_party = models.ForeignKey(
        ThirdParty,
        on_delete=models.PROTECT,
        related_name='orders'
    )
    sale_type = models.ForeignKey(
        'reference_tables.SaleTypeOrder',
        on_delete=models.PROTECT,
        related_name='orders'
    )
    payment_method = models.ForeignKey(
        'reference_tables.PaymentMethodOrder',
        on_delete=models.PROTECT,
        related_name='orders'
    )
    
    # Totals
    subtotal = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    total_iva = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    total_excise_tax = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    total_amount = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    
    # Additional fields
    notes = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    history = HistoricalRecords()

    class Meta:
        db_table = 'orders'
        
    def save(self, *args, **kwargs):
        if not self.order_number:
            # Generate sequential order number
            next_number = OrderCounter.get_next_number(self.company, self.order_type)
            prefix = self.order_type.upper()[:4]
            self.order_number = f"{prefix}-{self.company.id:03d}-{next_number:06d}"
            
        super().save(*args, **kwargs)
        
    def __str__(self):
        return f'{self.order_number} - {self.third_party}'


class OrderItem(SafeDeleteModel):
    _safedelete_policy = SOFT_DELETE_CASCADE

    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name='order_items'
    )
    item_price = models.ForeignKey(
        ItemPrice,
        on_delete=models.PROTECT,
        related_name='order_items'
    )
    
    # Quantity and pricing
    quantity = models.DecimalField(max_digits=10, decimal_places=2)
    unit_price = models.DecimalField(max_digits=15, decimal_places=2)
    line_total = models.DecimalField(max_digits=15, decimal_places=2)
    
    # Item properties (JSON field for flexibility)
    item_properties = models.JSONField(
        null=True, 
        blank=True, 
        help_text="Item-specific properties like color, size, etc."
    )
    
    # Line-level taxes
    line_iva = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    line_excise_tax = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    line_total_with_taxes = models.DecimalField(max_digits=15, decimal_places=2)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    history = HistoricalRecords()

    class Meta:
        db_table = 'order_items'
        
    def save(self, *args, **kwargs):
        # Calculate line total if not already set
        if not self.line_total:
            self.line_total = self.quantity * self.unit_price
        
        # Calculate taxes based on item_price tax rates if not already set
        if self.line_iva == 0 and self.item_price.iva:
            self.line_iva = (self.line_total * self.item_price.iva) / 100
        if self.line_excise_tax == 0 and self.item_price.excise_tax:
            self.line_excise_tax = (self.line_total * self.item_price.excise_tax) / 100
        
        # Calculate final total if not already set  
        if not self.line_total_with_taxes:
            self.line_total_with_taxes = self.line_total + self.line_iva + self.line_excise_tax
        
        super().save(*args, **kwargs)
        
    def __str__(self):
        return f'{self.order.order_number} - {self.item_price.item}'


class ItemPropertyDataType(SafeDeleteModel):
    """Data types available for item properties (text, number, choice, etc.)"""
    _safedelete_policy = SOFT_DELETE_CASCADE

    code = models.CharField(max_length=20, unique=True)  # internal identifier used in logic
    name = models.CharField(max_length=100)              # English display name
    name_es = models.CharField(max_length=100)           # Spanish display name
    history = HistoricalRecords()

    class Meta:
        db_table = 'item_property_data_types'
        ordering = ['name']

    def __str__(self):
        return self.name


class ItemPropertyType(SafeDeleteModel):
    """Define types of properties that items can have (color, brand, size, etc.)"""
    _safedelete_policy = SOFT_DELETE_CASCADE

    name = models.CharField(max_length=100)
    data_type = models.ForeignKey(
        ItemPropertyDataType,
        on_delete=models.PROTECT,
        related_name='property_types',
        null=True,
        blank=True,
    )
    is_required = models.BooleanField(default=False)
    company = models.ForeignKey(
        'core.Company',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='item_property_types'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    history = HistoricalRecords()

    class Meta:
        db_table = 'item_property_types'
        unique_together = [('name', 'company')]
        
    def __str__(self):
        return self.name


class ItemPropertyValue(SafeDeleteModel):
    """Possible values for choice-based properties"""
    _safedelete_policy = SOFT_DELETE_CASCADE

    property_type = models.ForeignKey(
        ItemPropertyType,
        on_delete=models.CASCADE,
        related_name='possible_values'
    )
    value = models.CharField(max_length=255)
    company = models.ForeignKey(
        'core.Company',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='item_property_values'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    history = HistoricalRecords()

    class Meta:
        db_table = 'item_property_values'
        unique_together = [('property_type', 'value', 'company')]
        
    def __str__(self):
        return f'{self.property_type.name}: {self.value}'


class ItemProperty(SafeDeleteModel):
    """Actual property values assigned to items"""
    _safedelete_policy = SOFT_DELETE_CASCADE

    item = models.ForeignKey(
        Item,
        on_delete=models.CASCADE,
        related_name='properties'
    )
    property_type = models.ForeignKey(
        ItemPropertyType,
        on_delete=models.CASCADE
    )
    
    # Different value fields for different data types
    text_value = models.CharField(max_length=255, null=True, blank=True)
    number_value = models.IntegerField(null=True, blank=True)
    decimal_value = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    boolean_value = models.BooleanField(null=True, blank=True)
    date_value = models.DateField(null=True, blank=True)
    choice_value = models.ForeignKey(
        ItemPropertyValue,
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    history = HistoricalRecords()

    class Meta:
        db_table = 'item_properties'
        unique_together = [('item', 'property_type')]
        
    def get_value(self):
        """Return the actual value based on property type"""
        code = self.property_type.data_type.code if self.property_type.data_type else None
        if code == 'text':
            return self.text_value
        elif code == 'number':
            return self.number_value
        elif code == 'decimal':
            return self.decimal_value
        elif code == 'boolean':
            return self.boolean_value
        elif code == 'date':
            return self.date_value
        elif code in ['choice', 'multiple_choice']:
            return self.choice_value.value if self.choice_value else None
        return None
        
    def __str__(self):
        return f'{self.item} - {self.property_type.name}: {self.get_value()}'
