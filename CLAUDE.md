# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

Django + Django REST Framework port of a Rails accounting/inventory application for Colombian companies (NIT/cédula, DIAN economic activities, IVA, impuesto al consumo). Some view logic explicitly "mirrors Rails behaviour" — check comments before refactoring those spots.

Three Django apps:
| App | Models |
|---|---|
| `core` | `User` (Django built-in), `Role`, `Company` |
| `reference_tables` | `ColombianCity`, `ColombianDepartment`, `DianEconomicActivity`, `DocumentType`, `ExciseTaxType`, `ExciseTaxRate`, `IvaType`, `IvaRate`, `UnitMeasure`, `SaleTypeOrder`, `PaymentMethodOrder` |
| `accounting` | `Country`, `ItemGroup`, `Item`, `ItemPrice`, `ThirdParty`, `Order`, `OrderItem`, `ItemProperty*` |

## Commands

```bash
# Run the dev server
python manage.py runserver

# Migrations
python manage.py makemigrations
python manage.py migrate

# Run the full test suite
python -m pytest accounting/tests/ -v

# Run a single test file / class / test
python -m pytest accounting/tests/test_order_views.py -v
python -m pytest accounting/tests/test_order_views.py::TestOrderUpdateEndpoint -v
python -m pytest accounting/tests/test_order_views.py::TestOrderUpdateEndpoint::test_patch_updates_existing_item_by_id -v

# Validate the app + OpenAPI schema after touching views/serializers (no formal CI exists, so do this manually)
python manage.py check
python manage.py spectacular --file /tmp/schema.yaml

# Seed reference data / demo records (in order)
python manage.py load_seeds
python manage.py create_demo_companies
python manage.py create_demo_third_parties
python manage.py create_demo_item_prices
```

Tests require a real Postgres connection (see `.env`, default port `5439` for the Docker container in the README) — `pytest-django` creates/destroys a real test database per run, there is no SQLite/mocked-DB fallback.

There is no linter/formatter configured (no flake8/black/ruff config) and no CI workflow — `manage.py check` + the test suite are the only automated gates.

## Architecture

### Layering: views → serializers → services → models

- **`models.py`** per app. Every model extends `SafeDeleteModel` (`django-safedelete`, `_safedelete_policy = SOFT_DELETE_CASCADE`) and has a `history = HistoricalRecords()` field (`django-simple-history`). Deletes are soft; `Model.objects` excludes soft-deleted rows, `Model.all_objects` includes them (used by every viewset's `restore` action).
- **`accounting/serializers/`** is a package, not a single file: `basic_serializers.py` (Item/ItemPrice/Country/ThirdParty/etc.), `order_serializer.py` (Order/OrderItem/ItemProperty*), and small dedicated `*_excel_serializers.py` files used **only** for OpenAPI documentation of file-upload/response shapes (not for actual (de)serialization logic). Re-exported through `serializers/__init__.py` with an explicit `__all__`.
- **`accounting/views/`** is a package: `basic_views.py`, `order_views.py`. Same re-export pattern via `views/__init__.py`.
- **`accounting/services/`** holds business logic that doesn't belong in a serializer or view: Excel import/export classes (`item_excel_export.py`, `item_excel_import.py`, `item_price_excel_*.py`), shared column-layout constants (`item_excel_columns.py`, `item_price_excel_columns.py` — single source of truth for header text + field order, imported by both the exporter and importer for a given resource), `tax_calculations.py` (shared `calculate_taxes(item, amount)` used by both Order creation and ItemPrice Excel import so tax math isn't duplicated), and `excel_filenames.py` (shared `Prefix#CompanyName#YYYY-MM-DD.xlsx` builder).
- `core` and `reference_tables` are flatter (single `models.py`/`serializers.py`/`views.py`/`urls.py` per app) — only `accounting` has grown into the views/serializers/services package structure above as it absorbed most of the business logic.

### Company-scoped resources

