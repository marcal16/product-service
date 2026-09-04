import pytest
from product_service.dependencies.session import get_session
from product_service.main import app
from httpx2 import AsyncClient, ASGITransport
import sqlalchemy as sa

from tests.conftest import get_test_session, test_engine

@pytest.fixture(scope='function')
async def client():
        
    app.dependency_overrides[get_session] = get_test_session
    transport = ASGITransport(app=app)
    try:
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            yield client
    finally:
        app.dependency_overrides.clear()
        async with test_engine.begin() as conn:
            await conn.execute(sa.text("DELETE FROM products;"))