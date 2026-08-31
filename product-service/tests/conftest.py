import pytest
from product_service.main import app
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from product_service.core.settings import settings
from product_service.db.base import Base
from product_service.dependencies.session import get_session
from httpx2 import AsyncClient, ASGITransport

test_engine =  create_async_engine(settings.test_db_src, echo=True)
async_session = async_sessionmaker(test_engine, expire_on_commit=False)

async def get_test_session():
    async with async_session() as session:
        yield session

@pytest.fixture(scope='function')
async def client(setup_database):
    app.dependency_overrides[get_session] = get_test_session
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client
    app.dependency_overrides.clear()

@pytest.fixture(scope='function')
async def setup_database():
    # Create the database tables before each test
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    # Drop the database tables after each test
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)