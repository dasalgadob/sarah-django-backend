"""
Management command: load_seeds

Populates the database with reference / seed data that mirrors
the original Rails db/seeds setup.

Usage:
    python manage.py load_seeds
"""

import csv
import os
from pathlib import Path

from django.core.management.base import BaseCommand

# The CSV files live inside django_app/fixtures/ (copies of db/seeds/).
FIXTURES_DIR = Path(__file__).resolve().parent.parent.parent.parent / 'fixtures'


class Command(BaseCommand):
    help = 'Load seed data from CSV files into the database.'

    def handle(self, *args, **options):
        self._load_document_types()
        self._load_countries()
        self._load_colombian_departments()
        self._load_colombian_cities()
        self._load_dian_economic_activities()
        self._load_item_groups()
        self._load_unit_measures()
        self._load_iva_types_and_rates()
        self._load_excise_tax_types_and_rates()
        self.stdout.write(self.style.SUCCESS('Seed data loaded successfully.'))

    # ------------------------------------------------------------------
    # Loaders
    # ------------------------------------------------------------------

    def _load_document_types(self):
        from reference_tables.models import DocumentType
        DocumentType.objects.all().delete()
        path = FIXTURES_DIR / 'document_types.csv'
        with open(path, newline='', encoding='utf-8') as f:
            reader = csv.reader(f, delimiter=';')
            next(reader)  # skip header
            for row in reader:
                if len(row) >= 2 and row[0].strip():  # skip empty rows
                    DocumentType.objects.create(code=int(row[0]), name=row[1])
        self.stdout.write('  DocumentType: loaded')

    def _load_countries(self):
        from accounting.models import Country
        Country.objects.all().delete()
        path = FIXTURES_DIR / 'countries.csv'
        with open(path, newline='', encoding='utf-8') as f:
            reader = csv.reader(f, delimiter=';')
            next(reader)
            for row in reader:
                if len(row) >= 2 and row[0].strip():  # skip empty rows
                    Country.objects.create(code=int(row[0]), name=row[1])
        self.stdout.write('  Country: loaded')

    def _load_colombian_departments(self):
        from reference_tables.models import ColombianDepartment
        ColombianDepartment.objects.all().delete()
        path = FIXTURES_DIR / 'colombian_departments.csv'
        with open(path, newline='', encoding='utf-8') as f:
            reader = csv.reader(f, delimiter=';')
            next(reader)
            for row in reader:
                if len(row) >= 2 and row[0].strip():  # skip empty rows
                    ColombianDepartment.objects.create(code=row[0], name=row[1])
        self.stdout.write('  ColombianDepartment: loaded')

    def _load_colombian_cities(self):
        from reference_tables.models import ColombianCity, ColombianDepartment
        ColombianCity.objects.all().delete()
        path = FIXTURES_DIR / 'colombian_cities.csv'
        with open(path, newline='', encoding='utf-8') as f:
            reader = csv.reader(f, delimiter=',')
            next(reader)
            for row in reader:
                if len(row) >= 2 and row[0].strip():  # skip empty rows
                    dept_code = row[0][:2]
                    dept = ColombianDepartment.objects.filter(code=dept_code).first()
                    if dept:
                        ColombianCity.objects.create(
                            code=row[0], name=row[1], colombian_department=dept
                        )
        self.stdout.write('  ColombianCity: loaded')

    def _load_dian_economic_activities(self):
        from reference_tables.models import DianEconomicActivity
        DianEconomicActivity.objects.all().delete()
        path = FIXTURES_DIR / 'dian_economic_activities.csv'
        with open(path, newline='', encoding='utf-8') as f:
            reader = csv.reader(f, delimiter=',')
            next(reader)
            for row in reader:
                if len(row) >= 2 and row[0].strip():  # skip empty rows
                    DianEconomicActivity.objects.create(code=row[0], name=row[1])
        self.stdout.write('  DianEconomicActivity: loaded')

    def _load_item_groups(self):
        from accounting.models import ItemGroup
        ItemGroup.objects.all().delete()
        for name in ('Consumibles', 'Productos', 'Materia Prima', 'Servicios'):
            ItemGroup.objects.create(name=name)
        self.stdout.write('  ItemGroup: loaded')

    def _load_unit_measures(self):
        from reference_tables.models import UnitMeasure
        UnitMeasure.objects.all().delete()
        path = FIXTURES_DIR / 'unit_measures.csv'
        with open(path, newline='', encoding='utf-8') as f:
            reader = csv.reader(f, delimiter=';')
            next(reader)
            for row in reader:
                if len(row) >= 2 and row[0].strip():  # skip empty rows
                    UnitMeasure.objects.create(abbreviation=row[0], name=row[1])
        self.stdout.write('  UnitMeasure: loaded')

    def _load_iva_types_and_rates(self):
        from reference_tables.models import IvaType, IvaRate
        IvaRate.objects.all().delete()
        IvaType.objects.all().delete()
        gravado = IvaType.objects.create(name='Gravado')
        exento = IvaType.objects.create(name='Exento')
        IvaType.objects.create(name='Excluido')
        IvaType.objects.create(name='No gravado')
        IvaRate.objects.create(value='19.00', iva_type=gravado)
        IvaRate.objects.create(value='5.00', iva_type=gravado)
        IvaRate.objects.create(value='0.00', iva_type=exento)
        self.stdout.write('  IvaType / IvaRate: loaded')

    def _load_excise_tax_types_and_rates(self):
        from reference_tables.models import ExciseTaxType, ExciseTaxRate
        ExciseTaxRate.objects.all().delete()
        ExciseTaxType.objects.all().delete()
        gravado = ExciseTaxType.objects.create(name='Gravado')
        ExciseTaxType.objects.create(name='No gravado')
        for value in ('4', '8', '16'):
            ExciseTaxRate.objects.create(value=value, excise_tax_type=gravado)
        self.stdout.write('  ExciseTaxType / ExciseTaxRate: loaded')
