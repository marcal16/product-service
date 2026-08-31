from datetime import datetime

from pydantic import BaseModel, ConfigDict
from product_service.db.models.products import CurrencyEnum
from decimal import Decimal

#post
class ProductCreate(BaseModel):
    name: str
    price: Decimal
    currency: CurrencyEnum
    sku: str
    quantity: Decimal

#update
class ProductUpdate(BaseModel):
    name: str | None = None
    price: Decimal | None = None
    currency: CurrencyEnum | None = None
    sku: str | None = None
    quantity: Decimal | None = None

#repone
class ProductResponse(BaseModel):
    id: int
    name: str
    price: Decimal
    currency: CurrencyEnum
    sku: str
    quantity: Decimal
    created_at: datetime
    updated_at: datetime
    is_active: bool

    model_config = ConfigDict(from_attributes=True)

#filter
class BaseFilter(BaseModel):
    page: int | None = 1
    limit: int | None = 10

class ProductFilter(BaseFilter):
    is_active: bool | None = None