Many resources are nested under `/api/companies/{company_pk}/...` (see `accounting/urls.py`'s `company_items_router`/`company_orders_router`) as well as exposed at a flat top-level route. The same `ViewSet` serves both; `get_queryset()` checks `self.kwargs.get('company_pk')` and filters or doesn't. When creating objects under a company-scoped route, `company` is **not** in the request body — viewsets override `create()`/`perform_create()` to inject `company_id` from the URL kwarg before validation (see `ItemViewSet`, `ItemPriceViewSet`). `OrderViewSet` is the exception: `company` is always a required field in the payload, even under the nested route.

### Custom create()/update() overrides on ModelViewSet

Several viewsets override `create()` (and now `OrderViewSet.update()`) rather than relying purely on `perform_create()`, because required FK fields (like `company`) need to be injected into the data dict **before** `serializer.is_valid()` runs — `perform_create()` alone runs too late for fields the serializer would otherwise reject as missing.

`OrderViewSet.get_serializer_class()` branches by `self.action`: `create` → `OrderCreateSerializer`, `update`/`partial_update` → `OrderUpdateSerializer`, everything else → `OrderSerializer` (read representation, `order_items` is read-only there). `OrderUpdateSerializer.update()` treats a provided `order_items` list as the **full replacement set**: entries with `id` update that existing `OrderItem` (must belong to the order, validated in `validate_order_items`), entries without `id` create a new line, and any existing line not referenced by `id` is deleted. Omitting `order_items` from the PATCH body entirely leaves existing items untouched.

### Pricing/tax computation is always server-derived, never trusted from the client

`OrderItemCreateSerializer`/`OrderItemUpdateSerializer` accept `item_price` (an `ItemPrice` id) + `quantity` + an *optional* `unit_price` override. They do **not** accept `line_iva`, `line_excise_tax`, or `line_total_with_taxes` — those are always computed via `services.tax_calculations.calculate_taxes(item, amount)` from the resolved `unit_price` and the `Item`'s `iva_rate`/`excise_tax_rate`, both in `OrderCreateSerializer.create()`/`OrderUpdateSerializer.update()` and in `ItemPriceExcelImporter`. If you add another money-in code path, reuse `calculate_taxes` rather than re-deriving the formula.

### Filtering/ordering/search

Company-scoped list endpoints use `django_filters.rest_framework.DjangoFilterBackend` with a dedicated `*Filter(django_filters.FilterSet)` class per viewset (e.g. `ItemFilter`, `ItemPriceFilter` in `basic_views.py`) plus DRF's `OrderingFilter`. Text filters default to `lookup_expr='icontains'`; FK filters are exact-match by id unless a `CharFilter` with `field_name='related__field'` is declared for cross-relation text search (see `ItemPriceFilter.code`/`.name` filtering on `item__code`/`item__name`).

### Excel import/export pattern

For any resource that gets a `download`/`upload` pair (see `Item`, `ItemPrice`), follow the existing 3-file shape in `accounting/services/`:
1. `<resource>_excel_columns.py` — column key constants, `COLUMN_ORDER`, `COLUMN_HEADERS` (Spanish), and a derived `HEADER_ROW`. Both exporter and importer import from here so headers/order never drift apart.
2. `<resource>_excel_export.py` — an `Exporter` class wrapping a queryset, building an `openpyxl.Workbook`, exposing `as_http_response(filename=...)`.
3. `<resource>_excel_import.py` — an `Importer` class with `import_workbook(file_obj)` that iterates rows, validates per-row (collecting field errors into a dict rather than raising on the first problem), and returns an `ImportResult` (`created`/`updated`/`errors: list[RowError]`) — a bad row is skipped and reported, it never aborts the whole upload. Each row is wrapped in its own `transaction.atomic()` so partial success is safe.

Columns suffixed "(Solo Lectura)" in headers are computed/derived and ignored on import even if a value is present in the cell; columns suffixed "(No Editar)" are still read on import (they're the upsert key or a FK reference) but aren't meant to be hand-edited for existing rows. `download`/`upload` actions are added directly on the resource's existing `ModelViewSet` via `@action(detail=False, ...)`, not a separate viewset.

OpenAPI documentation for these actions needs an explicit `@extend_schema(...)` (from `drf_spectacular.utils`) — without it, drf-spectacular falls back to the viewset's default `serializer_class`/pagination and produces a misleading schema for these non-standard actions. Always confirm with `python manage.py spectacular --file /tmp/schema.yaml` (clean run, no warnings) after adding one.

### CORS gotcha for file downloads

`CORS_ALLOW_ALL_HEADERS` (in `config/settings.py`) controls which **request** headers the browser may send — it does *not* expose response headers to frontend JS. Any endpoint that returns a `Content-Disposition` filename (the Excel downloads) needs the header listed in `CORS_EXPOSE_HEADERS`, or the frontend's `fetch()` will see `null` for it.

### Pagination

Default pagination is `core.pagination.CustomPageNumberPagination`, which renames `results` → `data` and adds `total_pages` to the standard DRF paginated response shape. `LargeResultsSetPagination`/`SmallResultsSetPagination` (also in `core/pagination.py`) override `page_size` for specific viewsets. Endpoints meant to populate a frontend `<select>` (e.g. `items/select-list/`, `*-types/` choice endpoints) explicitly set `pagination_class = None` on the action.

### Tests

Live under `accounting/tests/`, configured via root `pytest.ini` (`DJANGO_SETTINGS_MODULE = config.settings`). `accounting/tests/conftest.py` provides the shared fixtures most tests build on: `company`/`other_company` (full Colombian FK chain — `DocumentType`, `Country`, `ColombianDepartment`, `ColombianCity`, `DianEconomicActivity`), `item_group`, `unit_measure`, `iva_type`/`iva_rate`, `excise_tax_type`/`excise_tax_rate`, `item`, `item_price`, `third_party`, `sale_type`, `payment_method`, and `api_client` (a `rest_framework.test.APIClient` pre-authenticated via `force_authenticate` — auth is required on virtually every endpoint, `DEFAULT_PERMISSION_CLASSES` is `IsAuthenticated`). Cross-company isolation (an id from `other_company` must be rejected) is a recurring test case worth writing for any new company-scoped endpoint.

When a DecimalField value is set via `Model.objects.create(price='100000.00', ...)`, the in-memory Python attribute stays a `str` until the object is reloaded from the DB — call `.refresh_from_db()` (or re-fetch) before asserting `Decimal` equality in a test.
