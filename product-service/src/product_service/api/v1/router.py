from fastapi import APIRouter
from .products_api import router as products_router
from .orders_api import router as orders_router

router = APIRouter(prefix="/api/v1", tags=["v1"])
router.include_router(products_router, prefix="/products", tags=["products"])
#AC-103
router.include_router(orders_router, prefix="/orders", tags=["orders"])
