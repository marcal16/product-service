import logging
from typing import Annotated
from product_service.dependencies.session import get_session
from fastapi import APIRouter, Depends, status, HTTPException
from product_service.srv.orders_srv import OrdersService
from product_service.repos.orders_repo import OrdersRepo
import product_service.schemas.orders as ors
import product_service.domain.exceptions.products_exceptions as pe

router = APIRouter()

logger = logging.getLogger(__name__)

def get_service(session = Depends(get_session)):

    repo = OrdersRepo(session)
    service = OrdersService(repo)
    return service

ServiceDependency = Annotated[OrdersService, Depends(get_service)]

@router.post("", response_model=ors.OrderResponse, status_code=status.HTTP_201_CREATED)
async def create_order(
    service: ServiceDependency,
    payload: ors.OrderCreate
):
    try:
        logger.info("Creating new order")
        return await service.create_order(payload)
    except pe.InvalidOrderData as e:
        logger.error(f"Error occurred while creating order: {e}")
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail=str(e))
    except pe.ProductNotFound as e:
        logger.error(f"Error occurred while creating order: {e}")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order has product that does not exist")
    except pe.InsufficientQuantity as e:
        logger.error(f"Error occurred while creating order: {e}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Insufficient product quantity. Details: " + str(e))