from __future__ import annotations

from typing import Annotated

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Query,
    status,
)
from pydantic import BaseModel
from sqlmodel import select

from app.db.models.goal import Goal
from app.db.models.memory import Memory
from app.db.session import SessionLocal
from app.services.auth.account_authorization import (
    normalize_account_identifier,
)
from app.services.auth.application_authorization import (
    enforce_application_authorization,
)
from app.services.auth.auth_dependency import (
    AuthenticatedPrincipal,
)
from app.services.embedding.embedding_service import (
    generate_embedding,
)
from app.services.insights.insight_engine import (
    generate_insights_for_scope as generate_product_insights_for_scope,
)
from app.services.intelligence.insight_service import (
    generate_insights as generate_panel_insights,
)
from app.services.intelligence.prioritization_service import (
    get_next_action_for_scope,
    get_prioritized_tasks_for_scope,
)
from app.services.memory.scope import (
    MemoryIdentityScope,
    account_scope,
    orm_identity_predicate,
)
from app.services.search.vector_search_service import (
    search_memories_for_scope,
)


router = APIRouter(
    prefix="/dashboard",
    tags=["Knowledge Workspace"],
)


class TaskCreateRequest(BaseModel):
    summary: str


_GENERIC_SUBTASKS = frozenset(
    {
        "clarify objective",
        "break into steps",
        "execute first step",
        "draft key points",
        "align data and evidence",
        "review and refine messaging",
        "gather latest performance data",
        "identify key trends",
        "summarize insights",
    }
)


def _account_scope_from_principal(
    principal: AuthenticatedPrincipal,
) -> MemoryIdentityScope:
    return account_scope(
        principal.workspace_id,
        normalize_account_identifier(
            principal.user_id
        ),
    )


def _get_account_scope(
    principal: Annotated[
        AuthenticatedPrincipal,
        Depends(
            enforce_application_authorization
        ),
    ],
) -> MemoryIdentityScope:
    return _account_scope_from_principal(
        principal
    )


def _build_hierarchy(
    tasks: list[dict],
) -> list[dict]:
    task_map = {
        task["id"]: {
            **task,
            "children": [],
        }
        for task in tasks
        if task.get("id") is not None
    }

    for task in task_map.values():
        dependencies = (
            task.get("depends_on")
            or []
        )

        if not isinstance(
            dependencies,
            list,
        ):
            dependencies = [
                dependencies
            ]

        for parent_id in dependencies:
            parent = task_map.get(
                parent_id
            )

            if parent is not None:
                parent[
                    "children"
                ].append(
                    task
                )

    return [
        task
        for task in task_map.values()
        if not task.get(
            "depends_on"
        )
    ]


@router.get("/tasks")
def product_tasks(
    scope: Annotated[
        MemoryIdentityScope,
        Depends(
            _get_account_scope
        ),
    ],
):
    session = SessionLocal()

    try:
        memories = session.exec(
            select(Memory).where(
                Memory.workspace_id
                == scope.workspace_id,
                orm_identity_predicate(
                    Memory,
                    scope,
                ),
            )
        ).all()

        tasks = []

        for memory in memories:
            summary = (
                memory.summary
                or ""
            ).strip()

            if (
                summary.casefold()
                in _GENERIC_SUBTASKS
                and not memory.depends_on
            ):
                continue

            tasks.append(
                {
                    "id": memory.id,
                    "summary":
                        memory.summary,
                    "status":
                        memory.status,
                    "memory_type":
                        memory.memory_type,
                    "depends_on":
                        memory.depends_on,
                }
            )

        return _build_hierarchy(
            tasks
        )

    finally:
        session.close()


@router.get("/search")
def product_search(
    q: Annotated[
        str,
        Query(
            min_length=1,
            max_length=4096,
        ),
    ],
    scope: Annotated[
        MemoryIdentityScope,
        Depends(
            _get_account_scope
        ),
    ],
):
    session = SessionLocal()

    try:
        embedding = generate_embedding(
            q
        )

        return search_memories_for_scope(
            session=session,
            embedding=embedding,
            scope=scope,
            limit=10,
        )

    finally:
        session.close()


@router.get("/insights")
def panel_insights(
    scope: Annotated[
        MemoryIdentityScope,
        Depends(
            _get_account_scope
        ),
    ],
):
    session = SessionLocal()

    try:
        tasks = (
            get_prioritized_tasks_for_scope(
                session,
                scope,
                limit=50,
            )
        )

        return generate_panel_insights(
            tasks
        )

    finally:
        session.close()


