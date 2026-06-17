from fastapi import APIRouter

from app.services.product.readiness import (
    product_readiness
)


router = APIRouter()


@router.get("/product/console")
def product_console():

    return product_readiness()