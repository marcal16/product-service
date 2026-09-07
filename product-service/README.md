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


#Kubernetess
added 2 endpoint for containers probes and healthchecks
added health check to docker compose files
added kubernetess manifests for secrest,services,statefulSet for db and deploy for api

Commands outputs:
pods:
NAME                                   READY   STATUS    RESTARTS   AGE
product-service-app-594bcd5cc5-68vgh   1/1     Running   0          21m
product-service-app-594bcd5cc5-f65bl   1/1     Running   0          21m
product-service-db-0                   1/1     Running   0          15m

services:
NAME              TYPE        CLUSTER-IP       EXTERNAL-IP   PORT(S)          AGE
fastapi-service   NodePort    10.110.120.108   <none>        8000:30080/TCP   135m
kubernetes        ClusterIP   10.96.0.1        <none>        443/TCP          10d
postgres          ClusterIP   10.105.61.66     <none>        5432/TCP         135m

api pod
Name:             product-service-app-594bcd5cc5-68vgh
Namespace:        default
Priority:         0
Service Account:  default
Node:             minikube/192.168.49.2
Start Time:       Mon, 07 Sep 2026 15:41:11 +0800
Labels:           app=fastapi
                  pod-template-hash=594bcd5cc5
Annotations:      <none>
Status:           Running
IP:               10.244.0.48
IPs:
  IP:           10.244.0.48
Controlled By:  ReplicaSet/product-service-app-594bcd5cc5
Containers:
  product-service:
    Container ID:   docker://b8cea6b751bbee18ca46b89744faad8ce769cc92d356ffc48129ac5a74464a4f
    Image:          products:v1.0.0
    Image ID:       docker://sha256:d63fb0d77033b1d826e80ec9b14d59896a46a94a1c30fb9671dd623089027c1d
    Port:           8000/TCP
    Host Port:      0/TCP
    State:          Running
      Started:      Mon, 07 Sep 2026 15:41:12 +0800
    Ready:          True
    Restart Count:  0
    Limits:
      cpu:     500m
      memory:  128Mi
    Requests:
      cpu:      250m
      memory:   64Mi
    Liveness:   http-get http://:8000/api/v1/health/live delay=15s timeout=3s period=60s successThreshold=1 failureThreshold=5
    Readiness:  http-get http://:8000/api/v1/health/ready delay=5s timeout=3s period=60s successThreshold=1 failureThreshold=3
    Environment:
      DB_SRC:  <set to the key 'db_src' in secret 'db-connection-data'>  Optional: false
    Mounts:
      /var/run/secrets/kubernetes.io/serviceaccount from kube-api-access-mc8q5 (ro)
Conditions:
  Type                        Status
  PodReadyToStartContainers   True 
  Initialized                 True 
  Ready                       True 
  ContainersReady             True 
  PodScheduled                True 
Volumes:
  kube-api-access-mc8q5:
    Type:                    Projected (a volume that contains injected data from multiple sources)
    TokenExpirationSeconds:  3607
    ConfigMapName:           kube-root-ca.crt
    Optional:                false
    DownwardAPI:             true
QoS Class:                   Burstable
Node-Selectors:              <none>
Tolerations:                 node.kubernetes.io/not-ready:NoExecute op=Exists for 300s
                             node.kubernetes.io/unreachable:NoExecute op=Exists for 300s
Events:
  Type     Reason     Age                From               Message
  ----     ------     ----               ----               -------
  Normal   Scheduled  22m                default-scheduler  Successfully assigned default/product-service-app-594bcd5cc5-68vgh to minikube
  Normal   Pulled     22m                kubelet            spec.containers{product-service}: Container image "products:v1.0.0" already present on machine and can be accessed by the pod
  Normal   Created    22m                kubelet            spec.containers{product-service}: Container created
  Normal   Started    22m                kubelet            spec.containers{product-service}: Container started
  Warning  Unhealthy  17m (x4 over 19m)  kubelet            spec.containers{product-service}: Readiness probe failed: HTTP probe failed with statuscode: 503


probes logs:
INFO:     Started server process [1]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
INFO:     10.244.0.1:54086 - "GET /api/v1/health/live HTTP/1.1" 200 OK
INFO:     10.244.0.1:54100 - "GET /api/v1/health/ready HTTP/1.1" 200 OK
