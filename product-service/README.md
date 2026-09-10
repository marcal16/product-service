#######PRODUCT SERVICE############

Service allow to add, update, get, mark as deleted products

To launch:
docker compose up

To test:
docker compose -f docker-compose-dev.yaml up --build

API endpoints:
product:
POST /api/v1/products
GET /api/v1/products
GET /api/v1/products/{product_id}
PUT /api/v1/products/{product_id}
DELETE /api/v1/products{product_id}
POST /api/v1/products/{product_id}/reserve
orders:
POST /api/v1/orders
POST /api/v1/orders/{order_id}/cancel
POST /api/v1/orders/{order_id}/confirm
healtcheck:
GET /api/v1/health/live
GET /api/v1/health/ready

.env example file structure:
POSTGRES_USER=postgres
POSTGRES_PASSWORD=123
POSTGRES_DB=products_service
DB_SRC=postgresql+asyncpg://postgres:123@localhost/products_service #Main db
TESTING=True
TEST_DB_SRC=postgresql+asyncpg://postgres:123@localhost/test_db #test db, works with testing=true

Database strcuture:
    type: CurrencyEnum (USD, EUR, CAD), can be extended
    tables:
        Products (id, name, description, price, currency, sku, quantity, reserved, 
        is_active, created_at, updated_at)
        Orders (id, status, created_at, updated_at)
        Order_items (id, order_id, product_id, quantity)

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
    k8s: kubernetes manifests

#Kubernetess
The API runs with two replicas. PostgreSQL runs as a StatefulSet. The API uses readiness and liveness probes. When PostgreSQL becomes unavailable, API Pods remain running but become unready; after PostgreSQL recovery they become ready again.

#Docker
docker-compose.yaml, Dockerfile - prod app launch on docker
docker-compose-dev.yaml, Dockerfile.dev - test launch
Dockerfile_minikube - build for migration to k8s, excluded alembic migration

CI pipeline

Every push to main and pull-request run:
- poetry and its dependencies installation
- alembic migration
- pytest
- docker build
- ruff code quality and formatting checks

#Processes

Products:
  CRUD actions (create, get, update, delete) 
  Basic reserve - checks quantity and moves the amount to reserve
Health:
  made for containers healthchecks
Orders:
  create - order documents for reservation, its lock products before
           quantity checks. Products sorted by id before lock in order
           to avoid deadlocks. Order statuses: PENGING, CANCELLED, CONFIRMED
  cancel - cancel order. All reserved amounts move back to quantity. Order locks
           first, if failed the operation is cancelled. If status is not pendings
           it returns error. Confirmed orders must be reversed by another document
           Items locked next ordered by id. There are no reservation and quantity checks,
           because there must be enough. The amount in order items are moved from reserve
           to quantity.
  confirm - confirm order. All checks are the same like in cancel process. Amount from
            products' reserve are written off. The reserved amount must in product must be enough
            to be written off.