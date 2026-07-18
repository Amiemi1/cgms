from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates


router = APIRouter(
    tags=["Product Readiness Dashboard"],
)

templates = Jinja2Templates(
    directory="app/dashboard/templates",
)


@router.get(
    "/product-readiness/dashboard",
    response_class=HTMLResponse,
    include_in_schema=False,
)
def product_readiness_dashboard(request: Request):
    """
    Render the Product Readiness dashboard.

    Readiness data is loaded by the page from the dynamic
    Product Readiness REST API.
    """
    return templates.TemplateResponse(
        "product_readiness_dashboard.html",
        {
            "request": request,
        },
    )