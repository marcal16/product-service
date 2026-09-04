from enum import Enum   
import sqlalchemy as sa
from sqlalchemy.orm import mapped_column, Mapped, relationship
from product_service.db.base import Base
from decimal import Decimal
from datetime import date, datetime

class CurrencyEnum(Enum):
    USD = "USD"
    EUR = "EUR"
    CAD = "CAD"

class Products(Base):
    __tablename__ = "products"

    id: Mapped[int] = mapped_column(sa.Integer, primary_key=True)
    name: Mapped[str] = mapped_column(sa.String(255), nullable=False)
    description: Mapped[str] = mapped_column(sa.Text, nullable=True)
    price: Mapped[Decimal] = mapped_column(sa.Numeric(15, 2), nullable=False)
    currency: Mapped[CurrencyEnum] = mapped_column(sa.Enum(CurrencyEnum, native_enum=True, create_type=True, name="currency_enum"), nullable=False)
    sku: Mapped[str] = mapped_column(sa.String(100), nullable=False, unique=True)
    #Changed to integer due to company's policy of not allowing float values for quantity
    quantity: Mapped[int] = mapped_column(sa.Integer, nullable=False)
    #AC-102
    reserved: Mapped[int] = mapped_column(sa.Integer, nullable=False, default=0, server_default="0")
    #AC-102
    is_active: Mapped[bool] = mapped_column(sa.Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(sa.DateTime, server_default=sa.func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(sa.DateTime, server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False)

    __table_args__ = (
        sa.CheckConstraint('price > 0', name='check_price_positive'),
        sa.CheckConstraint('quantity >= 0', name='check_quantity_non_negative'),
        sa.CheckConstraint("TRIM(name) <> ''", name='check_name_not_empty_ck'),
    )


#AC-103
class OrderStatusEnum(Enum):
    PENDING = "PENDING"
    CONFIRMED = "CONFIRMED"
    CANCELLED = "CANCELLED"

class Orders(Base):
    __tablename__ = "orders"

    id: Mapped[int] = mapped_column(sa.Integer, primary_key=True)
    status: Mapped[OrderStatusEnum] = mapped_column(sa.Enum(OrderStatusEnum, native_enum=True, create_type=True, name="order_status_enum"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(sa.DateTime, server_default=sa.func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(sa.DateTime, server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False)

    items: Mapped[list["OrderItems"]] = relationship("OrderItems", back_populates="order")

class OrderItems(Base):
    __tablename__ = "order_items"

    id: Mapped[int] = mapped_column(sa.Integer, primary_key=True)
    order_id: Mapped[int] = mapped_column(sa.Integer, sa.ForeignKey("orders.id"), nullable=False)
    product_id: Mapped[int] = mapped_column(sa.Integer, sa.ForeignKey("products.id"), nullable=False)
    quantity: Mapped[int] = mapped_column(sa.Integer, nullable=False)

    order: Mapped["Orders"] = relationship("Orders", back_populates="items")

    __table_args__ = (
        sa.CheckConstraint('quantity > 0', name='check_order_item_quantity_positive'),
    )