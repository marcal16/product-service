import pytest, asyncio

product_data = {
    "name": "Test Product",
    "price": 19.99,
    "currency": "USD",
    "sku": "TESTSKU123",
    "quantity": 10
}

#AC-102
@pytest.mark.parametrize("product_data", [product_data])
async def test_reserv_1_item(client, product_data):
    # Create a product to reserve
    create_response = await client.post("/api/v1/products", json=product_data)
    product_id = create_response.json()["id"]

    # Reserve 1 item of the product
    payload = {"quantity": 1}
    reserve_response = await client.post(f"/api/v1/products/{product_id}/reserve", json=payload)
    assert reserve_response.status_code == 200
    data = reserve_response.json()
    assert data["reserved"] == 1
    assert data["quantity"] == product_data["quantity"] - 1  # Check that the quantity has decreased by 1

@pytest.mark.parametrize("product_data", [product_data])
async def test_reserv_all_stock(client, product_data):
    # Create a product to reserve
    create_response = await client.post("/api/v1/products", json=product_data)
    product_id = create_response.json()["id"]

    # Reserve all stock of the product
    payload = {"quantity": product_data["quantity"]}
    reserve_response = await client.post(f"/api/v1/products/{product_id}/reserve", json=payload)
    assert reserve_response.status_code == 200
    data = reserve_response.json()
    assert data["reserved"] == product_data["quantity"]
    assert data["quantity"] == 0  # Check that the quantity has decreased by the reserved amount

@pytest.mark.parametrize("product_data", [product_data])
async def test_reserv_inactive_product(client, product_data):
    # Create a product to reserve
    create_response = await client.post("/api/v1/products", json=product_data)
    product_id = create_response.json()["id"]

    # Make it inactive
    await client.delete(f"/api/v1/products/{product_id}")

    # Try to reserve the inactive product
    payload = {"quantity": 1}
    reserve_response = await client.post(f"/api/v1/products/{product_id}/reserve", json=payload)
    assert reserve_response.status_code == 404
    data = reserve_response.json()
    assert data["detail"] == "Product not found"

async def test_reserv_non_existing_product(client):

    payload = {"quantity": 1}
    reserve_response = await client.post(f"/api/v1/products/{3}/reserve", json=payload)
    assert reserve_response.status_code == 404
    data = reserve_response.json()
    assert data["detail"] == "Product not found"

async def test_reserv_invalid_quantity(client):

    payload = {"quantity": -1}
    reserve_response = await client.post(f"/api/v1/products/{3}/reserve", json=payload)
    assert reserve_response.status_code == 422
    data = reserve_response.json()
    assert data["detail"] == "Quantity to reserve must be greater than zero"

@pytest.mark.parametrize("product_data", [product_data])
async def test_reserv_insufficient_quantity(client, product_data):
    # Create a product to reserve
    create_response = await client.post("/api/v1/products", json=product_data)
    product_id = create_response.json()["id"]
    quantity = product_data["quantity"] + 1  # Request more than available
    # Reserve all stock of the product
    payload = {"quantity": quantity}
    reserve_response = await client.post(f"/api/v1/products/{product_id}/reserve", json=payload)

    assert reserve_response.status_code == 400
    data = reserve_response.json()
    assert "Insufficient quantity available for reservation" in data["detail"]

    record = await client.get(f"/api/v1/products/{product_id}")
    record_data = record.json()
    assert record_data["reserved"] == 0  # Ensure reserved count is still 0
    assert record_data["quantity"] == product_data["quantity"]  # Ensure quantity is unchanged

@pytest.mark.parametrize("product_data", [product_data])
async def test_reserv_concurrent_requests(client, product_data):
    # Create a product to reserve
    create_response = await client.post("/api/v1/products", json=product_data)
    product_id = create_response.json()["id"]

    # Define the number of concurrent requests and the quantity to reserve
    concurrent_requests = 2
    reserve_quantity = 7  # Each request will try to reserve 3 items

    # Create a list of tasks for concurrent reservation requests
    tasks = [
        client.post(f"/api/v1/products/{product_id}/reserve", json={"quantity": reserve_quantity})
        for _ in range(concurrent_requests)
    ]

    # Execute the tasks concurrently
    responses = await asyncio.gather(*tasks)

    # Check the responses and ensure that only the allowed number of reservations succeeded
    successful_reservations = sum(1 for response in responses if response.status_code == 200)
    assert successful_reservations == 1

    # Fetch the product record to check the final reserved count and quantity
    record_response = await client.get(f"/api/v1/products/{product_id}")
    record_data = record_response.json()
    assert record_data["reserved"] == successful_reservations * reserve_quantity
    assert record_data["quantity"] == product_data["quantity"] - (successful_reservations * reserve_quantity)