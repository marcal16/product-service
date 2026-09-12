import asyncio


async def test_adjustment_valid(client):

    adj_data = {"reason": "123", "items": [{"product_id": 1, "quantity_delta": -10}]}

    # product before doc
    prod = await client.get("/api/v1/products/1")
    prod_data = prod.json()

    response = await client.post("/api/v1/products/inventory-adjustments", json=adj_data)
    assert response.status_code == 201

    # product after doc
    prod2 = await client.get("/api/v1/products/1")
    prod2_data = prod2.json()

    data = response.json()
    assert data["status"] == "PENDING"
    assert prod_data["quantity"] == prod2_data["quantity"]


async def test_adjustment_empty_items(client):

    adj_data = {"reason": "123", "items": []}

    response = await client.post("/api/v1/products/inventory-adjustments", json=adj_data)

    assert response.status_code == 400
    data = response.json()
    assert "No items provided" in data["detail"]


async def test_adjustment_zero_quantity(client):

    adj_data = {"reason": "123", "items": [{"product_id": 1, "quantity_delta": 0}]}

    response = await client.post("/api/v1/products/inventory-adjustments", json=adj_data)

    assert response.status_code == 400
    data = response.json()
    assert "Product ID 1 has zero quantity" in data["detail"]


async def test_adjustment_non_existing_prod(client):

    adj_data = {"reason": "123", "items": [{"product_id": 99, "quantity_delta": 30}]}

    response = await client.post("/api/v1/products/inventory-adjustments", json=adj_data)

    assert response.status_code == 404
    data = response.json()
    assert "One or more product not found" in data["detail"]
    assert "99" in data["detail"]


async def test_post_adjustment_positive_delta(client):

    adj_data = {"reason": "123", "items": [{"product_id": 1, "quantity_delta": 10}]}

    # product before doc
    prod = await client.get("/api/v1/products/1")
    prod_data = prod.json()

    response = await client.post("/api/v1/products/inventory-adjustments", json=adj_data)
    assert response.status_code == 201
    data = response.json()
    doc_id = data["id"]

    post_response = await client.post(f"/api/v1/products/inventory-adjustments/{doc_id}/post")
    assert post_response.status_code == 200

    # product after doc
    prod2 = await client.get("/api/v1/products/1")
    prod2_data = prod2.json()

    post_data = post_response.json()
    assert post_data["message"] == "posted"
    assert prod2_data["quantity"] == (prod_data["quantity"] + adj_data["items"][0]["quantity_delta"])


async def test_post_adjustment_negative_delta(client):

    adj_data = {"reason": "123", "items": [{"product_id": 1, "quantity_delta": -10}]}

    # product before doc
    prod = await client.get("/api/v1/products/1")
    prod_data = prod.json()

    response = await client.post("/api/v1/products/inventory-adjustments", json=adj_data)
    assert response.status_code == 201
    data = response.json()
    doc_id = data["id"]

    post_response = await client.post(f"/api/v1/products/inventory-adjustments/{doc_id}/post")
    assert post_response.status_code == 200

    # product after doc
    prod2 = await client.get("/api/v1/products/1")
    prod2_data = prod2.json()

    post_data = post_response.json()
    assert post_data["message"] == "posted"
    assert prod2_data["quantity"] == (prod_data["quantity"] + adj_data["items"][0]["quantity_delta"])


async def test_post_nonexisting_adjustment(client):

    post_response = await client.post("/api/v1/products/inventory-adjustments/99/post")
    assert post_response.status_code == 404
    data = post_response.json()
    assert "Adjustment does not exists" in data["detail"]


async def test_post_wrong_status(client):

    adj_data = {"reason": "123", "items": [{"product_id": 1, "quantity_delta": 10}]}

    response = await client.post("/api/v1/products/inventory-adjustments", json=adj_data)
    assert response.status_code == 201
    data = response.json()
    doc_id = data["id"]

    post_response = await client.post(f"/api/v1/products/inventory-adjustments/{doc_id}/post")
    assert post_response.status_code == 200

    post_response2 = await client.post(f"/api/v1/products/inventory-adjustments/{doc_id}/post")
    assert post_response2.status_code == 422
    data = post_response2.json()
    assert "Must be PENDING" in data["detail"]


async def test_post_insufficient_quantity(client):

    adj_data = {"reason": "123", "items": [{"product_id": 1, "quantity_delta": -9999}]}

    response = await client.post("/api/v1/products/inventory-adjustments", json=adj_data)
    assert response.status_code == 201
    data = response.json()
    doc_id = data["id"]

    post_response = await client.post(f"/api/v1/products/inventory-adjustments/{doc_id}/post")
    assert post_response.status_code == 422
    data = post_response.json()
    assert "not enough quantity" in data["detail"]

    doc = await client.get(f"/api/v1/products/inventory-adjustments/{doc_id}")
    doc_data = doc.json()
    assert doc_data["status"] == "PENDING"


async def test_adjustment_cancelled(client):

    adj_data = {"reason": "123", "items": [{"product_id": 1, "quantity_delta": -10}]}

    response = await client.post("/api/v1/products/inventory-adjustments", json=adj_data)
    assert response.status_code == 201
    data = response.json()
    doc_id = data["id"]

    cancel_resp = await client.post(f"/api/v1/products/inventory-adjustments/{doc_id}/cancel")
    assert cancel_resp.status_code == 200
    data = cancel_resp.json()
    assert data["message"] == "cancelled"


