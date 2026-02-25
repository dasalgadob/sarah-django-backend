"""
Management command: create_demo_companies

Creates 10 demo company records for testing and development.

Usage:
    python manage.py create_demo_companies
    python manage.py create_demo_companies --count 20  # Create 20 companies instead
"""

from django.core.management.base import BaseCommand
from django.db import transaction
from django.db import models

from core.models import Company
from reference_tables.models import DocumentType, ColombianCity, ColombianDepartment, DianEconomicActivity
from accounting.models import Country


class Command(BaseCommand):
    help = 'Create demo company records for testing and development.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--count',
            type=int,
            default=10,
            help='Number of demo companies to create (default: 10)',
        )
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Delete all existing companies before creating new ones',
        )

    def handle(self, *args, **options):
        count = options['count']
        
        if options['clear']:
            deleted_count = Company.objects.count()
            Company.objects.all().delete()
            self.stdout.write(self.style.WARNING(f'Deleted {deleted_count} existing companies.'))

        # Get the highest existing document number to avoid duplicates
        existing_max = Company.objects.aggregate(
            max_doc=models.Max('document_number')
        )['max_doc'] or 8000000000

        with transaction.atomic():
            created_companies = []
            for i in range(count):
                company = self._create_demo_company(i + 1, existing_max)
                created_companies.append(company)
                self.stdout.write(f'Created: {company.legal_name or company.company_name}')

        self.stdout.write(
            self.style.SUCCESS(f'Successfully created {len(created_companies)} demo companies.')
        )

    def _create_demo_company(self, index, existing_max_doc_number):
        """Create a single demo company with realistic Colombian data."""
        # Get reference data (ensure the seeds have been loaded)
        try:
            nit_document_type = DocumentType.objects.get(code=31)  # NIT
            colombia = Country.objects.get(code=169)  # Colombia
            bogota_department = ColombianDepartment.objects.filter(name__icontains='Bogot').first()
            bogota_city = ColombianCity.objects.filter(
                colombian_department=bogota_department,
                name__icontains='Bogot'
            ).first()
            economic_activity = DianEconomicActivity.objects.first()
        except Exception as e:
            raise Exception(
                f"Missing reference data. Please run 'python manage.py load_seeds' first. Error: {e}"
            )

        # Generate unique document numbers starting after existing ones
        base_doc_number = existing_max_doc_number + index * 100

        # Demo company data with realistic Colombian companies
        demo_companies = [
            {
                'document_number': base_doc_number + 1,
                'dv': 7,
                'legal_name': f'Empresa Colombiana Demo {index} S.A.S.',
                'company_name': f'Demo Company {index}',
                'main_address': f'Calle {50 + index} # {10 + index}-{20 + index*2}',
                'email': f'contacto@democompany{index}.com.co',
                'phone': f'+57 1 {300 + index}{400 + index:04d}',
            },
            {
                'document_number': base_doc_number + 2,
                'dv': 3,
                'legal_name': f'Inversiones Demo {index} LTDA',
                'company_name': f'Demo Investments {index}',
                'main_address': f'Carrera {30 + index} # {40 + index}-{50 + index*3}',
                'email': f'info@demoinvest{index}.co',
                'phone': f'+57 1 {320 + index}{500 + index:04d}',
            },
            {
                'document_number': base_doc_number + 3,
                'dv': 1,
                'legal_name': f'Comercializadora Demo {index} S.A.',
                'company_name': f'Demo Trading {index}',
                'main_address': f'Avenida {60 + index} # {70 + index}-{80 + index}',
                'email': f'ventas@demotrade{index}.com',
                'phone': f'+57 1 {310 + index}{600 + index:04d}',
            },
            {
                'document_number': base_doc_number + 4,
                'dv': 9,
                'legal_name': f'Tecnología Demo {index} S.A.S.',
                'company_name': f'Demo Tech {index}',
                'main_address': f'Diagonal {20 + index} # {25 + index}-{35 + index}',
                'email': f'info@demotech{index}.co',
                'phone': f'+57 1 {350 + index}{700 + index:04d}',
            },
            {
                'document_number': base_doc_number + 5,
                'dv': 5,
                'legal_name': f'Servicios Demo {index} LTDA',
                'company_name': f'Demo Services {index}',
                'main_address': f'Transversal {15 + index} # {18 + index}-{28 + index}',
                'email': f'servicios@demoserv{index}.com.co',
                'phone': f'+57 1 {360 + index}{800 + index:04d}',
            },
            {
                'document_number': base_doc_number + 6,
                'dv': 2,
                'legal_name': f'Construcción Demo {index} S.A.',
                'company_name': f'Demo Construction {index}',
                'main_address': f'Calle {80 + index} Sur # {90 + index}-{100 + index}',
                'email': f'proyectos@democonst{index}.co',
                'phone': f'+57 1 {330 + index}{900 + index:04d}',
            },
            {
                'document_number': base_doc_number + 7,
                'dv': 8,
                'legal_name': f'Alimentos Demo {index} S.A.S.',
                'company_name': f'Demo Foods {index}',
                'main_address': f'Carrera {45 + index} # {55 + index}-{65 + index}',
                'email': f'comercial@demofood{index}.com',
                'phone': f'+57 1 {340 + index}{1000 + index:04d}',
            },
            {
                'document_number': base_doc_number + 8,
                'dv': 4,
                'legal_name': f'Logística Demo {index} LTDA',
                'company_name': f'Demo Logistics {index}',
                'main_address': f'Autopista {10 + index} # {12 + index}-{22 + index}',
                'email': f'operaciones@demolog{index}.co',
                'phone': f'+57 1 {370 + index}{1100 + index:04d}',
            },
            {
                'document_number': base_doc_number + 9,
                'dv': 6,
                'legal_name': f'Consultoría Demo {index} S.A.S.',
                'company_name': f'Demo Consulting {index}',
                'main_address': f'Zona Rosa Calle {95 + index} # {105 + index}-{115 + index}',
                'email': f'consultoria@democons{index}.com.co',
                'phone': f'+57 1 {380 + index}{1200 + index:04d}',
            },
            {
                'document_number': base_doc_number + 10,
                'dv': 0,
                'legal_name': f'Manufactura Demo {index} LTDA',
                'company_name': f'Demo Manufacturing {index}', 
                'main_address': f'Zona Industrial Calle {120 + index} # {130 + index}-{140 + index}',
                'email': f'produccion@demomanuf{index}.co',
                'phone': f'+57 1 {390 + index}{1300 + index:04d}',
            },
        ]

        # Use modulo to cycle through the demo data
        company_data = demo_companies[index % len(demo_companies)]

        company = Company.objects.create(
            document_type=nit_document_type,
            document_number=company_data['document_number'],
            dv=company_data['dv'],
            legal_name=company_data['legal_name'],
            company_name=company_data['company_name'],
            country=colombia,
            colombian_city=bogota_city,
            colombian_department=bogota_department,
            main_address=company_data['main_address'],
            email=company_data['email'],
            phone=company_data['phone'],
            dian_economic_activity=economic_activity,
        )

        return company