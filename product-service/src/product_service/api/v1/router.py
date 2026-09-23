from fastapi import APIRouter
from .products_api import router as products_router
from .orders_api import router as orders_router
from .health_api import router as health_router
from .reports_api import router as reports_router

router = APIRouter(prefix="/api/v1", tags=["v1"])
router.include_router(products_router, prefix="/products", tags=["products"])
# AC-103
router.include_router(orders_router, prefix="/orders", tags=["orders"])

router.include_router(health_router, prefix="/health", tags=["health"])

router.include_router(reports_router, prefix="/reports", tags=["reports"])
