import logging
from fastapi import APIRouter, Depends
from typing import Annotated, List
from product_service.dependencies.session import get_session
from product_service.repos.reports_repo import ReportsRepo
import product_service.schemas.reports as rs

logger = logging.getLogger(__name__)

router = APIRouter()


def get_repo(db=Depends(get_session)):
    return ReportsRepo(db)


RepoDependency = Annotated[ReportsRepo, Depends(get_repo)]


@router.get("/inventory", response_model=List[rs.InventoryReportResponse])
async def inventory_report(repo: RepoDependency, filters: rs.InventoryReportFilter = Depends()):
    logger.info("Executing inventory report")
    return await repo.inventory_report(filters)


@router.get("/orders", response_model=rs.OrdersReportResponse)
async def order_statistics(repo: RepoDependency, filters: rs.OrdersReportFilter = Depends()):
    logger.info("Executing orders report")
    return await repo.orders_statistics(filters)


@router.get("/products/top-ordered", response_model=List[rs.ProductOrderedReportResponse])
async def top_ordered(repo: RepoDependency, filters: rs.TopProductsReportFilter = Depends()):
    logger.info("Executing top ordered products report")
    return await repo.top_ordered_products(filters)
