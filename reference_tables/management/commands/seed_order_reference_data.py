"""Management command to seed SaleTypeOrder and PaymentMethodOrder data."""

from django.core.management.base import BaseCommand
from django.db import transaction

from ...models import SaleTypeOrder, PaymentMethodOrder


class Command(BaseCommand):
    help = "Seed initial data for SaleTypeOrder and PaymentMethodOrder models"

    def add_arguments(self, parser):
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear existing data before seeding',
        )

    def handle(self, *args, **options):
        with transaction.atomic():
            if options['clear']:
                self.stdout.write('Clearing existing data...')
                SaleTypeOrder.objects.all().delete()
                PaymentMethodOrder.objects.all().delete()
                self.stdout.write(self.style.SUCCESS('Existing data cleared'))

            # Seed SaleTypeOrder data
            sale_types = [
                'Presencial',
                'Envío',
            ]
            
            self.stdout.write('Seeding SaleTypeOrder data...')
            created_sale_types = 0
            
            for sale_type_name in sale_types:
                sale_type, created = SaleTypeOrder.objects.get_or_create(
                    name=sale_type_name
                )
                if created:
                    created_sale_types += 1
                    self.stdout.write(f'  Created: {sale_type_name}')
                else:
                    self.stdout.write(f'  Exists: {sale_type_name}')
            
            # Seed PaymentMethodOrder data
            payment_methods = [
                'Contraentrega',
                'PSE/Transferencia',
                'Efectivo',
                'Addi',
            ]
            
            self.stdout.write('Seeding PaymentMethodOrder data...')
            created_payment_methods = 0
            
            for payment_method_name in payment_methods:
                payment_method, created = PaymentMethodOrder.objects.get_or_create(
                    name=payment_method_name
                )
                if created:
                    created_payment_methods += 1
                    self.stdout.write(f'  Created: {payment_method_name}')
                else:
                    self.stdout.write(f'  Exists: {payment_method_name}')

            # Summary
            self.stdout.write(
                self.style.SUCCESS(
                    f'Seeding complete! '
                    f'Sale types: {created_sale_types} created, '
                    f'Payment methods: {created_payment_methods} created'
                )
            )
            
            # Show final counts
            total_sale_types = SaleTypeOrder.objects.count()
            total_payment_methods = PaymentMethodOrder.objects.count()
            
            self.stdout.write(
                f'Total records - Sale types: {total_sale_types}, '
                f'Payment methods: {total_payment_methods}'
            )