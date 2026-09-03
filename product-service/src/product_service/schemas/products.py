from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field
from product_service.db.models.products import CurrencyEnum
from decimal import Decimal

#post
class ProductCreate(BaseModel):
    name: str
    description: str | None = None
    price: Decimal
    currency: CurrencyEnum
    sku: str
    quantity: int

#update
class ProductUpdate(BaseModel):
    name: str | None = None
    price: Decimal | None = None
    currency: CurrencyEnum | None = None
    sku: str | None = None
    quantity: int | None = None

#reserve
class ProductReserve(BaseModel):
    quantity: int

#response
class ProductResponse(BaseModel):
    id: int
    name: str
    description: str | None = None
    price: Decimal
    currency: CurrencyEnum
    sku: str
    quantity: int
    reserved: int
    created_at: datetime
    updated_at: datetime
    is_active: bool

    model_config = ConfigDict(from_attributes=True)

class ProductReservationResponse(BaseModel):
    sku: str
    quantity: int
    reserved: int
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

#filter
class BaseFilter(BaseModel):
    page: int | None = Field(default=1, ge=1)
    limit: int | None = Field(default=10, ge=1)

class ProductFilter(BaseFilter):
    is_active: bool | None = None