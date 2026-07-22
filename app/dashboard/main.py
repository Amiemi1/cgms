from contextlib import asynccontextmanager
import logging

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlmodel import SQLModel

from app.core.runtime_policy import (
    get_runtime_environment,
    initialize_database_schema,
)
from app.db.models.memory import Memory
from app.db.session import SessionLocal, engine
from app.services.product_readiness.bootstrap import (
    bootstrap_product_capabilities,
)

from app.dashboard.routes.patent_readiness_dashboard import (
    router as patent_readiness_dashboard_router,
)

from app.dashboard.routes.patent_evidence_export import (
    router as patent_evidence_export_router,
)

from app.dashboard.routes.browser_auth import (
    router as browser_auth_router,
)

from app.dashboard.routes.browser_session_administration import (
    router as browser_session_administration_router,
)

# Ensure orchestration handlers are registered
import app.services.orchestration.handlers  # noqa: F401

# Core dashboard routers
from app.dashboard.routes.memory_panels import router as memory_panels_router
from app.dashboard.routes.memory_graph import router as memory_graph_router
from app.dashboard.routes.memory_actions import router as memory_actions_router
from app.dashboard.routes.insights import router as insights_router
from app.dashboard.routes.intelligence_api import router as intelligence_router

# Runtime / governance routers
from app.dashboard.routes.runtime_events import router as runtime_events_router
from app.dashboard.routes.audit_console import router as audit_console_router
from app.dashboard.routes.session_replay import router as session_replay_router
from app.dashboard.routes.enterprise_readiness import router as enterprise_readiness_router
from app.dashboard.routes.product_readiness import router as product_readiness_router
from app.dashboard.routes.system_health import router as system_health_router
from app.dashboard.routes.environment_manifest import router as environment_manifest_router
from app.dashboard.routes.runtime_metrics import router as runtime_metrics_router
from app.dashboard.routes.runtime_commands import router as runtime_commands_router
from app.dashboard.routes.runtime_flags import router as runtime_flags_router
from app.dashboard.routes.runtime_kill_switch import router as runtime_kill_switch_router
from app.dashboard.routes.runtime_policy import router as runtime_policy_router
from app.dashboard.routes.runtime_quarantine import router as runtime_quarantine_router

# Connector / workspace routers
from app.dashboard.routes.connectors import router as connector_router
from app.dashboard.routes.connector_control import router as connector_control_router
from app.dashboard.routes.connector_health import router as connector_health_router
from app.dashboard.routes.external_ingestion import router as external_ingestion_router
from app.dashboard.routes.workspaces import router as workspace_router
from app.dashboard.routes.workspace_context import router as workspace_context_router
from app.dashboard.routes.workspace_metrics import router as workspace_metrics_router
from app.dashboard.routes.workspace_admin import router as workspace_admin_router
from app.dashboard.routes.workspace_quotas import router as workspace_quotas_router
from app.dashboard.routes.connector_adapters import router as connector_adapters_router

# Product / commercial / release routers
from app.dashboard.routes.admin_summary import router as admin_summary_router
from app.dashboard.routes.product_console import router as product_console_router
from app.dashboard.routes.release_status import router as release_status_router
from app.dashboard.routes.commercial import router as commercial_router
from app.dashboard.routes.ga_release import router as ga_router
from app.dashboard.routes.ops import router as ops_router

from app.dashboard.routes.goal_api import (
    router as goal_router
)

from app.dashboard.routes.runtime_timeline import (
    router as runtime_timeline_router
)

from app.dashboard.routes.operator_console import (
    router as operator_console_router
)

from app.dashboard.routes.memory_intelligence import (
    router as memory_intelligence_router
)

from app.dashboard.routes.product_readiness_dashboard import (
    router as product_readiness_dashboard_router,
)

from app.services.security.cors_policy import (
    get_allowed_cors_origins,
)

