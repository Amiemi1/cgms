from fastapi import APIRouter
from sqlmodel import select

from app.db.session import SessionLocal
from app.db.models.memory import Memory
from datetime import datetime, timedelta

from app.services.search.vector_search_service import search_memories
from app.services.embedding.embedding_service import generate_embedding

from app.services.intelligence.prioritization_service import get_prioritized_tasks
from app.services.intelligence.insight_service import generate_insights

from app.services.auth.application_authorization import (
    enforce_application_authorization,
)
from app.services.workspace.tenant_scope import (
    get_current_workspace_id,
    load_scoped_record,
)

from fastapi import Body

from fastapi import APIRouter, Depends, HTTPException
from app.db.models import Memory # or wherever your Memory model is
from app.db.session import SessionLocal

from fastapi import Body, Request

router = APIRouter(tags=["Dashboard"])


def _get_workspace_id(
    principal=Depends(
        enforce_application_authorization
    ),
) -> str:
    return get_current_workspace_id(principal)



# --------------------------------------------------
# HELPER
# --------------------------------------------------

def memory_to_dict(m: Memory):
    return {
        "id": m.id,
        "summary": m.summary,
        "priority": m.priority,
        "type": m.memory_type,
        "status": m.status,
        "created_at": m.created_at,
        "reminder_time": m.reminder_time
    }


# ---------------------------------------------
# BUILD HIERARCHY (TOP LEVEL FUNCTION)
# ---------------------------------------------
def build_hierarchy(tasks):

    task_map = {t["id"]: {**t, "children": []} for t in tasks if t.get("id")}

    # assign children
    for t in task_map.values():
        deps = t.get("depends_on") or []
        if not isinstance(deps, list):
            deps = [deps]

        for d in deps:
            parent = task_map.get(d)
            if parent:
                parent["children"].append(t)

    # extract roots
    roots = [
        t for t in task_map.values()
        if not t.get("depends_on")
    ]

    return roots

# ---------------------------------------------
# TASKS ENDPOINT (ONLY ONE)
# ---------------------------------------------
@router.get("/tasks/{chat_id}")
def get_tasks(
    chat_id: int,
    workspace_id: str = Depends(
        _get_workspace_id
    ),
):
    session = SessionLocal()
    try:
        memories = session.exec(
            select(Memory).where(
                Memory.workspace_id == workspace_id,
                Memory.chat_id == chat_id,
            )
        ).all()

        tasks = []
        for m in memories:
            summary = (m.summary or "").lower()
            depends_on = m.depends_on

            # 🔒 GUARDRAIL — REMOVE ORPHAN SUBTASKS
            if summary in [
                "clarify objective",
                "break into steps",
                "execute first step",
                "draft key points",
                "align data and evidence",
                "review and refine messaging",
                "gather latest performance data",
                "identify key trends",
                "summarize insights"
            ] and not depends_on:
                continue

            tasks.append({
                "id": m.id,
                "summary": m.summary,
                "status": m.status,
                "memory_type": m.memory_type,
                "depends_on": m.depends_on
            })

        # ✅ SAME LEVEL AS 'tasks = []'
        # ---------------------------------------------
        # GUARDRAIL: REMOVE ORPHAN SUBTASKS
        # ---------------------------------------------
        def is_generic_subtask(summary: str):
            return summary.lower() in [
                "clarify objective",
                "break into steps",
                "execute first step",
                "draft key points",
                "align data and evidence",
                "review and refine messaging",
                "gather latest performance data",
                "identify key trends",
                "summarize insights"
            ]

        clean_tasks = []

        for t in tasks:
            if is_generic_subtask(t["summary"]) and not t.get("depends_on"):
                continue
            clean_tasks.append(t)

        print("\n--- TASKS SENT TO FRONTEND ---")
        for t in tasks:
            print(t["id"], "|", t["summary"], "| depends_on:", t.get("depends_on"))
        print("--- END ---\n")

        # ✅ SAME LEVEL AS clean_tasks
        return build_hierarchy(clean_tasks)

    finally:
        session.close()


# --------------------------------------------------
# EVENTS PANEL (TEMP SAME AS TASKS)
# --------------------------------------------------

