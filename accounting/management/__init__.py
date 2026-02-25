"""
Management command: create_demo_third_parties

Creates 10 demo third party records for each existing company.

Usage:
    python manage.py create_demo_third_parties
    python manage.py create_demo_third_parties --per-company 15  # Create 15 per company
"""

import random
from django.core.management.base import BaseCommand
from django.db import transaction

from accounting.models import ThirdParty, Country
from core.models import Company
from reference_tables.models import (
    DocumentType, 
    ColombianCity, 
    ColombianDepartment, 
    DianEconomicActivity
)


class Command(BaseCommand):
    help = 'Create demo third party records for each existing company.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--per-company',
            type=int,
            default=10,
            help='Number of third parties to create per company (default: 10)',
        )
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Delete all existing third parties before creating new ones',
        )

    def handle(self, *args, **options):
        per_company = options['per_company']
        
        if options['clear']:
            deleted_count = ThirdParty.objects.count()
            ThirdParty.objects.all().delete()
            self.stdout.write(self.style.WARNING(f'Deleted {deleted_count} existing third parties.'))

        companies = Company.objects.all()
        if not companies.exists():
            self.stdout.write(
                self.style.ERROR('No companies found. Please create companies first using "python manage.py create_demo_companies".')
            )
            return

        total_created = 0
        for company in companies:
            created_count = self._create_third_parties_for_company(company, per_company)
            total_created += created_count
            self.stdout.write(f'Created {created_count} third parties for {company.legal_name or company.company_name}')

        self.stdout.write(
            self.style.SUCCESS(f'Successfully created {total_created} demo third parties across {companies.count()} companies.')
        )

    def _create_third_parties_for_company(self, company, count):
        """Create third party records for a single company."""
        # Get reference data
        try:
            cedula_doc_type = DocumentType.objects.get(code=13)  # Cédula de ciudadanía
            nit_doc_type = DocumentType.objects.get(code=31)  # NIT
            colombia = Country.objects.get(code=169)  # Colombia
            
            # Get a random Colombian city and its department
            cities = ColombianCity.objects.select_related('colombian_department').all()
            if not cities.exists():
                raise Exception("No Colombian cities found")
            
            economic_activities = DianEconomicActivity.objects.all()
            
        except Exception as e:
            raise Exception(
                f"Missing reference data. Please run 'python manage.py load_seeds' first. Error: {e}"
            )

        # Third party types to cycle through
        third_party_types = [
            ThirdParty.SUPPLIER,
            ThirdParty.CLIENT, 
            ThirdParty.EMPLOYEE,
            ThirdParty.PUBLIC_TYPE,
        ]

        # Demo data templates
        supplier_templates = [
            {
                'legal_name': 'Proveedores Andinos S.A.S.',
                'company_name': 'Andinos Supply',
                'email': 'ventas@andinos.co',
            },
            {
                'legal_name': 'Distribuidora Nacional LTDA',
                'company_name': 'DisNacional',
                'email': 'comercial@disnacional.com',
            },
            {
                'legal_name': 'Importaciones del Valle S.A.',
                'company_name': 'Valle Import',
                'email': 'info@valleimport.co',
            },
        ]

        client_templates = [
            {
                'legal_name': 'Comercializadora del Norte S.A.S.',
                'company_name': 'Norte Commerce',
                'email': 'compras@nortecommerce.co',
            },
            {
                'legal_name': 'Retail Solutions LTDA',
                'company_name': 'RetailSol',
                'email': 'pedidos@retailsol.com',
            },
        ]

        employee_templates = [
            {
                'first_name': 'Carlos',
                'middle_name': 'Andrés',
                'first_lastname': 'Rodríguez',
                'second_last_name': 'García',
                'email': 'carlos.rodriguez@company.co',
            },
            {
                'first_name': 'María',
                'middle_name': 'Elena',
                'first_lastname': 'González',
                'second_last_name': 'López',
                'email': 'maria.gonzalez@company.co',
            },
            {
                'first_name': 'Luis',
                'middle_name': 'Fernando',
                'first_lastname': 'Martínez',
                'second_last_name': 'Hernández',
                'email': 'luis.martinez@company.co',
            },
            {
                'first_name': 'Ana',
                'middle_name': 'Sofía',
                'first_lastname': 'Jiménez',
                'second_last_name': 'Ruiz',
                'email': 'ana.jimenez@company.co',
            },
        ]

        public_templates = [
            {
                'legal_name': 'Alcaldía de Medellín',
                'company_name': 'Municipio de Medellín',
                'email': 'contacto@medellin.gov.co',
            },
            {
                'legal_name': 'DIAN - Dirección de Impuestos',
                'company_name': 'DIAN',
                'email': 'info@dian.gov.co',
            },
        ]

        neighborhoods = [
            'Centro', 'Zona Rosa', 'El Poblado', 'Laureles', 'Envigado', 'Sabaneta',
            'Chapinero', 'La Candelaria', 'Usaquén', 'Suba', 'Engativá', 'Fontibón',
            'El Chicó', 'La Macarena', 'Teusaquillo', 'Barrios Unidos'
        ]

        with transaction.atomic():
            created_third_parties = []
            
            # Get highest existing document number to avoid duplicates
            existing_max = ThirdParty.objects.aggregate(
                max_doc=models.Max('document_number')
            )['max_doc'] or 10000000

            for i in range(count):
                # Cycle through third party types
                tp_type = third_party_types[i % len(third_party_types)]
                
                # Get a random city
                city = random.choice(cities)
                
                # Base third party data
                tp_data = {
                    'company': company,
                    'country': colombia,
                    'colombian_city': city,
                    'colombian_department': city.colombian_department,
                    'third_party_type': tp_type,
                    'neighborhood': random.choice(neighborhoods),
                    'phone': f'+57 {random.randint(300, 350)} {random.randint(1000000, 9999999)}',
                    'address': f'Calle {random.randint(10, 150)} # {random.randint(10, 99)}-{random.randint(10, 99)}',
                }

                # Add economic activity (optional)
                if economic_activities.exists():
                    tp_data['dian_economic_activity'] = random.choice(economic_activities)

                # Type-specific data
                if tp_type == ThirdParty.SUPPLIER:
                    template = random.choice(supplier_templates)
                    tp_data.update({
                        'document_type': nit_doc_type,
                        'document_number': existing_max + (i * 1000) + random.randint(1, 999),
                        'legal_name': f"{template['legal_name']} {i+1}",
                        'company_name': f"{template['company_name']} {i+1}",
                        'email': template['email'].replace('@', f'{i+1}@'),
                    })
                    
                elif tp_type == ThirdParty.CLIENT:
                    template = random.choice(client_templates)
                    tp_data.update({
                        'document_type': nit_doc_type,
                        'document_number': existing_max + (i * 1000) + random.randint(1, 999),
                        'legal_name': f"{template['legal_name']} {i+1}",
                        'company_name': f"{template['company_name']} {i+1}",
                        'email': template['email'].replace('@', f'{i+1}@'),
                    })
                    
                elif tp_type == ThirdParty.EMPLOYEE:
                    template = random.choice(employee_templates)
                    tp_data.update({
                        'document_type': cedula_doc_type,
                        'document_number': existing_max + (i * 100) + random.randint(10000, 99999),
                        'first_name': template['first_name'],
                        'middle_name': template.get('middle_name'),
                        'first_lastname': template['first_lastname'],
                        'second_last_name': template.get('second_last_name'),
                        'email': template['email'].replace('company.co', f'{company.id}company.co'),
                    })
                    
                elif tp_type == ThirdParty.PUBLIC_TYPE:
                    template = random.choice(public_templates)
                    tp_data.update({
                        'document_type': nit_doc_type,
                        'document_number': existing_max + (i * 1000) + random.randint(1, 999),
                        'legal_name': f"{template['legal_name']} {i+1}",
                        'company_name': f"{template['company_name']} {i+1}",
                        'email': template['email'],
                    })

                # Create the third party
                third_party = ThirdParty.objects.create(**tp_data)
                created_third_parties.append(third_party)

        return len(created_third_parties)