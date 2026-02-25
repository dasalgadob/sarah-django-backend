"""
Management command: create_demo_item_prices

Creates demo item and item price records for each existing company.

Usage:
    python manage.py create_demo_item_prices
    python manage.py create_demo_item_prices --per-company 15
"""

import random
from decimal import Decimal
from django.core.management.base import BaseCommand
from django.db import transaction, models

from accounting.models import Item, ItemPrice, ItemGroup
from core.models import Company
from reference_tables.models import (
    UnitMeasure,
    IvaType,
    IvaRate,
    ExciseTaxType,
    ExciseTaxRate,
)


class Command(BaseCommand):
    help = 'Create demo item and item price records for each existing company.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--per-company',
            type=int,
            default=10,
            help='Number of item prices to create per company (default: 10)',
        )
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Delete all existing items and item prices before creating new ones',
        )

    def handle(self, *args, **options):
        per_company = options['per_company']
        
        if options['clear']:
            item_price_count = ItemPrice.objects.count()
            item_count = Item.objects.count()
            ItemPrice.objects.all().delete()
            Item.objects.all().delete()
            self.stdout.write(self.style.WARNING(
                f'Deleted {item_price_count} item prices and {item_count} items.'
            ))

        companies = Company.objects.all()
        if not companies.exists():
            self.stdout.write(
                self.style.ERROR('No companies found. Please create companies first using "python manage.py create_demo_companies".')
            )
            return

        total_created = 0
        for company in companies:
            created_count = self._create_item_prices_for_company(company, per_company)
            total_created += created_count
            self.stdout.write(f'Created {created_count} item prices for {company.legal_name or company.company_name}')

        self.stdout.write(
            self.style.SUCCESS(f'Successfully created {total_created} demo item prices across {companies.count()} companies.')
        )

    def _create_item_prices_for_company(self, company, count):
        """Create item price records for a single company."""
        # Get reference data
        try:
            item_groups = list(ItemGroup.objects.all())
            unit_measures = list(UnitMeasure.objects.all())
            iva_types = list(IvaType.objects.all())
            iva_rates = list(IvaRate.objects.all())
            excise_tax_types = list(ExciseTaxType.objects.all())
            excise_tax_rates = list(ExciseTaxRate.objects.all())
            
            if not all([item_groups, unit_measures]):
                raise Exception("Missing item groups or unit measures")
            
        except Exception as e:
            raise Exception(
                f"Missing reference data. Please run 'python manage.py load_seeds' first. Error: {e}"
            )

        # Demo item templates
        item_templates = [
            {
                'name': 'Computador Portátil',
                'category': 'Tecnología',
                'base_price': 2500000,
            },
            {
                'name': 'Escritorio Ejecutivo',
                'category': 'Muebles',
                'base_price': 850000,
            },
            {
                'name': 'Impresora Láser',
                'category': 'Tecnología',
                'base_price': 450000,
            },
            {
                'name': 'Silla Ergonómica',
                'category': 'Muebles',
                'base_price': 320000,
            },
            {
                'name': 'Teléfono IP',
                'category': 'Telecomunicaciones',
                'base_price': 180000,
            },
            {
                'name': 'Proyector HD',
                'category': 'Audiovisual',
                'base_price': 1200000,
            },
            {
                'name': 'Mesa de Reuniones',
                'category': 'Muebles',
                'base_price': 950000,
            },
            {
                'name': 'Monitor 24 pulgadas',
                'category': 'Tecnología',
                'base_price': 380000,
            },
            {
                'name': 'Sistema de Audio',
                'category': 'Audiovisual',
                'base_price': 750000,
            },
            {
                'name': 'Archivador Metálico',
                'category': 'Oficina',
                'base_price': 280000,
            },
        ]

        with transaction.atomic():
            created_count = 0
            
            for i in range(count):
                # Select item template
                template = item_templates[i % len(item_templates)]
                
                # Create item first
                item_code = f"ITEM-{company.id:03d}-{i+1:03d}"
                
                item = Item.objects.create(
                    code=item_code,
                    name=f"{template['name']} {i+1}",
                    item_group=random.choice(item_groups),
                    unit_measure=random.choice(unit_measures),
                    company=company,
                    iva_type=random.choice(iva_types) if iva_types else None,
                    iva_rate=random.choice(iva_rates) if iva_rates else None,
                    excise_tax_type=random.choice(excise_tax_types) if excise_tax_types else None,
                    excise_tax_rate=random.choice(excise_tax_rates) if excise_tax_rates else None,
                )

                # Create both buying and selling prices for each item
                price_types = [ItemPrice.BUYING, ItemPrice.SELLING]
                
                for price_type in price_types:
                    created_count += 1
                    
                    # Calculate prices based on type
                    base_price = Decimal(str(template['base_price']))
                    
                    if price_type == ItemPrice.BUYING:
                        # Buying price is typically lower
                        price = base_price * Decimal(str(random.uniform(0.7, 0.9)))
                    else:
                        # Selling price is typically higher
                        price = base_price * Decimal(str(random.uniform(1.1, 1.4)))
                    
                    # Calculate IVA (19% typical in Colombia)
                    iva_percentage = Decimal('0.19')
                    iva_amount = price * iva_percentage
                    
                    # Calculate excise tax (random between 0-5%)
                    excise_percentage = Decimal(str(random.uniform(0, 0.05)))
                    excise_amount = price * excise_percentage
                    
                    # Calculate total
                    total = price + iva_amount + excise_amount
                    
                    # Create item price
                    ItemPrice.objects.create(
                        price=price.quantize(Decimal('0.01')),
                        iva=iva_amount.quantize(Decimal('0.01')),
                        excise_tax=excise_amount.quantize(Decimal('0.01')),
                        total=total.quantize(Decimal('0.01')),
                        item_price_type=price_type,
                        item=item,
                        company=company,
                    )

        return created_count