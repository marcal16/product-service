from sqlalchemy import select, true
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import DBAPIError, IntegrityError
from product_service.db.models.products import Products, Orders, OrderItems, OrderStatusEnum
import product_service.schemas.orders as ors
import product_service.domain.exceptions.products_exceptions as pe


class OrdersRepo:
    def __init__(self, db: AsyncSession):
        self.db = db

    # AC-103
    async def create_order(self, order_data: ors.OrderCreate):

        products = {}
        for item in order_data.items:
            products[item.product_id] = products.get(item.product_id, 0) + item.quantity

        db_products = await self.db.execute(
            select(Products)
            .where(Products.id.in_(products.keys()) & Products.is_active.is_(true()))
            .order_by(Products.id)
            .with_for_update()
        )
        db_products = db_products.scalars().all()

        if len(db_products) != len(products):
            await self.db.rollback()
            raise pe.ProductNotFound("One or more products in the order do not exist")

        errors = []
        for db_product in db_products:
            requested_quantity = products[db_product.id]
            if db_product.quantity < requested_quantity:
                error = f"Insufficient quantity available for product ID {db_product.id}. "
                error += f"Requested: {requested_quantity}, Available: {db_product.quantity}"
                errors.append(error)
        if errors:
            await self.db.rollback()
            raise pe.InsufficientQuantity("<br/>".join(errors))

        new_order = Orders(status=OrderStatusEnum.PENDING)
        self.db.add(new_order)
        await self.db.flush()  # Ensure new_order.id is available
        order_items = []

        for db_product in db_products:
            requested_quantity = products[db_product.id]
            db_product.quantity -= requested_quantity
            db_product.reserved += requested_quantity
            order_item = OrderItems(
                order_id=new_order.id, product_id=db_product.id, quantity=requested_quantity
            )
            order_items.append(order_item)
        self.db.add_all(order_items)

        await self.db.commit()
        await self.db.refresh(new_order)  # Update order created_at and updated_at dates
        return {
            "id": new_order.id,
            "status": new_order.status,
            "items": [{"product_id": item.product_id, "quantity": item.quantity} for item in order_items],
            "created_at": new_order.created_at,
        }

    async def cancel_order(self, order_id: int):

        try:
            order_res = await self.db.execute(
                select(Orders).where(Orders.id == order_id).with_for_update(nowait=True)
            )
            order = order_res.scalar()
            if not order:
                await self.db.rollback()
                raise pe.OrderNotFound("Order not found")

            if order.status != OrderStatusEnum.PENDING:
                order_status = order.status
                await self.db.rollback()
                raise pe.InvalidOrderStatus(
                    f"Order status is {order_status}. \
                                            Only orders with status PENDING can be cancelled"
                )

            products_stmt = (
                select(Products, OrderItems)
                .join(OrderItems, OrderItems.product_id == Products.id)
                .where(OrderItems.order_id == order_id)
                .order_by(Products.id)
                .with_for_update(of=[Products])
            )
            products = await self.db.execute(products_stmt)

            for prod, item_line in products:
                prod.reserved -= item_line.quantity
                prod.quantity += item_line.quantity

            order.status = OrderStatusEnum.CANCELLED
            await self.db.commit()
            await self.db.refresh(order)
            return order

        except DBAPIError:
            await self.db.rollback()
            raise pe.OrderLockError("The order is locked by another process")
        except IntegrityError:
            await self.db.rollback()
            raise pe.InvalidProductData("Programming error, quantity cannot be lower than zero")

    async def confirm_order(self, order_id: int):

        try:
            order_res = await self.db.execute(
                select(Orders).where(Orders.id == order_id).with_for_update(nowait=True)
            )
            order = order_res.scalar()
            if not order:
                await self.db.rollback()
                raise pe.OrderNotFound("Order not found")

            if order.status != OrderStatusEnum.PENDING:
                order_status = order.status
                await self.db.rollback()
                raise pe.InvalidOrderStatus(
                    f"Order status is {order_status}. \
                    Only orders with status PENDING can be confirmed"
                )

            products_stmt = (
                select(Products, OrderItems)
                .join(OrderItems, OrderItems.product_id == Products.id)
                .where(OrderItems.order_id == order_id)
                .order_by(Products.id)
                .with_for_update(of=[Products])
            )
            products = await self.db.execute(products_stmt)

            for prod, item_line in products:
                if prod.reserved < item_line.quantity:
                    error_mes = f"Product with ID {prod.id} has not enough reserved amount"
                    await self.db.rollback()
                    raise pe.InvalidProductData(error_mes)
                prod.reserved -= item_line.quantity

            order.status = OrderStatusEnum.CONFIRMED
            await self.db.commit()
            await self.db.refresh(order)
            return order

        except DBAPIError:
            await self.db.rollback()
            raise pe.OrderLockError("The order is locked by another process")
        except IntegrityError:
            await self.db.rollback()
            raise pe.InvalidProductData("Programming error, quantity cannot be lower than zero")
