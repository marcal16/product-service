import product_service.schemas.orders as ors
import product_service.domain.exceptions.products_exceptions as pe
from product_service.repos.orders_repo import OrdersRepo

class OrdersService():

    def __init__(self, products_repository: OrdersRepo):
        self.products_repository = products_repository

    #AC-103
    async def create_order(self, order_data: ors.OrderCreate):
        if not order_data.items:
            raise pe.InvalidOrderData("Order must contain at least one item")
        if any(item.quantity <= 0 for item in order_data.items):
            raise pe.InvalidOrderData("All order items must have a quantity greater than zero")
        return await self.products_repository.create_order(order_data)