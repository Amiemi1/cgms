from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from sqlmodel import SQLModel

from app.db.session import engine

# ROUTERS
from app.dashboard.routes.auth import router as auth_router
from app.dashboard.routes.dashboard import router as dashboard_router
from app.dashboard.routes.memory_graph import router as memory_graph_router
from app.dashboard.routes.memory_actions import router as memory_actions_router
from app.dashboard.routes.insights import router as insights_router
from app.dashboard.routes.goal_api import router as goal_router


# ------------------------------------------------
# CREATE APP
# ------------------------------------------------

app = FastAPI(
    title="CGMS Dashboard API",
    description="Contextual Group Memory System",
    version="1.0"
)


# ------------------------------------------------
# CORS
# ------------------------------------------------

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ------------------------------------------------
# DATABASE INIT
# ------------------------------------------------

@app.on_event("startup")
def on_startup():

    SQLModel.metadata.create_all(engine)

    print("Database schema validated")


# ------------------------------------------------
# REGISTER ROUTERS
# ------------------------------------------------

app.include_router(auth_router)

app.include_router(dashboard_router)

app.include_router(memory_graph_router)

app.include_router(memory_actions_router)

app.include_router(insights_router)

app.include_router(goal_router)

# ------------------------------------------------
# ROOT ENDPOINT
# ------------------------------------------------

@app.get("/")
def root():

    return {
        "system": "CGMS",
        "status": "running"
    }