@router.get("/events/{chat_id}")
def get_events(
    chat_id: int,
    workspace_id: str = Depends(
        _get_workspace_id
    ),
):

    session = SessionLocal()

    try:

        events = session.exec(
            select(Memory)
            .where(
                Memory.workspace_id == workspace_id,
                Memory.chat_id == chat_id,
            )
            .order_by(Memory.created_at.desc())
        ).all()

        return [memory_to_dict(m) for m in events]

    finally:
        session.close()


# --------------------------------------------------
# DECISIONS PANEL (TEMP SAME)
# --------------------------------------------------

@router.get("/decisions/{chat_id}")
def get_decisions(
    chat_id: int,
    workspace_id: str = Depends(
        _get_workspace_id
    ),
):

    session = SessionLocal()

    try:

        decisions = session.exec(
            select(Memory)
            .where(
                Memory.workspace_id == workspace_id,
                Memory.chat_id == chat_id,
            )
            .order_by(Memory.created_at.desc())
        ).all()

        return [memory_to_dict(m) for m in decisions]

    finally:
        session.close()


# --------------------------------------------------
# INSIGHTS PANEL
# --------------------------------------------------

@router.get("/insights/{chat_id}")
def get_insights(
    chat_id: int,
    workspace_id: str = Depends(
        _get_workspace_id
    ),
):

    session = SessionLocal()

    try:
        memories = session.exec(
            select(Memory)
            .where(
                Memory.workspace_id == workspace_id,
                Memory.chat_id == chat_id,
            )
            .order_by(Memory.created_at.desc())
            .limit(50)
        ).all()

        tasks = []

        for m in memories:
            tasks.append({
                "id": m.id,
                "summary": m.summary,
                "status": m.status,
                "memory_type": m.memory_type,
                "depends_on": m.depends_on
            })

        print("DEBUG TASKS:", tasks)

        insights = generate_insights(tasks)

        print("DEBUG INSIGHTS:", insights)

        return insights

    except Exception as e:
        import traceback
        print("🚨 INSIGHTS ERROR:", e)
        traceback.print_exc()

        return [{"type": "error", "message": str(e)}]

    finally:
        session.close()


# --------------------------------------------------
# RESTORE MEMORY - DELETED --> ACTIVE
# --------------------------------------------------

@router.patch("/memory/{memory_id}/restore")
def restore_memory(
    memory_id: int,
    workspace_id: str = Depends(
        _get_workspace_id
    ),
):

    session = SessionLocal()

    try:
        m = load_scoped_record(
            session,
            Memory,
            memory_id,
            workspace_id,
        )

        if not m:
            return {"error": "not found"}

        m.status = "active"
        session.add(m)
        session.commit()

        return {"status": "restored"}

    finally:
        session.close()


# --------------------------------------------------
# RESTORE MEMORY - COMPLETED --> ACTIVE
# --------------------------------------------------

@router.patch("/memory/{memory_id}/reopen")
def reopen_memory(
    memory_id: int,
    workspace_id: str = Depends(
        _get_workspace_id
    ),
):

    session = SessionLocal()

    try:
        m = load_scoped_record(
            session,
            Memory,
            memory_id,
            workspace_id,
        )

        if not m:
            return {"error": "not found"}

        m.status = "active"
        session.add(m)
        session.commit()

        return {"status": "reopened"}

    finally:
        session.close()


# --------------------------------------------------
# TIMELINE PANEL
# --------------------------------------------------

@router.get("/timeline/{chat_id}")
def get_timeline(
    chat_id: int,
    workspace_id: str = Depends(
        _get_workspace_id
    ),
):

    session = SessionLocal()

    try:

        memories = session.exec(
            select(Memory)
            .where(
                Memory.workspace_id == workspace_id,
                Memory.chat_id == chat_id,
            )
            .order_by(Memory.created_at.desc())
        ).all()

        return [
            {
                "time": m.created_at,
                "summary": m.summary
            }
            for m in memories
        ]

    finally:
        session.close()


# --------------------------------------------------
# COMPLETE MEMORY
# --------------------------------------------------

