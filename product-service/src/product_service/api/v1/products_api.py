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

def get_service(session = Depends(get_session)):

    repo = ProductsRepo(session)
    service = ProductsService(repo)
    return service

ServiceDependency = Annotated[ProductsService, Depends(get_service)]

@router.get("", response_model=list[ps.ProductResponse])
async def get_products(
    service: ServiceDependency,
    filter = Depends()
):
    return await service.get_all_products(filter)

@router.post("", response_model=ps.ProductResponse, status_code=status.HTTP_201_CREATED)
async def create_product(
    service: ServiceDependency,
    payload: ps.ProductCreate
):
    try:
        logger.info("Creating new product")
        return await service.create_product(payload)
    except pe.InvalidProductData as e:
        logger.error(f"Error occurred while creating product: {e}")
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail=str(e))
    except pe.ProductAlreadyExists as e:
        logger.error(f"Error occurred while creating product: {e}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Product already exists")

@router.get("/{product_id}")
async def get_product(
    product_id: int,
    service: ServiceDependency
):
    try:
        logger.info(f"Fetching product with ID: {product_id}")
        return await service.get_product_by_id(product_id)
    except pe.ProductNotFound as e:
        logger.error(f"Error occurred while fetching product: {e}")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")

@router.put("/{product_id}")
async def update_product(
    product_id: int,
    payload: ps.ProductUpdate,
    service: ServiceDependency
):
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
async def delete_product(
    product_id: int,
    service: ServiceDependency
):
    try:
        logger.info(f"Deleting product with ID: {product_id}")
        await service.delete_product(product_id)
    except pe.ProductNotFound as e:
        logger.error(f"Error occurred while deleting product: {e}")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")
    except pe.InvalidProductData as e:
        logger.error(f"Error occurred while deleting product: {e}")
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail=str(e))

