from datetime import datetime, timedelta


async def test_inventory_report(client):

    payload = {"quantity": 95}
    reserve_response = await client.post("/api/v1/products/1/reserve", json=payload)
    assert reserve_response.status_code == 200

    filters = {"available_below": 10}
    response = await client.get("/api/v1/reports/inventory", params=filters)
    assert response.status_code == 200

    data = response.json()
    assert len(data) == 1
    prod = data[0]
    assert prod["total_stock"] == prod["quantity"] + prod["reserved"]


async def test_orders_report(client):

    # New orders
    order_data = {"items": [{"product_id": 1, "quantity": 40}, {"product_id": 2, "quantity": 30}]}
    response = await client.post("/api/v1/orders", json=order_data)
    order_id = response.json()["id"]
    response = await client.post(f"/api/v1/orders/{order_id}/confirm")
    assert response.status_code == 200

    order_data = {"items": [{"product_id": 3, "quantity": 10}, {"product_id": 2, "quantity": 15}]}
    response = await client.post("/api/v1/orders", json=order_data)
    order_id = response.json()["id"]
    response = await client.post(f"/api/v1/orders/{order_id}/cancel")
    assert response.status_code == 200

    order_data = {"items": [{"product_id": 2, "quantity": 20}]}
    response = await client.post("/api/v1/orders", json=order_data)
    order_id = response.json()["id"]

    # report
    data = {"created_to": datetime.now() - timedelta(hours=10)}
    response = await client.get("/api/v1/reports/orders", params=data)
    data = response.json()
    assert len(data) == 4
    assert data["total"] == 0

    response = await client.get("/api/v1/reports/orders")
    data = response.json()
    assert data["total"] == 3
    assert data["confirmed"] == 1
    assert data["cancelled"] == 1


async def test_top_products_report(client):

    # New orders
    order_data = {"items": [{"product_id": 1, "quantity": 40}, {"product_id": 2, "quantity": 30}]}
    response = await client.post("/api/v1/orders", json=order_data)
    order_id = response.json()["id"]
    response = await client.post(f"/api/v1/orders/{order_id}/confirm")
    assert response.status_code == 200

    order_data = {"items": [{"product_id": 3, "quantity": 10}, {"product_id": 2, "quantity": 15}]}
    response = await client.post("/api/v1/orders", json=order_data)
    order_id = response.json()["id"]
    response = await client.post(f"/api/v1/orders/{order_id}/cancel")
    assert response.status_code == 200

    order_data = {"items": [{"product_id": 2, "quantity": 20}]}
    response = await client.post("/api/v1/orders", json=order_data)
    order_id = response.json()["id"]

    # report
    response = await client.get("/api/v1/reports/products/top-ordered", params={})
    data = response.json()
    assert len(data) == 3

    prod1 = data[0]
    assert prod1["ordered_quantity"] == 65
    assert prod1["product_id"] == 2

    prod3 = data[-1]
    assert prod3["product_id"] == 3
    assert prod3["ordered_quantity"] == 10
