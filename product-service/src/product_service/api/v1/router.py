from fastapi import APIRouter
from .products_api import router as products_router

router = APIRouter(prefix="/api/v1", tags=["v1"])
router.include_router(products_router, prefix="/products", tags=["products"])