@router.get("/product-insights")
def predictive_insights(
    scope: Annotated[
        MemoryIdentityScope,
        Depends(
            _get_account_scope
        ),
    ],
):
    return {
        "insights":
            generate_product_insights_for_scope(
                scope
            )
    }


@router.get("/priorities")
def product_priorities(
    scope: Annotated[
        MemoryIdentityScope,
        Depends(
            _get_account_scope
        ),
    ],
):
    session = SessionLocal()

    try:
        return (
            get_prioritized_tasks_for_scope(
                session,
                scope,
            )
            or []
        )

    finally:
        session.close()


@router.get("/goals")
def product_goals(
    scope: Annotated[
        MemoryIdentityScope,
        Depends(
            _get_account_scope
        ),
    ],
    limit: Annotated[
        int,
        Query(
            ge=1,
            le=100,
        ),
    ] = 20,
):
    session = SessionLocal()

    try:
        goals = session.exec(
            select(Goal)
            .where(
                Goal.workspace_id
                == scope.workspace_id,
                orm_identity_predicate(
                    Goal,
                    scope,
                ),
                Goal.status
                != "deleted",
            )
            .order_by(
                Goal.created_at.desc()
            )
            .limit(
                limit
            )
        ).all()

        clean_goals = []
        seen = set()

        for goal in goals:
            name = str(
                getattr(
                    goal,
                    "name",
                    "",
                )
            ).strip()

            if (
                not name
                or name.isdigit()
            ):
                continue

            normalized = name.casefold()

            if normalized in seen:
                continue

            seen.add(
                normalized
            )

            clean_goals.append(
                {
                    "id": goal.id,
                    "name": name,
                    "description":
                        getattr(
                            goal,
                            "description",
                            None,
                        ),
                    "status":
                        getattr(
                            goal,
                            "status",
                            "active",
                        ),
                    "created_at":
                        str(
                            goal.created_at
                        ),
                }
            )

        return clean_goals

    finally:
        session.close()


@router.get("/next-action")
def product_next_action(
    scope: Annotated[
        MemoryIdentityScope,
        Depends(
            _get_account_scope
        ),
    ],
):
    session = SessionLocal()

    try:
        return (
            get_next_action_for_scope(
                session,
                scope,
            )
            or {}
        )

    finally:
        session.close()


@router.post("/tasks/create")
def create_product_task(
    payload: TaskCreateRequest,
    scope: Annotated[
        MemoryIdentityScope,
        Depends(
            _get_account_scope
        ),
    ],
):
    summary = (
        payload.summary
        or ""
    ).strip()

    if not summary:
        raise HTTPException(
            status_code=(
                status.HTTP_422_UNPROCESSABLE_ENTITY
            ),
            detail=(
                "Task summary is required."
            ),
        )

    session = SessionLocal()

    try:
        task = Memory(
            workspace_id=(
                scope.workspace_id
            ),
            chat_id=scope.chat_id,
            account_user_id=(
                scope.account_user_id
            ),
            summary=summary,
            memory_type="task",
            status="active",
        )

        session.add(
            task
        )
        session.commit()
        session.refresh(
            task
        )

        return {
            "id": task.id,
            "summary":
                task.summary,
            "status":
                task.status,
            "memory_type":
                task.memory_type,
        }

    finally:
        session.close()


@router.delete("/memory/deduplicate")
def deduplicate_product_memories(
    scope: Annotated[
        MemoryIdentityScope,
        Depends(
            _get_account_scope
        ),
    ],
):
    session = SessionLocal()

    try:
        memories = session.exec(
            select(Memory).where(
                Memory.workspace_id
                == scope.workspace_id,
                orm_identity_predicate(
                    Memory,
                    scope,
                ),
            )
        ).all()

        seen = set()
        duplicates = []

        for memory in memories:
            key = (
                memory.summary
                or ""
            ).strip().casefold()

            if key in seen:
                duplicates.append(
                    memory
                )
            else:
                seen.add(
                    key
                )

        for duplicate in duplicates:
            session.delete(
                duplicate
            )

        session.commit()

        return {
            "deleted":
                len(duplicates)
        }

    finally:
        session.close()
