from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi import Request
from app.dashboard.routes.memory_panels import router as memory_router
from fastapi.middleware.cors import CORSMiddleware
from sqlmodel import SQLModel
from app.db.session import engine

# SPRINT 1 — EVENT-DRIVEN ORCHESTRATION
import app.services.orchestration.handlers

# ROUTERS
from app.dashboard.routes.memory_panels import router as memory_panels_router
from app.dashboard.routes.memory_graph import router as memory_graph_router
from app.dashboard.routes.memory_actions import router as memory_actions_router
from app.dashboard.routes.insights import router as insights_router
from app.dashboard.routes.intelligence_api import router as intelligence_router
from app.dashboard.routes.goal_api import router as goal_router
from fastapi import HTTPException
from app.db.session import SessionLocal
from app.db.models.memory import Memory

from app.dashboard.routes.runtime_events import (
    router as runtime_router
)

from app.dashboard.routes.runtime_events import router as runtime_events_router

app = FastAPI(
    title="CGMS Dashboard",
    version="1.0"
)

from app.dashboard.routes.audit_console import (
    router as audit_console_router
)

from app.dashboard.routes.session_replay import (
    router as session_replay_router
)

from app.dashboard.routes.enterprise_readiness import (
    router as enterprise_readiness_router
)

from app.dashboard.routes.system_health import (
    router as system_health_router
)

from app.dashboard.routes.environment_manifest import (
    router as environment_manifest_router
)

templates = Jinja2Templates(directory="app/dashboard/templates")


@app.get("/dashboard", response_class=HTMLResponse)
def dashboard(request: Request):
    return templates.TemplateResponse("dashboard.html", {"request": request})


# ---------- MARK TASK COMPLETE ----------
@app.post("/dashboard/tasks/{task_id}/complete")
def mark_task_complete(task_id: int):

    db = SessionLocal()

    try:
        task = db.query(Memory).filter(
            Memory.id == task_id,
            Memory.memory_type == "task"
        ).first()

        if not task:
            raise HTTPException(status_code=404, detail="Task not found")

        task.status = "completed"
        db.commit()

        return {"success": True}

    finally:
        db.close()

# -----------------------------
# CORS
# -----------------------------

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)




# -----------------------------
# DATABASE INIT
# -----------------------------

@app.on_event("startup")
def on_startup():

    SQLModel.metadata.create_all(engine)

    print("Database schema validated")


# -----------------------------
# ROUTERS
# -----------------------------

app.include_router(memory_panels_router, prefix="/dashboard")
app.include_router(memory_graph_router, prefix="/dashboard")
app.include_router(memory_actions_router, prefix="/dashboard")
app.include_router(insights_router, prefix="/dashboard")
app.include_router(intelligence_router)
app.include_router(goal_router)
app.include_router(memory_router)

# SPRINT 1 — EVENT-DRIVEN ORCHESTRATION
app.include_router(runtime_events_router)

app.include_router(
    audit_console_router
)

app.include_router(
    session_replay_router
)

app.include_router(
    enterprise_readiness_router
)

app.include_router(
    system_health_router
)

app.include_router(
    environment_manifest_router
)

# -----------------------------
# ROOT
# -----------------------------

@app.get("/")
def root():
    return {
        "system": "CGMS",
        "status": "running",
        "build": "auto_deploy_test"
    }