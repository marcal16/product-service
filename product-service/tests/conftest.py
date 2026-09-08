import pytest, os
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from product_service.core.settings import settings
#from product_service.db.base import Base

test_engine =  create_async_engine(settings.db_url, echo=True)
async_session = async_sessionmaker(test_engine, expire_on_commit=False)

async def get_test_session():
    async with async_session() as session:
        yield session

# Test base should accepts migrations now in advance
# @pytest.fixture(scope='session', autouse=True)
# async def setup_database():
#     # Create the database tables before each test
#     async with test_engine.begin() as conn:
#         await conn.run_sync(Base.metadata.create_all)
#     yield
#     # Drop the database tables after each test
#     async with test_engine.begin() as conn:
#         await conn.run_sync(Base.metadata.drop_all)