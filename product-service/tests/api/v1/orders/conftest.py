import pytest
from product_service.dependencies.session import get_session
from product_service.main import app
from httpx2 import AsyncClient, ASGITransport
import sqlalchemy as sa

from tests.conftest import get_test_session, test_engine


async def seed(conn):

    # Insert sample products for orders
    await conn.execute(
        sa.text(
            """
            INSERT INTO products (id, name, description, price, currency, sku, quantity, is_active) VALUES
            (1, 'Product 1', 'Description 1', 10.99, 'USD', 'SKU001', 100, true),
            (2, 'Product 2', 'Description 2', 20.99, 'USD', 'SKU002', 50, true),
            (3, 'Product 3', 'Description 3', 40.99, 'USD', 'SKU003', 70, true)
            """
        )
    )

@pytest.fixture(scope='function')
async def client():
        
    app.dependency_overrides[get_session] = get_test_session
    transport = ASGITransport(app=app)

    async with test_engine.begin() as conn:
        await seed(conn)

    try:
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            yield client
    finally:
        app.dependency_overrides.clear()
        async with test_engine.begin() as conn:
            await conn.execute(sa.text("TRUNCATE TABLE products, orders, order_items RESTART IDENTITY CASCADE;"))