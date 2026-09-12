import product_service.db.models.products as pm
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import DBAPIError, IntegrityError
import product_service.schemas.products as ps
import product_service.domain.exceptions.products_exceptions as pe


class ProductsRepo:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_product_by_id(self, product_id: int):
        res = await self.db.get(pm.Products, product_id)
        if not res or res.is_active is False:
            raise pe.ProductNotFound("Product not found")
        return res

    async def create_product(self, product_data: ps.ProductCreate):
        new_product = pm.Products(**product_data.model_dump())
        self.db.add(new_product)
        try:
            await self.db.commit()
        except IntegrityError as e:
            await self.db.rollback()
            orig = e.orig  # Access the original exception
            if "already exists" in str(orig):
                raise pe.ProductAlreadyExists("Product already exists")
            else:
                raise pe.InvalidProductData("Invalid product data", str(orig))
        return new_product

    async def update_product(self, product_id: int, update_data: dict):
        product = await self.get_product_by_id(product_id)
        if not product:
            raise pe.ProductNotFound("Product not found")
        for key, value in update_data.items():
            setattr(product, key, value)
        try:
            await self.db.commit()
            await self.db.refresh(product)
            return product
        except IntegrityError as e:
            await self.db.rollback()
            orig = e.orig  # Access the original exception
            raise pe.InvalidProductData("Invalid product data", str(orig))

    async def delete_product(self, product_id: int):
        product = await self.get_product_by_id(product_id)
        if not product:
            raise pe.ProductNotFound("Product not found")
        if product.is_active is False:
            raise pe.InvalidProductData("Product is already deleted")
        product.is_active = False
        await self.db.commit()

    async def get_all_products(self, filter: ps.ProductFilter):

        query = select(pm.Products)
        if filter.is_active is not None:
            query = query.where(pm.Products.is_active == filter.is_active)
        query = query.offset((filter.page - 1) * filter.limit).limit(filter.limit)
        query = query.order_by(pm.Products.created_at.desc(), pm.Products.id)

        result = await self.db.execute(query)
        return result.scalars().all()

    async def reserve_product(self, product_id: int, payload: ps.ProductReserve):
        stmt = select(pm.Products).where(pm.Products.id == product_id).with_for_update()
        product = await self.db.scalar(stmt)
        if not product or product.is_active is False:
            await self.db.rollback()
            raise pe.ProductNotFound("Product not found")
        quantity = payload.quantity
        if product.quantity < quantity:
            error = (
                f"Insufficient quantity available for reservation. "
                f"Product ID: {product_id}, Requested: {quantity}, Available: {product.quantity}"
            )
            await self.db.rollback()
            raise pe.InsufficientQuantity(error)
        product.reserved += quantity
        product.quantity -= quantity
        await self.db.commit()
        await self.db.refresh(product)
        return product

    async def create_adjustment(self, payload: ps.AdjustmentItemCreate):

        prod_ids = [item.product_id for item in payload.items]
        stmt = select(pm.Products.id).where(pm.Products.id.in_(prod_ids) & pm.Products.is_active)
        prods = await self.db.execute(stmt)
        diff = set(prod_ids).difference(set(prods.scalars().all()))
        if diff:
            raise pe.ProductNotFound(f"One or more product not found. Missing: {diff}")

        doc = pm.InventoryAdjustments(
            **payload.model_dump(exclude={"items"}), status=pm.DocumentStatusEnum.PENDING
        )
        items = [pm.InventoryAdjustmentsItems(**item.model_dump()) for item in payload.items]
        doc.items = items

        self.db.add(doc)
        await self.db.commit()
        await self.db.refresh(doc)

        return {
            "id": doc.id,
            "status": doc.status,
            "reason": doc.reason,
            "created_at": doc.created_at,
            "updated_at": doc.updated_at,
            "items": [{"product_id": item.id, "quantity_delta": item.quantity_delta} for item in items],
        }

    async def get_adjustment(self, id: int):
        stmt = (
            select(pm.InventoryAdjustments)
            .options(selectinload(pm.InventoryAdjustments.items))
            .where(pm.InventoryAdjustments.id == id)
        )
        doc = await self.db.scalar(stmt)

        if not doc:
            raise pe.DocumentNotFound("Inventory adjustment not found")
        return {
            "id": doc.id,
            "status": doc.status,
            "reason": doc.reason,
            "created_at": doc.created_at,
            "updated_at": doc.updated_at,
            "items": [{"product_id": item.id, "quantity_delta": item.quantity_delta} for item in doc.items],
        }

    async def post_adjustment(self, id: int):
        try:
            adj_res = await self.db.execute(
                select(pm.InventoryAdjustments)
                .where(pm.InventoryAdjustments.id == id)
                .options(selectinload(pm.InventoryAdjustments.items))
                .with_for_update(nowait=True)
            )

            adj_doc = adj_res.scalar()
            if not adj_doc:
                await self.db.rollback()
                raise pe.DocumentNotFound("Inventory adjustment not found")

            if adj_doc.status != pm.DocumentStatusEnum.PENDING:
                status = adj_doc.status
                await self.db.rollback()
                raise pe.InvalidDocumentStatus(f"""
                    Inventory adjustment current status is {status}.
                    Must be PENDING to post""")

            gr_items = {}
            for item in adj_doc.items:
                gr_items[item.product_id] = gr_items.setdefault(item.product_id, 0) + item.quantity_delta

            products_stmt = (
                select(pm.Products)
                .where(pm.Products.id.in_(list(gr_items.keys())))
                .order_by(pm.Products.id)
                .with_for_update(of=[pm.Products])
            )

            products_res = await self.db.execute(products_stmt)
            products = products_res.scalars().all()

            errors = []

            for prod in products:
                prod.quantity += gr_items.get(prod.id)
                if prod.quantity < 0:
                    errors.append(f"Product ID {prod.id} has not enough quantity to adjust")

            if errors:
                await self.db.rollback()
                raise pe.InsufficientQuantity("\n".join(errors))

            adj_doc.status = pm.DocumentStatusEnum.POSTED
            await self.db.commit()

        except DBAPIError:
            await self.db.rollback()
            raise pe.DataLockError("The inventory adjustment is locked by another process")

    async def cancel_adjustment(self, id: int):

        try:
            adj_res = await self.db.execute(
                select(pm.InventoryAdjustments)
                .where(pm.InventoryAdjustments.id == id)
                .with_for_update(nowait=True)
            )
            adj_doc = adj_res.scalar()
            if not adj_doc:
                await self.db.rollback()
                raise pe.DocumentNotFound("Inventory adjustment not found")

            if adj_doc.status != pm.DocumentStatusEnum.PENDING:
                status = adj_doc.status
                await self.db.rollback()
                raise pe.InvalidDocumentStatus(f"""
                    Inventory adjustment current status is {status}.
                    Must be PENDING to cancel""")

            adj_doc.status = pm.DocumentStatusEnum.CANCELLED
            await self.db.commit()

        except DBAPIError:
            await self.db.rollback()
            raise pe.DataLockError("The inventory adjustment is locked by another process")