@router.patch("/memory/{memory_id}/complete")
def complete_memory(
    memory_id: int,
    workspace_id: str = Depends(
        _get_workspace_id
    ),
):

    session = SessionLocal()

    try:

        memory = load_scoped_record(
            session,
            Memory,
            memory_id,
            workspace_id,
        )

        if not memory:
            return {"error": "Memory not found"}

        memory.status = "completed"
        session.add(memory)

        # 🔁 AUTO-COMPLETE PARENT
        def complete_parent_chain(child):
            parent_ids = child.depends_on or []

            for parent_id in parent_ids:

                siblings = session.exec(
                    select(Memory).where(
                        Memory.workspace_id == workspace_id,
                        Memory.chat_id == child.chat_id
                    )
                ).all()

                siblings = [
                    s for s in siblings
                    if s.depends_on and parent_id in s.depends_on
                ]

                if siblings and all(s.status == "completed" for s in siblings):

                    parent = load_scoped_record(
                        session,
                        Memory,
                        parent_id,
                        workspace_id,
                    )

                    if parent and parent.status != "completed":
                        parent.status = "completed"
                        session.add(parent)

                        # 🔁 RECURSE UPWARDS
                        complete_parent_chain(parent)

        # ✅ CALL IT HERE
        complete_parent_chain(memory)

        session.commit()
        return {"status": "completed"}

    finally:
        session.close()


# --------------------------------------------------
# DELETE MEMORY
# --------------------------------------------------

@router.delete("/memory/{memory_id}")
def delete_memory(
    memory_id: int,
    workspace_id: str = Depends(
        _get_workspace_id
    ),
):

    session = SessionLocal()

    try:
        m = load_scoped_record(
            session,
            Memory,
            memory_id,
            workspace_id,
        )

        if not m:
            return {"error": "not found"}

        m.status = "deleted"   # ✅ SOFT DELETE
        session.add(m)
        session.commit()

        return {"status": "deleted"}

    finally:
        session.close()


# --------------------------------------------------
# DELAY MEMORY
# --------------------------------------------------

@router.patch("/memory/{memory_id}/delay")
def delay_memory(
    memory_id: int,
    workspace_id: str = Depends(
        _get_workspace_id
    ),
):

    session = SessionLocal()

    try:
        m = load_scoped_record(
            session,
            Memory,
            memory_id,
            workspace_id,
        )

        if not m:
            return {"error": "not found"}

        if m.reminder_time:
            m.reminder_time = m.reminder_time + timedelta(days=1)
        else:
            m.reminder_time = datetime.utcnow() + timedelta(days=1)

        session.add(m)
        session.commit()

        return {"status": "delayed"}

    finally:
        session.close()

# --------------------------------------------------
# DEDUPLICATE MEMORY
# --------------------------------------------------

@router.delete("/memory/deduplicate/{chat_id}")
def deduplicate_memories(
    chat_id: int,
    workspace_id: str = Depends(
        _get_workspace_id
    ),
):

    session = SessionLocal()

    try:

        memories = session.exec(
            select(Memory)
            .where(
                Memory.workspace_id == workspace_id,
                Memory.chat_id == chat_id,
            )
        ).all()

        seen = set()
        duplicates = []

        for m in memories:
            key = m.summary.strip().lower()

            if key in seen:
                duplicates.append(m)
            else:
                seen.add(key)

        deleted = 0

        for d in duplicates:
            session.delete(d)
            deleted += 1

        session.commit()

        return {"deleted": deleted}

    finally:
        session.close()

# --------------------------------------------------
# SEMANTIC SEARCH
# --------------------------------------------------

@router.get("/search/{chat_id}")
def semantic_search(
    chat_id: int,
    q: str,
    workspace_id: str = Depends(
        _get_workspace_id
    ),
):

    session = SessionLocal()

    try:
        emb = generate_embedding(q)

        results = search_memories(
            session=session,
            chat_id=chat_id,
            embedding=emb,
            workspace_id=workspace_id,
            limit=10
        )

        return results

    finally:
        session.close()

# --------------------------------------------------
# MEMORY GRAPH
# --------------------------------------------------

