import logging
from typing import Annotated
from product_service.dependencies.session import get_session
from fastapi import APIRouter, Depends, status, HTTPException
from product_service.srv.products_srv import ProductsService
from product_service.repos.products_repo import ProductsRepo
import product_service.schemas.products as ps
import product_service.domain.exceptions.products_exceptions as pe

router = APIRouter()

logger = logging.getLogger(__name__)


def get_service(session=Depends(get_session)):

    repo = ProductsRepo(session)
    service = ProductsService(repo)
    return service


ServiceDependency = Annotated[ProductsService, Depends(get_service)]


@router.get("", response_model=list[ps.ProductResponse])
async def get_products(service: ServiceDependency, filter: ps.ProductFilter = Depends()):
    return await service.get_all_products(filter)


@router.post("", response_model=ps.ProductResponse, status_code=status.HTTP_201_CREATED)
async def create_product(service: ServiceDependency, payload: ps.ProductCreate):
    try:
        logger.info("Creating new product")
        return await service.create_product(payload)
    except pe.InvalidProductData as e:
        logger.error(f"Error occurred while creating product: {e}")
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail=str(e))
    except pe.ProductAlreadyExists as e:
        logger.error(f"Error occurred while creating product: {e}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Product already exists")


@router.get("/{product_id}", response_model=ps.ProductResponse)
async def get_product(product_id: int, service: ServiceDependency):
    try:
        logger.info(f"Fetching product with ID: {product_id}")
        return await service.get_product_by_id(product_id)
    except pe.ProductNotFound as e:
        logger.error(f"Error occurred while fetching product: {e}")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")


@router.put("/{product_id}", response_model=ps.ProductResponse)
async def update_product(product_id: int, payload: ps.ProductUpdate, service: ServiceDependency):
    try:
        logger.info(f"Updating product with ID: {product_id}")
        return await service.update_product(product_id, payload)
    except pe.ProductNotFound as e:
        logger.error(f"Error occurred while updating product: {e}")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")
    except pe.InvalidProductData as e:
        logger.error(f"Error occurred while updating product: {e}")
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail=str(e))


@router.delete("/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_product(product_id: int, service: ServiceDependency):
    try:
        logger.info(f"Deleting product with ID: {product_id}")
        await service.delete_product(product_id)
    except pe.ProductNotFound as e:
        logger.error(f"Error occurred while deleting product: {e}")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")
    except pe.InvalidProductData as e:
        logger.error(f"Error occurred while deleting product: {e}")
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail=str(e))


@router.post(
    "/{product_id}/reserve", status_code=status.HTTP_200_OK, response_model=ps.ProductReservationResponse
)
async def reserve_product(product_id: int, payload: ps.ProductReserve, service: ServiceDependency):
    try:
        logger.info(f"Reserving {payload.quantity} units of product with ID: {product_id}")
        return await service.reserve_product(product_id, payload)
    except pe.ProductNotFound as e:
        logger.error(f"Error occurred while reserving product: {e}")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")
    except pe.InsufficientQuantity as e:
        logger.error(f"Error occurred while reserving product: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Insufficient quantity available for reservation"
        )
    except pe.InvalidProductData as e:
        logger.error(f"Error occurred while reserving product: {e}")
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail=str(e))


@router.post(
    "/inventory-adjustments", response_model=ps.AdjustmentResponse, status_code=status.HTTP_201_CREATED
)
async def create_inventory_adjustments(service: ServiceDependency, payload: ps.AdjustmentCreate):
    try:
        logger.info("Creating new inventory adjustment")
        return await service.create_adjustment(payload)
    except pe.ProductNotFound as e:
        logger.error(f"Error occured while creating inventiry adjustment: {e}")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except pe.InvalidProductData as e:
        logger.error(f"Error occured while creating inventiry adjustment: {e}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/inventory-adjustments/{doc_id}", response_model=ps.AdjustmentResponse)
async def get_adustment(service: ServiceDependency, doc_id: int):
    try:
        logger.info(f"Readin inventory adjustment #{doc_id}")
        return await service.get_adjustment(doc_id)
    except pe.DocumentNotFound as e:
        logger.error(f"Error occured while posting inventory adjustment: {e}")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Adjustment does not exists")


@router.post("/inventory-adjustments/{doc_id}/post")
async def post_adjustment(service: ServiceDependency, doc_id: int):
    try:
        logger.info(f"Posting inventory adjustment #{doc_id}")
        await service.post_adjustment(doc_id)
    except pe.InvalidDocumentStatus as e:
        logger.error(f"Error occured while posting inventory adjustments. {e}")
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="Document has unprocessable status. Must be PENDING",
        )
    except pe.InsufficientQuantity as e:
        logger.error(f"Error occured while posting inventory adjustments. {e}")
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=f"One or more products have no enough items to proceed: {e}",
        )
    except pe.DocumentNotFound as e:
        logger.error(f"Error occured while posting inventory adjustment: {e}")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Adjustment does not exists")
    except pe.DataLockError as e:
        logger.error(f"Error occured while posting inventory adjustment: {e}")
        raise HTTPException(status_code=status.HTTP_423_LOCKED, detail=str(e))
    return {"message": "posted"}


@router.post("/inventory-adjustments/{doc_id}/cancel")
async def cancel_adjustment(service: ServiceDependency, doc_id: int):
    try:
        logger.info(f"Cancelling inventory adjustment #{doc_id}")
        await service.cancel_adjustment(doc_id)
    except pe.InvalidDocumentStatus as e:
        logger.error(f"Error occured while cancelling inventory adjustments. {e}")
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="Document has unprocessable status. Must be PENDING",
        )
    except pe.DocumentNotFound as e:
        logger.error(f"Error occured while cancelling inventory adjustment: {e}")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Adjustment does not exists")
    except pe.DataLockError as e:
        logger.error(f"Error occured while cancelling inventory adjustment: {e}")
        raise HTTPException(status_code=status.HTTP_423_LOCKED, detail=str(e))
    return {"message": "cancelled"}
