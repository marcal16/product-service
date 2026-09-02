import pytest

product_data = {
    "name": "Test Product",
    "price": 19.99,
    "currency": "USD",
    "sku": "TESTSKU123",
    "quantity": 10
}

@pytest.mark.parametrize("product_data", [product_data])
async def test_create_product(client, product_data):
    response = await client.post("/api/v1/products", json=product_data)
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == product_data["name"]
    assert data["price"] == str(product_data["price"]) # Decimal values are often returned as strings in JSON
    assert "id" in data

@pytest.mark.parametrize("product_data", [product_data])
async def test_get_product(client, product_data):
    # First, create a product to retrieve
    create_response = await client.post("/api/v1/products", json=product_data)
    product_id = create_response.json()["id"]

    # Now, retrieve the product
    response = await client.get(f"/api/v1/products/{product_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == product_id
    assert data["name"] == product_data["name"]

async def test_get_nonexistent_product(client):
    response = await client.get("/api/v1/products/999999")  # Assuming this ID does not exist
    assert response.status_code == 404
    data = response.json()
    assert data["detail"] == "Product not found"

@pytest.mark.parametrize("product_data", [product_data])
async def test_delete_product(client, product_data):
    # First, create a product to delete
    create_response = await client.post("/api/v1/products", json=product_data)
    product_id = create_response.json()["id"]

    # Now, delete the product
    delete_response = await client.delete(f"/api/v1/products/{product_id}")
    assert delete_response.status_code == 204

    # Try to retrieve the deleted product
    get_response = await client.get(f"/api/v1/products/{product_id}")
    assert get_response.status_code == 404
    data = get_response.json()
    assert data["detail"] == "Product not found"

@pytest.mark.parametrize("product_data", [product_data])
async def test_update_product(client, product_data):
    # First, create a product to update
    create_response = await client.post("/api/v1/products", json=product_data)
    product_id = create_response.json()["id"]

    # Update the product's price
    updated_data = {"price": 29.99}
    update_response = await client.put(f"/api/v1/products/{product_id}", json=updated_data)
    assert update_response.status_code == 200
    data = update_response.json()
    assert data["price"] == str(updated_data["price"])

    # Retrieve the updated product to verify changes
    get_response = await client.get(f"/api/v1/products/{product_id}")
    assert get_response.status_code == 200
    data = get_response.json()
    assert data["price"] == str(updated_data["price"])

@pytest.mark.parametrize("product_data", [product_data])
async def test_duplicate_sku(client, product_data):
    # Create the first product
    response1 = await client.post("/api/v1/products", json=product_data)
    assert response1.status_code == 201

    # Attempt to create a second product with the same SKU
    response2 = await client.post("/api/v1/products", json=product_data)
    assert response2.status_code == 400
    data = response2.json()
    assert data["detail"] == "Product already exists"

@pytest.mark.parametrize("product_data", [product_data])
async def test_invalid_price(client, product_data):
    # Set an invalid price (negative value)
    product_data_wrong_price = product_data.copy()
    product_data_wrong_price["price"] = -10.00
    response = await client.post("/api/v1/products", json=product_data_wrong_price)
    assert response.status_code == 422  # Unprocessable Entity
    data = response.json()
    assert "check_price_positive" in data["detail"]  # Check that the error is related to the price field

@pytest.mark.parametrize("product_data", [product_data])
async def test_invalid_currency(client, product_data):
    # Set an invalid currency code
    product_data_wrong_currency = product_data.copy()
    product_data_wrong_currency["currency"] = "INVALID"
    response = await client.post("/api/v1/products", json=product_data_wrong_currency)
    assert response.status_code == 422  # Unprocessable Entity
    data = response.json()
    assert "currency" in data["detail"][0]["loc"]  # Check that the error is related to the currency field

@pytest.mark.parametrize("product_data", [product_data])
async def test_invalid_quantity(client, product_data):
    # Set an invalid quantity (negative value)
    product_data_wrong_quantity = product_data.copy()
    product_data_wrong_quantity["quantity"] = -5
    response = await client.post("/api/v1/products", json=product_data_wrong_quantity)
    assert response.status_code == 422  # Unprocessable Entity
    data = response.json()
    assert "check_quantity_non_negative" in data["detail"]  # Check that the error is related to the quantity field
