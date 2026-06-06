from fastapi import FastAPI

from app.web.routers.dashboard_api import router as dashboard_router
from app.web.routers.memory_api import router as memory_router
from app.web.routers.intelligence_api import router as intelligence_router
from app.web.routers.search_api import router as search_router


app = FastAPI(
    title="CGMS Dashboard API",
    version="1.0"
)


@app.get("/")
def root():
    return {"system": "CGMS", "status": "running"}


# EXISTING DASHBOARD ROUTES
app.include_router(dashboard_router)

# NEW ROUTES
app.include_router(memory_router)
app.include_router(intelligence_router)
app.include_router(search_router)