@router.get("/memory-graph/{chat_id}")
def memory_graph(
    chat_id: int,
    workspace_id: str = Depends(
        _get_workspace_id
    ),
):

    session = SessionLocal()

    try:
        memories = session.exec(
            select(Memory)
            .where(
                Memory.workspace_id == workspace_id,
                Memory.chat_id == chat_id,
            )
            .limit(50)
        ).all()

        nodes = []
        links = []

        for m in memories:
            nodes.append({
                "id": m.id,
                "label": m.summary[:30]
            })

        # simple linking: same keyword
        for i in range(len(memories)):
            for j in range(i+1, len(memories)):
                if memories[i].summary.split()[0] == memories[j].summary.split()[0]:
                    links.append({
                        "source": memories[i].id,
                        "target": memories[j].id
                    })

        return {"nodes": nodes, "links": links}

    finally:
        session.close()



@router.post("/tasks/complete")
def complete_task(
    payload: dict = Body(...),
    workspace_id: str = Depends(
        _get_workspace_id
    ),
):
    session = SessionLocal()
    try:
        task_id = payload.get("id")

        if not task_id:
            return {"status": "error", "message": "No task id provided"}

        task = load_scoped_record(
            session,
            Memory,
            task_id,
            workspace_id,
        )

        if not task:
            return {"status": "not found"}

        task.status = "completed"
        # ✅ COMPLETE ALL CHILDREN
        children = session.exec(
            select(Memory).where(
                Memory.workspace_id == workspace_id,
                Memory.depends_on.contains([task.id])
            )
        ).all()

        for c in children:
            c.status = "completed"
            session.add(c)

        session.add(task)
        session.commit()

        return {"status": "success"}

    except Exception as e:
        import traceback
        print("COMPLETE TASK ERROR:", e)
        traceback.print_exc()
        return {"status": "error", "message": str(e)}

    finally:
        session.close()

# ===============================
# TASK BREAKDOWN ENDPOINT
# ===============================
@router.post("/tasks/breakdown")
async def breakdown_task(
    request: Request,
    workspace_id: str = Depends(
        _get_workspace_id
    ),
):

    session = SessionLocal()

    try:
        payload = {}

        try:
            payload = await request.json()
        except Exception:
            payload = {}

        task_id = None

        if isinstance(payload, dict):
            task_id = (
                payload.get("id")
                or payload.get("task_id")
                or payload.get("taskId")
            )

        elif isinstance(payload, int):
            task_id = payload

        elif isinstance(payload, str) and payload.isdigit():
            task_id = int(payload)

        if not task_id:
            task_id = request.query_params.get("id") or request.query_params.get("task_id")

        if not task_id:
            raise HTTPException(
                status_code=400,
                detail={
                    "message": "No task id provided",
                    "received_payload": payload
                }
            )

        task = load_scoped_record(
            session,
            Memory,
            int(task_id),
            workspace_id,
        )

        if not task:
            raise HTTPException(
                status_code=404,
                detail="Task not found"
            )

        summary = (task.summary or "").lower()

        if "prepare" in summary:
            subtasks = [
                "Draft key points",
                "Align data and evidence",
                "Review and refine messaging"
            ]

        elif "review" in summary:
            subtasks = [
                "Gather latest performance data",
                "Identify key trends",
                "Summarize insights"
            ]

        elif "meeting" in summary:
            subtasks = [
                "Confirm agenda",
                "Prepare materials",
                "Align stakeholders"
            ]

        else:
            subtasks = [
                "Clarify objective",
                "Break into steps",
                "Execute first step"
            ]

        created = []

        for s in subtasks:
            new_task = Memory(
                workspace_id=workspace_id,
                chat_id=task.chat_id,
                source_message_id=0,
                summary=s,
                status="active",
                memory_type="task",
                created_at=datetime.utcnow(),
                depends_on=[task.id]
            )

            session.add(new_task)
            session.flush()

            created.append({
                "id": new_task.id,
                "summary": new_task.summary,
                "status": new_task.status,
                "depends_on": new_task.depends_on
            })

        session.commit()

        return {
            "status": "success",
            "parent_task_id": task.id,
            "created": created
        }

    finally:
        session.close()