startup_logger = logging.getLogger(
    "cgms.dashboard.startup"
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    runtime_environment = (
        get_runtime_environment()
    )

    startup_logger.info(
        "cgms_starting environment=%s",
        runtime_environment,
    )

    database_schema_ready = (
        initialize_database_schema(
            create_all=(
                SQLModel.metadata.create_all
            ),
            engine=engine,
            environment=runtime_environment,
            logger=startup_logger,
        )
    )

    app.state.runtime_environment = (
        runtime_environment
    )

    app.state.database_schema_ready = (
        database_schema_ready
    )

    capability_count = (
        bootstrap_product_capabilities()
    )

    startup_logger.info(
        "product_readiness_catalogue_loaded "
        "capability_count=%s",
        capability_count,
    )

    try:
        yield

    finally:
        startup_logger.info(
            "cgms_stopping environment=%s",
            runtime_environment,
        )


app = FastAPI(
    title="CGMS Dashboard",
    version="1.50",
    lifespan=lifespan,
)


templates = Jinja2Templates(
    directory="app/dashboard/templates"
)

allowed_cors_origins = (
    get_allowed_cors_origins()
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/dashboard", response_class=HTMLResponse)
def dashboard(request: Request):
    return templates.TemplateResponse(
        "dashboard.html",
        {"request": request},
    )


@app.post("/dashboard/tasks/{task_id}/complete")
def mark_task_complete(task_id: int):
    db = SessionLocal()

    try:
        task = (
            db.query(Memory)
            .filter(
                Memory.id == task_id,
                Memory.memory_type == "task",
            )
            .first()
        )

        if not task:
            raise HTTPException(
                status_code=404,
                detail="Task not found",
            )

        task.status = "completed"
        db.commit()

        return {"success": True}

    finally:
        db.close()


# Dashboard routers
app.include_router(memory_panels_router, prefix="/dashboard")
app.include_router(memory_graph_router, prefix="/dashboard")
app.include_router(memory_actions_router, prefix="/dashboard")
app.include_router(insights_router, prefix="/dashboard")

# Do not include goal_api for now.
# memory_panels already exposes /dashboard/goals/{chat_id}
# Including goal_api duplicates that route and causes instability.

app.include_router(intelligence_router)

# Runtime / governance
app.include_router(runtime_events_router)
app.include_router(audit_console_router)
app.include_router(session_replay_router)
app.include_router(enterprise_readiness_router)
app.include_router(product_readiness_router)
app.include_router(system_health_router)
app.include_router(environment_manifest_router)
app.include_router(runtime_metrics_router)
app.include_router(runtime_commands_router)
app.include_router(runtime_flags_router)
app.include_router(runtime_kill_switch_router)
app.include_router(runtime_policy_router)
app.include_router(runtime_quarantine_router)

# Connectors / workspace
app.include_router(connector_router)
app.include_router(connector_control_router)
app.include_router(connector_health_router)
app.include_router(external_ingestion_router)
app.include_router(workspace_router)
app.include_router(workspace_context_router)
app.include_router(workspace_metrics_router)
app.include_router(workspace_admin_router)
app.include_router(workspace_quotas_router)
app.include_router(connector_adapters_router)

# Product / commercial / release / ops
app.include_router(admin_summary_router)
app.include_router(product_console_router)
app.include_router(release_status_router)
app.include_router(commercial_router)
app.include_router(ga_router)
app.include_router(ops_router)

app.include_router(
    goal_router
)

app.include_router(
    runtime_timeline_router
)

app.include_router(operator_console_router)

app.include_router(memory_intelligence_router)

app.include_router(product_readiness_dashboard_router)

app.include_router(
    browser_auth_router
)

app.include_router(
    browser_session_administration_router
)

app.include_router(
    patent_readiness_dashboard_router
)

app.include_router(
    patent_evidence_export_router
)

@app.get("/")
def root():
    return {
        "system": "CGMS",
        "status": "running",
        "version": "1.50",
        "build": "stabilized_ga",
    }


@app.get("/debug/routes")
def debug_routes():
    return [
        {
            "path": route.path,
            "name": route.name,
        }
        for route in app.routes
    ]

@app.get(
"/operator",
response_class=HTMLResponse
)

def operator(
request:
Request
):

    return templates.TemplateResponse(

        "operator_console.html",

        {

            "request":
            request
        }

    )
