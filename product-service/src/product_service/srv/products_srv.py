import product_service.domain.exceptions.products_exceptions as pe
from product_service.repos.products_repo import ProductsRepo
import product_service.schemas.products as ps


class ProductsService:
    def __init__(self, products_repository: ProductsRepo):
        self.products_repository = products_repository

    async def get_product_by_id(self, product_id: int):
        return await self.products_repository.get_product_by_id(product_id)

    async def get_all_products(self, filter: ps.ProductFilter):
        return await self.products_repository.get_all_products(filter)

    async def create_product(self, product_data: ps.ProductCreate):
        return await self.products_repository.create_product(product_data)

    async def update_product(self, product_id: int, product_data: ps.ProductUpdate):
        data = product_data.model_dump(exclude_unset=True)
        if not data:
            raise pe.InvalidProductData("No fields provided for update")
        return await self.products_repository.update_product(product_id, data)

    async def delete_product(self, product_id: int):
        await self.products_repository.delete_product(product_id)

    async def reserve_product(self, product_id: int, payload: ps.ProductReserve):
        if payload.quantity <= 0:
            raise pe.InvalidProductData("Quantity to reserve must be greater than zero")
        return await self.products_repository.reserve_product(product_id, payload)

    async def create_adjustment(self, payload: ps.AdjustmentCreate):
        if not payload.items:
            raise pe.InvalidProductData("No items provided")
        errors = []
        for item in payload.items:
            if item.quantity_delta == 0:
                errors.append(f"Product ID {item.product_id} has zero quantity")
        if errors:
            raise pe.InvalidProductData("\n".join(errors))
        return await self.products_repository.create_adjustment(payload)

    async def get_adjustment(self, adjustment_id: int):
        return await self.products_repository.get_adjustment(adjustment_id)

    async def post_adjustment(self, adjustment_id: int):
        return await self.products_repository.post_adjustment(adjustment_id)

    async def cancel_adjustment(self, adjustment_id: int):
        return await self.products_repository.cancel_adjustment(adjustment_id)