async def test_adjustment_cancel_wrong_status(client):

    adj_data = {"reason": "123", "items": [{"product_id": 1, "quantity_delta": -10}]}

    response = await client.post("/api/v1/products/inventory-adjustments", json=adj_data)
    assert response.status_code == 201
    data = response.json()
    doc_id = data["id"]

    cancel_resp = await client.post(f"/api/v1/products/inventory-adjustments/{doc_id}/cancel")
    assert cancel_resp.status_code == 200

    cancel_resp2 = await client.post(f"/api/v1/products/inventory-adjustments/{doc_id}/cancel")
    assert cancel_resp2.status_code == 422
    data = cancel_resp2.json()
    assert "Must be PENDING" in data["detail"]


async def test_multi_product_adj_failed(client):

    adj_data = {
        "reason": "123",
        "items": [{"product_id": 1, "quantity_delta": 10}, {"product_id": 2, "quantity_delta": -10000}],
    }

    # product after doc
    prod = await client.get("/api/v1/products/1")
    prod_data = prod.json()

    response = await client.post("/api/v1/products/inventory-adjustments", json=adj_data)
    assert response.status_code == 201
    data = response.json()
    doc_id = data["id"]

    post_response = await client.post(f"/api/v1/products/inventory-adjustments/{doc_id}/post")
    assert post_response.status_code == 422
    data = post_response.json()
    assert "not enough quantity" in data["detail"]

    # product after doc
    prod2 = await client.get("/api/v1/products/1")
    prod2_data = prod2.json()

    assert prod_data["quantity"] == prod2_data["quantity"]

    doc = await client.get(f"/api/v1/products/inventory-adjustments/{doc_id}")
    doc_data = doc.json()
    assert doc_data["status"] == "PENDING"


# concurrency
async def test_two_adj_same_product(client):

    adj_data = {"reason": "123", "items": [{"product_id": 1, "quantity_delta": 10}]}

    response = await client.post("/api/v1/products/inventory-adjustments", json=adj_data)
    assert response.status_code == 201
    data = response.json()
    doc1_id = data["id"]

    response = await client.post("/api/v1/products/inventory-adjustments", json=adj_data)
    assert response.status_code == 201
    data = response.json()
    doc2_id = data["id"]

    responses = await asyncio.gather(
        client.post(f"/api/v1/products/inventory-adjustments/{doc1_id}/post"),
        client.post(f"/api/v1/products/inventory-adjustments/{doc2_id}/post"),
    )

    successful_responses = [response for response in responses if response.status_code == 200]
    # Both should succeed
    assert len(successful_responses) == 2

    doc = await client.get(f"/api/v1/products/inventory-adjustments/{doc1_id}")
    doc_data = doc.json()
    assert doc_data["status"] == "POSTED"


async def test_two_adj_conc_post(client):

    adj_data = {"reason": "123", "items": [{"product_id": 1, "quantity_delta": 10}]}

    response = await client.post("/api/v1/products/inventory-adjustments", json=adj_data)
    assert response.status_code == 201
    data = response.json()
    doc_id = data["id"]

    responses = await asyncio.gather(
        client.post(f"/api/v1/products/inventory-adjustments/{doc_id}/post"),
        client.post(f"/api/v1/products/inventory-adjustments/{doc_id}/post"),
    )

    successful_responses = [response for response in responses if response.status_code == 200]
    # Only one should succeed
    assert len(successful_responses) == 1

async def test_two_adj_conc_post_and_cancel(client):

    adj_data = {"reason": "123", "items": [{"product_id": 1, "quantity_delta": 10}]}

    response = await client.post("/api/v1/products/inventory-adjustments", json=adj_data)
    assert response.status_code == 201
    data = response.json()
    doc_id = data["id"]

    responses = await asyncio.gather(
        client.post(f"/api/v1/products/inventory-adjustments/{doc_id}/post"),
        client.post(f"/api/v1/products/inventory-adjustments/{doc_id}/cancel"),
    )

    successful_responses = [response for response in responses if response.status_code == 200]
    # Only one should succeed
    assert len(successful_responses) == 1

    doc = await client.get(f"/api/v1/products/inventory-adjustments/{doc_id}")
    doc_data = doc.json()
    assert doc_data["status"] in ["POSTED", "CANCELLED"]


async def test_two_multi_adj_conc_post(client):

    adj_data1 = {
        "reason": "123",
        "items": [{"product_id": 1, "quantity_delta": 10}, {"product_id": 3, "quantity_delta": -5}],
    }

    adj_data2 = {
        "reason": "123",
        "items": [{"product_id": 2, "quantity_delta": 20}, {"product_id": 1, "quantity_delta": -15}],
    }

    # product before doc
    prod = await client.get("/api/v1/products/1")
    prod_data = prod.json()
    total_changes = -5

    response = await client.post("/api/v1/products/inventory-adjustments", json=adj_data1)
    assert response.status_code == 201
    data = response.json()
    doc_id1 = data["id"]

    response = await client.post("/api/v1/products/inventory-adjustments", json=adj_data2)
    assert response.status_code == 201
    data = response.json()
    doc_id2 = data["id"]

    responses = await asyncio.gather(
        client.post(f"/api/v1/products/inventory-adjustments/{doc_id1}/post"),
        client.post(f"/api/v1/products/inventory-adjustments/{doc_id2}/post"),
    )

    successful_responses = [response for response in responses if response.status_code == 200]
    # Both should succeed
    assert len(successful_responses) == 2

    # product after doc
    prod2 = await client.get("/api/v1/products/1")
    prod2_data = prod2.json()

    assert prod_data["quantity"] + total_changes == prod2_data["quantity"]
