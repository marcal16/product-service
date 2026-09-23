from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
import product_service.schemas.reports as rs
import product_service.db.models.products as pm


class ReportsRepo:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def inventory_report(self, filters: rs.InventoryReportFilter):

        query = select(
            pm.Products.id.label("product_id"),
            pm.Products.name,
            pm.Products.sku,
            pm.Products.quantity,
            pm.Products.reserved,
            (pm.Products.quantity + pm.Products.reserved).label("total_stock"),
        )

        if filters.is_active:
            query = query.where(pm.Products.is_active == filters.is_active)

        if filters.available_below:
            query = query.where(pm.Products.quantity < filters.available_below)

        query = query.offset((filters.page - 1) * filters.limit).limit(filters.limit)
        query = query.order_by(pm.Products.id)

        res = await self.db.execute(query)
        return res.mappings().all()

    async def orders_statistics(self, filters: rs.OrdersReportFilter):

        all_orders = select(pm.Orders.id, pm.Orders.status)

        if filters.created_from:
            all_orders = all_orders.where(pm.Orders.created_at >= filters.created_from)
        if filters.created_to:
            all_orders = all_orders.where(pm.Orders.created_at <= filters.created_to)

        all_orders = all_orders.cte("all_orders")

        stmt = select(
            func.count().label("total"),
            func.count().filter(all_orders.c.status == "PENDING").label("pending"),
            func.count().filter(all_orders.c.status == "CONFIRMED").label("confirmed"),
            func.count().filter(all_orders.c.status == "CANCELLED").label("cancelled"),
        ).select_from(all_orders)

        res = await self.db.execute(stmt)
        return res.one()

    async def top_ordered_products(self, filters):

        cte = (
            select(pm.OrderItems.product_id, func.sum(pm.OrderItems.quantity).label("ordered_quantity"))
            .group_by(pm.OrderItems.product_id)
            .order_by(func.sum(pm.OrderItems.quantity).desc(), pm.OrderItems.product_id)
            .limit(filters.limit)
            .cte("cte")
        )

        stmt = (
            select(cte.c.product_id, pm.Products.sku, pm.Products.name, cte.c.ordered_quantity)
            .join(pm.Products, cte.c.product_id == pm.Products.id)
            .order_by(cte.c.ordered_quantity.desc(), cte.c.product_id)
        ).select_from(cte)

        res = await self.db.execute(stmt)
        return res.mappings().all()
