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

from app.dashboard.routes.runtime_metrics import (
    router as runtime_metrics_router
)

from app.dashboard.routes.runtime_commands import (
    router as runtime_commands_router
)

from app.dashboard.routes.runtime_flags import (
    router as runtime_flags_router
)

from app.dashboard.routes.runtime_kill_switch import (
    router as runtime_kill_switch_router
)

from app.dashboard.routes.runtime_policy import (
    router as runtime_policy_router
)

from app.dashboard.routes.runtime_quarantine import (
    router as runtime_quarantine_router
)

from app.dashboard.routes.connectors import (
    router as connector_router
)

from app.dashboard.routes.connector_control import (
    router as connector_control_router
)

from app.dashboard.routes.connector_health import (
    router as connector_health_router
)

from app.dashboard.routes.external_ingestion import (
    router as external_ingestion_router
)

from app.dashboard.routes.workspaces import (
    router as workspace_router
)

from app.dashboard.routes.workspace_context import (
    router as workspace_context_router
)

from app.dashboard.routes.workspace_metrics import (
    router as workspace_metrics_router
)

from app.dashboard.routes.workspace_admin import (
    router as workspace_admin_router
)

from app.dashboard.routes.workspace_quotas import (
    router as workspace_quotas_router
)

from app.dashboard.routes.connector_adapters import (
    router as connector_adapters_router
)

from app.dashboard.routes.admin_summary import (
    router as admin_summary_router
)

from app.dashboard.routes.product_console import (
    router as product_console_router
)

from app.dashboard.routes.release_status import (
    router as release_status_router
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

app.include_router(
    runtime_metrics_router
)

app.include_router(
    runtime_commands_router
)

app.include_router(
    runtime_flags_router
)

app.include_router(
    runtime_kill_switch_router
)

app.include_router(
    runtime_policy_router
)

app.include_router(
    runtime_quarantine_router
)

app.include_router(
    connector_router
)

app.include_router(
    connector_control_router
)

app.include_router(
    connector_health_router
)

app.include_router(
    external_ingestion_router
)

app.include_router(
    workspace_router
)

app.include_router(
    workspace_context_router
)

app.include_router(
    workspace_metrics_router
)

app.include_router(
    workspace_admin_router
)

app.include_router(
    workspace_quotas_router
)

app.include_router(
    connector_adapters_router
)

app.include_router(
    admin_summary_router
)

app.include_router(
    product_console_router
)

app.include_router(
    release_status_router
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