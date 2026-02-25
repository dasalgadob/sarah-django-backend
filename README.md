# Sarah Project – Django REST API

Django + Django REST Framework port of the original Rails application.

## App layout

| Django app | Models |
|---|---|
| `core` | `User` (Django built-in), `Role`, `Company` |
| `reference_tables` | `ColombianCity`, `ColombianDepartment`, `DianEconomicActivity`, `DocumentType`, `ExciseTaxType`, `ExciseTaxRate`, `IvaType`, `IvaRate`, `UnitMeasure` |
| `accounting` | `Country`, `ItemGroup`, `Item`, `ItemPrice`, `ThirdParty` |

## Requirements

- Python 3.11+
- PostgreSQL (any modern version) or Docker
- The packages in `requirements.txt`

## Database Setup

### Option 1: Docker PostgreSQL (Recommended)

Run a PostgreSQL container with the values from `.env.example`:

```bash
docker run --name sarah-postgres \
  -e POSTGRES_DB=sarah_db \
  -e POSTGRES_USER=postgres \
  -e POSTGRES_PASSWORD=postgres \
  -p 5439:5432 \
  -d postgres:14
```

To stop/start the container later:
```bash
docker stop sarah-postgres
docker start sarah-postgres
```

### Option 2: Local PostgreSQL

Install PostgreSQL locally and create a database named `sarah_db`.

## Quick start

```bash
# 1. Create and activate a virtual environment
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Configure the database and secret key
cp .env.example .env
# Edit .env and set DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD, SECRET_KEY

# 4. Apply migrations
python manage.py migrate

# 5. Load seed data
python manage.py load_seeds

# 6. (Optional) Create demo company records for testing
python manage.py create_demo_companies

# 7. (Optional) Create demo third party records for testing
python manage.py create_demo_third_parties

# 8. (Optional) Create demo item and item price records for testing
python manage.py create_demo_item_prices

# 9. (Optional) Create a superuser for the admin panel
python manage.py createsuperuser

# 10. Start the development server
python manage.py runserver
```

## API endpoints

| Prefix | App |
|---|---|
| `/api/users/` | core |
| `/api/roles/` | core |
| `/api/companies/` | core |
| `/api/colombian-departments/` | reference_tables |
| `/api/colombian-cities/` | reference_tables |
| `/api/dian-economic-activities/` | reference_tables |
| `/api/document-types/` | reference_tables |
| `/api/excise-tax-types/` | reference_tables |
| `/api/excise-tax-rates/` | reference_tables |
| `/api/iva-types/` | reference_tables |
| `/api/iva-rates/` | reference_tables |
| `/api/unit-measures/` | reference_tables |
| `/api/countries/` | accounting |
| `/api/item-groups/` | accounting |
| `/api/third-parties/` | accounting |
| `/api/companies/<id>/items/` | accounting |
| `/api/companies/<id>/item-prices/` | accounting |
| `/api/companies/<id>/third-parties/` | accounting |

## Demo Data

### Creating Demo Companies

To populate the database with realistic demo companies for testing:

```bash
# Create 10 demo companies (default)
python manage.py create_demo_companies

# Create a specific number of companies
python manage.py create_demo_companies --count 20

# Clear existing companies and create new ones
python manage.py create_demo_companies --clear --count 15
```

This command creates realistic Colombian companies with:
- Valid NIT document numbers
- Real Colombian addresses in Bogotá
- Proper email and phone formats
- Associations with existing reference data (document types, cities, etc.)

**Note**: The reference data must be loaded first with `python manage.py load_seeds`.

### Creating Demo Third Parties

To populate each company with realistic third party records (suppliers, clients, employees, etc.):

```bash
# Create 10 third parties per company (default)
python manage.py create_demo_third_parties

# Create a specific number of third parties per company
python manage.py create_demo_third_parties --per-company 15

# Clear existing third parties and create new ones
python manage.py create_demo_third_parties --clear --per-company 20
```

This command creates realistic third party records with:
- **Suppliers**: Companies with NIT documents and business emails
- **Clients**: Commercial entities with proper legal names
- **Employees**: Individuals with cédula documents and personal names  
- **Public Entities**: Government organizations (DIAN, municipalities, etc.)
- Realistic Colombian addresses, phones, and neighborhoods
- Proper associations with document types, cities, and economic activities

**Note**: Companies must exist first. Run `python manage.py create_demo_companies` if needed.

### Creating Demo Items and Item Prices

To populate each company with realistic item and pricing records:

```bash
# Create 10 item prices per company (default)
python manage.py create_demo_item_prices

# Create a specific number of item prices per company
python manage.py create_demo_item_prices --per-company 20

# Clear existing items/prices and create new ones
python manage.py create_demo_item_prices --clear --per-company 15
```

This command creates realistic product and pricing data with:
- **Items**: Technology products, furniture, office supplies with unique codes
- **Buying Prices**: Procurement costs (70-90% of base price)
- **Selling Prices**: Retail costs (110-140% of base price)  
- Automatic **IVA calculation** (19% Colombian tax)
- Random **excise tax calculation** (0-5%)
- **Total price calculation** (price + taxes)
- Proper associations with item groups, unit measures, and tax types

**Note**: Reference data must be loaded first with `python manage.py load_seeds`.

## Interactive documentation

| URL | Description |
|---|---|
| `/api/schema/swagger-ui/` | Swagger UI (OpenAPI 3.0) |
| `/api/schema/redoc/` | ReDoc |
| `/api/schema/` | Raw OpenAPI JSON/YAML |

## Admin

Visit `/admin/` and log in with a superuser account to manage all models.

## Authentication

The API uses JWT (JSON Web Token) authentication with expiring tokens.

### Obtain tokens (Login):
```bash
POST /api/auth/login/
{"username": "your_username", "password": "your_password"}

# Response:
{
  "access": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
}
```

### Use access token in requests:
```
Authorization: Bearer <access-token>
```

### Refresh expired access token:
```bash
POST /api/auth/refresh/
{"refresh": "your-refresh-token"}
```

### Verify token validity:
```bash
POST /api/auth/verify/
{"token": "your-access-token"}
```

### Logout (blacklist refresh token):
```bash
POST /api/auth/logout/
{"refresh": "your-refresh-token"}
```

**Token Lifetimes:**
- Access Token: 60 minutes
- Refresh Token: 7 days

## PostgreSQL environment variables

| Variable | Default | Description |
|---|---|---|
| `DB_HOST` | `localhost` | Database host |
| `DB_PORT` | `5432` | Database port |
| `DB_NAME` | `sarah_db` | Database name |
| `DB_USER` | `postgres` | Database user |
| `DB_PASSWORD` | *(empty)* | Database password |
| `SECRET_KEY` | *(insecure)* | Django secret key – **always set this in production** |
| `DEBUG` | `True` | Set to `False` in production |
| `ALLOWED_HOSTS` | `localhost,127.0.0.1` | Comma-separated list of allowed hosts |


To start postgresql@14 now and restart at login:
  brew services start postgresql@14
Or, if you don't want/need a background service you can just run:
  /opt/homebrew/opt/postgresql@14/bin/postgres -D /opt/homebrew/var/postgresql@14
