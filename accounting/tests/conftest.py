import pytest
from django.contrib.auth.models import User
from rest_framework.test import APIClient

from accounting.models import Country, Item, ItemGroup, ItemPrice, ThirdParty
from core.models import Company
from reference_tables.models import (
    ColombianCity,
    ColombianDepartment,
    DianEconomicActivity,
    DocumentType,
    ExciseTaxRate,
    ExciseTaxType,
    IvaRate,
    IvaType,
    PaymentMethodOrder,
    SaleTypeOrder,
    UnitMeasure,
)


@pytest.fixture
def company(db):
    document_type = DocumentType.objects.create(code=31, name='NIT')
    country = Country.objects.create(code=170, name='Colombia')
    department = ColombianDepartment.objects.create(code='11', name='Bogotá D.C.')
    city = ColombianCity.objects.create(code='11001', name='Bogotá', colombian_department=department)
    economic_activity = DianEconomicActivity.objects.create(code='4771', name='Comercio al por menor')
    return Company.objects.create(
        document_type=document_type,
        document_number=900123456,
        legal_name='Test Company SAS',
        country=country,
        colombian_city=city,
        colombian_department=department,
        dian_economic_activity=economic_activity,
    )


@pytest.fixture
def other_company(db):
    document_type = DocumentType.objects.create(code=31, name='NIT')
    country = Country.objects.create(code=171, name='Otro País')
    department = ColombianDepartment.objects.create(code='05', name='Antioquia')
    city = ColombianCity.objects.create(code='05001', name='Medellín', colombian_department=department)
    economic_activity = DianEconomicActivity.objects.create(code='4772', name='Otra actividad')
    return Company.objects.create(
        document_type=document_type,
        document_number=900654321,
        legal_name='Other Company SAS',
        country=country,
        colombian_city=city,
        colombian_department=department,
        dian_economic_activity=economic_activity,
    )


@pytest.fixture
def item_group(db):
    return ItemGroup.objects.create(name='Apparel')


@pytest.fixture
def unit_measure(db):
    return UnitMeasure.objects.create(abbreviation='UN', name='Unidad')


@pytest.fixture
def iva_type(db):
    return IvaType.objects.create(name='General')


@pytest.fixture
def iva_rate(db, iva_type):
    return IvaRate.objects.create(iva_type=iva_type, value='19.00')


@pytest.fixture
def excise_tax_type(db):
    return ExciseTaxType.objects.create(name='Tobacco')


@pytest.fixture
def excise_tax_rate(db, excise_tax_type):
    return ExciseTaxRate.objects.create(excise_tax_type=excise_tax_type, value='10.00')


@pytest.fixture
def item(db, company, item_group, unit_measure, iva_type, iva_rate):
    return Item.objects.create(
        base_code='TSHIRT001',
        base_name='Cotton T-Shirt',
        name='Cotton T-Shirt',
        item_group=item_group,
        unit_measure=unit_measure,
        company=company,
        iva_type=iva_type,
        iva_rate=iva_rate,
    )


@pytest.fixture
def item_price(db, item, company):
    price = ItemPrice.objects.create(
        item=item, company=company, item_price_type=ItemPrice.SELLING,
        price='100000.00', iva='19000.00', excise_tax='0.00', total='119000.00',
    )
    price.refresh_from_db()
    return price


@pytest.fixture
def third_party(db, company):
    document_type = DocumentType.objects.create(code=13, name='Cédula de ciudadanía')
    country = Country.objects.create(code=999, name='Third Party Country')
    department = ColombianDepartment.objects.create(code='99', name='Cundinamarca')
    city = ColombianCity.objects.create(code='99001', name='Soacha', colombian_department=department)
    return ThirdParty.objects.create(
        document_type=document_type,
        document_number=1000999888,
        neighborhood='Centro',
        third_party_type=ThirdParty.CLIENT,
        company=company,
        country=country,
        colombian_city=city,
        colombian_department=department,
        legal_name='Client Test SAS',
    )


@pytest.fixture
def sale_type(db):
    return SaleTypeOrder.objects.create(name='Retail')


@pytest.fixture
def payment_method(db):
    return PaymentMethodOrder.objects.create(name='Cash')


@pytest.fixture
def api_client(db):
    user = User.objects.create_user(username='tester', password='pass1234')
    client = APIClient()
    client.force_authenticate(user=user)
    return client
