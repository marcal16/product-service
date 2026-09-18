import asyncio
import product_service.srv.events_srv as events_service
import product_service.repos.events_repo as events_repo
import product_service.workers.worker as worker
from product_service.db.models.events import EventTypesEnum


async def test_check_event_after_order(client, db_session):

    # New order
    order_data = {"items": [{"product_id": 1, "quantity": 20}]}

    # Order is created
    create_response = await client.post("/api/v1/orders", json=order_data)
    assert create_response.status_code == 201

    order_data = create_response.json()
    order_id = order_data["id"]

    # Confirm it
    response = await client.post(f"/api/v1/orders/{order_id}/confirm")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "CONFIRMED"

    jobs = await events_repo.get_jobs(db_session)
    assert len(jobs) == 1
    data = jobs[0].payload
    assert data["id"] == order_id


async def test_check_no_events_if_order_is_not_confirmed(client, db_session):

    # New order
    order_data = {"items": [{"product_id": 1, "quantity": 10}]}

    # Order is created
    create_response = await client.post("/api/v1/orders", json=order_data)
    assert create_response.status_code == 201

    jobs = await events_repo.get_jobs(db_session)
    assert len(jobs) == 0


async def test_check_worker_finished(client, db_session):

    # New order
    order_data = {"items": [{"product_id": 1, "quantity": 20}]}

    # Order is created
    create_response = await client.post("/api/v1/orders", json=order_data)
    assert create_response.status_code == 201

    order_data = create_response.json()
    order_id = order_data["id"]

    # Confirm it
    response = await client.post(f"/api/v1/orders/{order_id}/confirm")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "CONFIRMED"

    jobs = await events_repo.get_jobs(db_session)
    assert len(jobs) == 1
    data = jobs[0].payload
    assert data["id"] == order_id

    await events_service.process_job(db_session)

    jobs = await events_repo.get_jobs(db_session, data["id"])
    job = jobs[0]
    assert job.status == EventTypesEnum.PROCESSED
    assert job.attempts == 1


async def test_check_worker_failed(client, db_session):

    # New order
    order_data = {"items": [{"product_id": 1, "quantity": 20}]}

    # Order is created
    create_response = await client.post("/api/v1/orders", json=order_data)
    assert create_response.status_code == 201

    order_data = create_response.json()
    order_id = order_data["id"]

    # Confirm it
    response = await client.post(f"/api/v1/orders/{order_id}/confirm")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "CONFIRMED"

    jobs = await events_repo.get_jobs(db_session)
    assert len(jobs) == 1
    data = jobs[0].payload
    assert data["id"] == order_id

    await events_service.process_job(db_session, error=True)

    jobs = await events_repo.get_jobs(db_session, data["id"])
    job = jobs[0]
    assert job.status == EventTypesEnum.FAILED
    assert job.last_error is not None

    # next try
    await events_service.process_job(db_session)

    jobs = await events_repo.get_jobs(db_session, data["id"])
    job = jobs[0]
    assert job.status == EventTypesEnum.PROCESSED
    assert job.attempts == 2


async def test_check_silmultaneous_workers_success(client, db_session):

    # Order
    order_data = {"items": [{"product_id": 1, "quantity": 20}]}

    # Order is created
    create_response = await client.post("/api/v1/orders", json=order_data)
    order1_id = create_response.json()["id"]

    # Confirm it
    await client.post(f"/api/v1/orders/{order1_id}/confirm")

    # Order 2
    order_data = {"items": [{"product_id": 1, "quantity": 20}]}

    # Order is created
    create_response = await client.post("/api/v1/orders", json=order_data)
    order2_id = create_response.json()["id"]

    # Confirm it
    await client.post(f"/api/v1/orders/{order2_id}/confirm")

    results = await asyncio.gather(worker.single_worker(), worker.single_worker())

    processed = [status for status in results if status == EventTypesEnum.PROCESSED]
    assert len(processed) == 2

    jobs = await events_repo.get_jobs(db_session)
    assert len(jobs) == 0
