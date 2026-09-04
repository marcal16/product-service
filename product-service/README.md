#######PRODUCT SERVICE############

Service allow to add, update, get, mark as deleted products

To launch:
docker compose up

To test:
docker compose -f docker-compose-dev.yaml up --build

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
        Products (id, name, description, price, currency, sku, quantity, is_active, created_at, updated_at)

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

  #AC-102
  db models:
    - added column 'reserverd' to products table, type int

  schemas:
    - ProductReserve - used for reservation, includes: quantity
    - ProdeuctReservationResponse - response, include: quantity, reserved, updated_at, sku

  endpoint:
    - new endpoint for reservation:
        POST /api/v1/products/{product_id}/reserve
    
  domain exceptions:
    - InsufficientQuantity - attempt to reserve more than stocked

  process:
    at service layer quantity checked for being positive, so at db level to checks
    at repo level userd pessimistic lock, record has got with 'with_for_update' construction
      so it is locked for one request at time, others wait in stock
      being locked it cheked for stock and after that changes are made

  tests:
    new file was created 'test_products_reservation_api.py', there is also concurrent requests test


#AC-103
Order business process

In order to extend business process logic in the future,
for the process created new service, repo, schemas, api files
added new exception

db:
  - new:
      - enum type OrderStatusEnum (PENDING, CONFIRMED, CANCELLED)
      - table orders (id, status, created_at, updated_at)
      - table orders itesm (id, order_id, product_id, quantity)

API:
  new route: 
    - POST /api/v1/orders/
        accepts list of items (id, quantity), can be repeated, their quantity will be summed and
        checked for availability as a one total number
        returns 422 InvalidOrderData if list of items is empty or any item has 0 quantity
        returns 404 ProductNotFound if non existing items are found in request
        returns 400 InsufficientQuantity if there are insufficient quantity for any of items

        order uses pessimisitc lock all items from the order at once in order to check their 
        availability and make reservation. It will be waiting until all of them are available
        before starts the process. So, deadlock will never happen.

Tests:
  restructurized to individual folders due to different fixtures are needed
  orders tested for every descrived error, correct requests, concurrent execution