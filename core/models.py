"""
Core app models.

Manages users (via Django's built-in User), roles and companies.
"""

from django.db import models
from django.contrib.auth.models import User
from safedelete.models import SafeDeleteModel, SOFT_DELETE_CASCADE
from simple_history.models import HistoricalRecords


class Role(SafeDeleteModel):
    """Application role that can be assigned to users."""
    _safedelete_policy = SOFT_DELETE_CASCADE

    name = models.CharField(max_length=100, unique=True)
    users = models.ManyToManyField(User, related_name='roles', blank=True)
    history = HistoricalRecords()

    class Meta:
        db_table = 'roles'

    def __str__(self):
        return self.name


class Company(SafeDeleteModel):
    """Colombian company / taxpayer registered in the system."""
    _safedelete_policy = SOFT_DELETE_CASCADE

    document_type = models.ForeignKey(
        'reference_tables.DocumentType',
        on_delete=models.PROTECT,
        related_name='companies',
    )
    document_number = models.BigIntegerField()
    dv = models.IntegerField(null=True, blank=True)
    legal_name = models.CharField(max_length=255, null=True, blank=True)
    company_name = models.CharField(max_length=255, null=True, blank=True)
    first_name = models.CharField(max_length=255, null=True, blank=True)
    middle_name = models.CharField(max_length=255, null=True, blank=True)
    first_lastname = models.CharField(max_length=255, null=True, blank=True)
    second_last_name = models.CharField(max_length=255, null=True, blank=True)
    country = models.ForeignKey(
        'accounting.Country',
        on_delete=models.PROTECT,
        related_name='companies',
    )
    colombian_city = models.ForeignKey(
        'reference_tables.ColombianCity',
        on_delete=models.PROTECT,
        related_name='companies',
    )
    colombian_department = models.ForeignKey(
        'reference_tables.ColombianDepartment',
        on_delete=models.PROTECT,
        related_name='companies',
    )
    main_address = models.CharField(max_length=255, null=True, blank=True)
    email = models.EmailField(null=True, blank=True)
    phone = models.CharField(max_length=50, null=True, blank=True)
    dian_economic_activity = models.ForeignKey(
        'reference_tables.DianEconomicActivity',
        on_delete=models.PROTECT,
        related_name='companies',
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    history = HistoricalRecords()

    class Meta:
        db_table = 'companies'
        unique_together = [('document_type', 'document_number')]

    def __str__(self):
        return self.legal_name or self.company_name or str(self.document_number)
