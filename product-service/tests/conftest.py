import pytest, os
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from product_service.db.base import Base

DB_URL = os.getenv("TEST_DB_SRC", "postgresql+asyncpg://postgres:123@localhost:5432/test_products_service")

test_engine =  create_async_engine(DB_URL, echo=True)
async_session = async_sessionmaker(test_engine, expire_on_commit=False)

async def get_test_session():
    async with async_session() as session:
        yield session

@pytest.fixture(scope='session', autouse=True)
async def setup_database():
    # Create the database tables before each test
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    # Drop the database tables after each test
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)