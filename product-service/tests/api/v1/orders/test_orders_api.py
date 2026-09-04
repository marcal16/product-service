import asyncio

async def test_create_order_one_position(client):

    order_data = {
        "items": [
            {
                "product_id": 1,
                "quantity": 20
            }
        ]
    }

    response = await client.post("/api/v1/orders", json=order_data)
    assert response.status_code == 201
    data = response.json()
    assert data["status"] == "PENDING"
    assert len(data["items"]) == 1

async def test_create_order_multiple_positions(client):
    
    order_data = {
        "items": [
            {
                "product_id": 1,
                "quantity": 10
            },
            {
                "product_id": 2,
                "quantity": 5
            }
        ]
    }

    response = await client.post("/api/v1/orders", json=order_data)
    assert response.status_code == 201
    data = response.json()
    assert data["status"] == "PENDING"
    assert len(data["items"]) == 2

async def test_create_order_with_same_id_position(client):
    
    order_data = {
        "items": [
            {
                "product_id": 1,
                "quantity": 10
            },
            {
                "product_id": 1,
                "quantity": 5
            }
        ]
    }

    response = await client.post("/api/v1/orders", json=order_data)
    assert response.status_code == 201
    data = response.json()
    assert len(data["items"]) == 1
    assert data["items"][0]["quantity"] == 15  # Quantities should be summed up

async def test_create_empty_order(client):
    
    order_data = {
        "items": []
    }

    response = await client.post("/api/v1/orders", json=order_data)
    assert response.status_code == 422  # Unprocessable Entity
    data = response.json()
    assert "Order must contain at least one item" in data['detail']

async def test_create_order_with_zero_quantity(client):
    
    order_data = {
        "items": [
            {
                "product_id": 1,
                "quantity": 0
            }
        ]
    }

    response = await client.post("/api/v1/orders", json=order_data)
    assert response.status_code == 422  # Unprocessable Entity
    data = response.json()
    assert "All order items must have a quantity greater than zero" in data['detail']

async def test_create_order_with_nonexisting_product(client):
    
    order_data = {
        "items": [
            {
                "product_id": 999,  # Assuming this product ID does not exist
                "quantity": 1
            }
        ]
    }

    response = await client.post("/api/v1/orders", json=order_data)
    assert response.status_code == 404  # Not Found
    data = response.json()
    assert "Order has product that does not exist" in data['detail']

async def test_create_order_with_insufficient_quantity(client):
    
    order_data = {
        "items": [
            {
                "product_id": 1,
                "quantity": 10  # This is assumed to be within available stock
            },
            {
                "product_id": 2,
                "quantity": 200  # Assuming this exceeds available stock
            }
        ]
    }

    response = await client.post("/api/v1/orders", json=order_data)
    assert response.status_code == 400  # Bad Request
    data = response.json()
    assert "Insufficient product quantity" in data['detail']
    assert "product ID 2" in data['detail']  # Ensure the error message mentions the specific product with insufficient quantity

async def test_concurrent_order_creation(client):

    order_data_1 = {
        "items": [
            {
                "product_id": 1,
                "quantity": 40
            },
            {
                "product_id": 2,
                "quantity": 30
            }
        ]
    }

    order_data_2 = {
        "items": [
            {
                "product_id": 2,
                "quantity": 40
            }
        ]
    }

    # Simulate concurrent requests
    responses = await asyncio.gather(
        client.post("/api/v1/orders", json=order_data_1),
        client.post("/api/v1/orders", json=order_data_2)
    )

    successful_responses = [response for response in responses if response.status_code == 201]
    assert len(successful_responses) == 1  # Only one should succeed due to stock limitations
    assert any(response.status_code == 400 for response in responses)  # The other should fail due to insufficient quantity
