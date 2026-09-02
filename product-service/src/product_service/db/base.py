from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from product_service.core.settings import settings

async_engine = create_async_engine(settings.db_src)
AsyncSessionLocal = async_sessionmaker(bind=async_engine, expire_on_commit=False)

class Base(DeclarativeBase):
    pass