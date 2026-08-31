#######PRODUCT SERVICE############

Service allow to add, update, get, mark as deleted products

To launch:
docker compose up

For test need to create db in local postgres with name test_products_service or change it URL inside
tests conftest.py
Project uses poetry, so first
-- poetry install 
then:
-- poetry run pytest

API endpoints:
POST /api/v1/products
GET /api/v1/products
GET /api/v1/products/{product_id}
PUT /api/v1/products/{product_id}
DELETE /api/v1/products{product_id}

.env example file structure:
POSTGRES_USER=postgres
POSTGRES_PASSWORD=123
POSTGRES_DB=products_service
DB_SRC=postgresql+asyncpg://postgres:123@localhost/products_service #For local launch

Database strcuture:
    type: CurrencyEnum (USD, EUR, CAD), can be extended
    tables:
        Products (id, name, price, currency, sku, quantity, is_active, created_at, updated_at)

Project structure:
    api/v1: api endpoints by block, router unites them all
    core: settings, logs setup, security
    db: base, engine, session maker
      models: db models
    dependencies: session
    domain: project exceptions and other strcutures (models)
      exceptions
    repos: repositories, all db operations
    schemas: pydantic schemas
    srv: service layer