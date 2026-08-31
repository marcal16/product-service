from product_service.db.models.products import Products
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError
import product_service.schemas.products as ps
import product_service.domain.exceptions.products_exceptions as pe

class ProductsRepo:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_product_by_id(self, product_id: int):
        res = await self.db.get(Products, product_id)
        if not res or res.is_active is False:
            raise pe.ProductNotFound("Product not found")
        return res

    async def create_product(self, product_data: ps.ProductCreate):
        new_product = Products(**product_data.model_dump())
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

        query = select(Products)
        if filter.is_active is not None:
            query = query.where(Products.is_active == filter.is_active)
        query = query.offset((filter.page - 1) * filter.limit).limit(filter.limit)
        
        result = await self.db.execute(query)
        return result.scalars().all()