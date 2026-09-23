from pydantic import BaseModel, ConfigDict, Field
from datetime import datetime

# Responses


class InventoryReportResponse(BaseModel):
    product_id: int
    name: str
    sku: str
    quantity: int
    reserved: int
    total_stock: int

    model_config = ConfigDict(from_attributes=True)


class OrdersReportResponse(BaseModel):
    total: int
    pending: int
    confirmed: int
    cancelled: int


class ProductOrderedReportResponse(BaseModel):
    product_id: int
    sku: str
    name: str
    ordered_quantity: int


# Filters
class BaseFilter(BaseModel):
    page: int | None = Field(default=1, ge=1)
    limit: int | None = Field(default=10, ge=1)


class InventoryReportFilter(BaseFilter):
    is_active: bool | None = None
    available_below: int | None = Field(default=None, ge=1)


class OrdersReportFilter(BaseModel):
    created_from: datetime | None = None
    created_to: datetime | None = None


class TopProductsReportFilter(BaseFilter):
    pass
