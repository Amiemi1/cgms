from sqlmodel import select, Session
from typing import List, Dict, Tuple
from datetime import datetime

from app.db.models.memory import Memory
from app.db.models.goal import Goal
from app.services.workspace.tenant_scope import (
    load_scoped_record,
    normalize_workspace_id,
)


# ------------------------------------------------
# GOAL SCORE
# ------------------------------------------------
def goal_score(session: Session, memory: Memory) -> int:

    try:
        if not memory.goal_id:
            return 0

        goal = load_scoped_record(
            session,
            Goal,
            memory.goal_id,
            memory.workspace_id,
        )

        if goal and goal.status == "active":
            return 25

        return 0

    except Exception as e:
        print("GOAL SCORE ERROR:", e)
        return 0


# ------------------------------------------------
# COMPUTE SCORE
# ------------------------------------------------
def compute_score(session: Session, memory: Memory, all_tasks) -> Tuple[int, List[str]]:

    score = 0
    reasons = []
    from datetime import datetime, timezone

    now = datetime.now(timezone.utc)

    try:
        # -----------------------------
        # BASE PRIORITY
        # -----------------------------
        base = memory.priority or 50
        score += base
        reasons.append(f"priority:{base}")

        # -----------------------------
        # GOAL ALIGNMENT
        # -----------------------------
        g = goal_score(session, memory)
        if g > 0:
            score += g
            reasons.append("goal:+25")

        # -------------------------------
        # URGENCY (CREATED TIME)
        # -------------------------------
        if memory.created_at:

            created = memory.created_at

            if created.tzinfo is None:
                created = created.replace(tzinfo=timezone.utc)

            age_hours = (now - created).total_seconds() / 3600

            if age_hours < 6:
                score += 15
                reasons.append("fresh:+15")

            elif age_hours < 24:
                score += 10
                reasons.append("recent:+10")


        # ---------------------------------
        # CHECK IF BLOCKED (REAL CONTEXT)
        # ---------------------------------
        blocked, _ = is_blocked(
            {
                "id": memory.id,
                "summary": memory.summary,
                "status": memory.status,
                "depends_on": memory.depends_on
            },
            all_tasks
        )

        # ---------------------------------
        # DEADLINE / TIME PRESSURE
        # ---------------------------------
        if memory.reminder_time and not blocked:

            reminder = memory.reminder_time

            if reminder.tzinfo is None:
                reminder = reminder.replace(tzinfo=timezone.utc)

            hours_left = (reminder - now).total_seconds() / 3600

            if hours_left < 0:
                score += 30
                reasons.append("overdue:+30")

            elif hours_left < 6:
                score += 20
                reasons.append("due_soon:+20")

            elif hours_left < 24:
                score += 10
                reasons.append("upcoming:+10")


        # -------------------------------
        # KEYWORD SIGNALS
        # -------------------------------
        text = (memory.summary or "").lower()

        if "price" in text:
            score += 15
            reasons.append("price:+15")

        if "meeting" in text:
            score += 10
            reasons.append("meeting:+10")

        if "review" in text:
            score += 8
            reasons.append("review:+8")


        # ---------------------------------
        # PATTERN INTELLIGENCE (ACTIONABLE ONLY)
        # ---------------------------------
        blocked, _ = is_blocked(
            {
                "id": memory.id,
                "summary": memory.summary,
                "status": memory.status,
                "depends_on": memory.depends_on
            },
            all_tasks
        )

        if not blocked:
            if "distributor" in text:
                score += 5
                reasons.append("pattern:distributor:+5")

            if "meeting" in text:
                score += 3
                reasons.append("pattern:meeting:+3")

        # -------------------------------
        # CONTEXT: MEETING COMING SOON
        # -------------------------------
        if "meeting" in text and memory.reminder_time and not blocked:

            reminder = memory.reminder_time

            if reminder.tzinfo is None:
                reminder = reminder.replace(tzinfo=timezone.utc)

            hours_left = (reminder - now).total_seconds() / 3600

            if hours_left < 24:
                score += 10
                reasons.append("context:meeting_soon:+10")

        # -------------------------------
        # SEQUENCE AWARENESS (EXECUTION FLOW)
        # -------------------------------
        text = (memory.summary or "").lower()

        # Meeting requires preparation first (only if NOT a blocker)
        is_blocker = "confirm" in text or "venue" in text

        if "meeting" in text and memory.reminder_time and not is_blocked:
            score -= 5
            reasons.append("sequence:prep_needed:-5")

        # Preparation tasks should come earlier
        if "prepare" in text or "slides" in text or "talking points" in text:
            score += 10
            reasons.append("sequence:prep:+10")

        # Approvals unlock execution
        if "approved" in text:
            score += 12
            reasons.append("sequence:unblock:+12")

        # Review before action
        if "review" in text:
            score += 6
            reasons.append("sequence:review:+6")

        # -------------------------------
        # BLOCKER LOGIC
        # -------------------------------
        if "confirm" in text:
            score += 12
            reasons.append("blocker:+12")

        # -------------------------------
        # LATE EXECUTION PENALTY
        # -------------------------------
        if "execute" in text or "run" in text:
            score -= 5
            reasons.append("late_stage:-5")

        # -----------------------------
        # REMINDER BOOST
        # -----------------------------
        try:
            if memory.reminder_time:
                reminder = memory.reminder_time.replace(tzinfo=None)

                if reminder < datetime.utcnow():
                    score += 15
                    reasons.append("overdue:+15")

        except Exception as e:
            print("REMINDER ERROR:", e)

        # -------------------------------
        # STATUS ADJUSTMENT
        # -------------------------------
        if memory.status == "completed":
            score -= 40
            reasons.append("completed:-40")

        if memory.status == "deleted":
            score -= 100
            reasons.append("deleted:-100")

        return score, reasons

    except Exception as e:
        print("COMPUTE SCORE ERROR:", e)
        return 0, ["error"]


# ------------------------------------------------
# GET PRIORITIZED TASKS
# ------------------------------------------------
def get_prioritized_tasks(
    session: Session,
    chat_id: int,
    workspace_id: str,
    limit: int = 10
) -> List[Dict]:

    try:
        resolved_workspace_id = normalize_workspace_id(
            workspace_id
        )

        memories = session.exec(
            select(Memory).where(
                Memory.workspace_id == resolved_workspace_id,
                Memory.chat_id == chat_id,
            )
        ).all()

        print("DEBUG: MEMORIES COUNT =", len(memories))

        all_tasks = [
            {
                "id": m.id,
                "summary": m.summary,
                "status": m.status,
                "depends_on": m.depends_on
            }
            for m in memories
        ]

        results = []

        for m in memories:
            print("DEBUG: PROCESSING:", m.summary, "| status:", m.status)
            # Skip deleted items
            if m.status == "deleted":
                continue

            score, reasons = compute_score(session, m, all_tasks)

            # ---------------------------------
            # APPLY DEPENDENCY BLOCKING
            # ---------------------------------
            blocked, reason = is_blocked(
                {
                    "id": m.id,
                    "summary": m.summary,
                    "status": m.status,
                    "depends_on": m.depends_on
                },
                all_tasks
            )

            print("DEBUG: BLOCKED =", blocked, "| reason =", reason)   # ✅ ADD

            # ❗ DO NOT penalize blockers
            is_blocker = any("blocker" in str(r).lower() for r in reasons)

            if blocked and not is_blocker:
                score -= 30
                reasons.append("blocked:-30")

            print("DEBUG: ADDING TASK:", m.summary, "| score:", score)   # ✅ ADD
            results.append({
                "id": m.id,
                "summary": m.summary,
                "score": score,
                "reasons": reasons
            })

        # Sort by score descending
        results.sort(key=lambda x: x["score"], reverse=True)

        print("DEBUG: FINAL RESULTS =", results)   # ✅ ADD
        return results[:limit] if results else []

    except Exception as e:
        print("PRIORITIES ERROR:", e)
        return []


# ------------------------------------------------
# DEPENDENCY DETECTION
# ------------------------------------------------
def is_blocked(task, all_tasks):

    def is_blocked(task, all_tasks):

        # ---------------------------------------------
        # AUTO BLOCK IF HAS CHILDREN  ✅ ADD HERE
        # ---------------------------------------------
        children = []

        for t in all_tasks:
            deps = t.get("depends_on") or []

            # ✅ normalize JSON / string / int cases
            if isinstance(deps, str):
                import json
                try:
                    deps = json.loads(deps)
                except:
                    deps = []

            if not isinstance(deps, list):
                deps = [deps]

            if task.get("id") in deps:
                children.append(t)

        # now check children
        for child in children:
            if child.get("status") != "completed":
                return True, "blocked by subtasks"

        # ---------------------------------------------
        # EXPLICIT DEPENDENCIES (MULTI-LEVEL)
        # ---------------------------------------------
        deps = task.get("depends_on") or []

        if not isinstance(deps, list):
            deps = [deps]

        blocked_by = []

        for dep_id in deps:
            parent = next((t for t in all_tasks if t.get("id") == dep_id), None)

            if parent and parent.get("status") != "completed":
                blocked_by.append(parent.get("summary"))

        if blocked_by:
            return True, f"blocked by: {', '.join(blocked_by)}"

        return False, None

    # ---------------------------------------------
    # AUTO BLOCK IF HAS CHILDREN
    # ---------------------------------------------
    children = [
        t for t in all_tasks
        if t.get("depends_on") and task.get("id") in t.get("depends_on")
    ]

    for child in children:
        if child.get("status") != "completed":
            return True, f"blocked by subtasks"

    # ---------------------------------------------
    # EXISTING LOGIC (KEEP EVERYTHING BELOW)
    # ---------------------------------------------
    text = (task.get("summary") or "").lower()

    # RULE 1: meeting depends on preparation
    if "meeting" in text:
        for t in all_tasks:
            s = (t.get("summary") or "").lower()
            if "prepare" in s or "slides" in s or "talking points" in s:
                return True, "waiting for preparation"

    # RULE 2: execution depends on approval
    if "execute" in text or "run" in text:
        for t in all_tasks:
            s = (t.get("summary") or "").lower()
            if "approved" in s:
                return False, None
        return True, "waiting for approval"

    # RULE 3: meeting depends on venue
    if "meeting" in text:
        for t in all_tasks:
            s = (t.get("summary") or "").lower()
            if "confirm meeting venue" in s:
                return True, "waiting for venue"

    return False, None

# ------------------------------------------------
# GET NEXT ACTION
# ------------------------------------------------
def get_next_action(
    session,
    chat_id: int,
    workspace_id: str,
):

    try:
        print("---- NEXT ACTION START ----")

        tasks = get_prioritized_tasks(
            session,
            chat_id,
            workspace_id,
            limit=50,
        )

        if not tasks:
            return {
                "id": None,
                "summary": "No tasks found",
                "score": 0,
                "reasons": ["no data"]
            }

        # -------------------------------
        # FILTER: ONLY ACTIONABLE TASKS
        # -------------------------------
        def is_actionable(t):
            text = (t.get("summary") or "").lower()
            non_action_keywords = ["approved", "completed", "done", "closed"]
            return not any(k in text for k in non_action_keywords)

        actionable = [t for t in tasks if isinstance(t, dict) and is_actionable(t)]
        pool = actionable if actionable else tasks

        # -------------------------------
        # REMOVE BLOCKED TASKS
        # -------------------------------
        ready_tasks = []

        for t in pool:
            if not isinstance(t, dict):
                continue

            blocked, reason = is_blocked(t, pool)

            if blocked:
                print("⛔ BLOCKED:", t.get("summary"), "|", reason)
            else:
                print("✅ READY:", t.get("summary"))
                ready_tasks.append(t)

        # Always consider all tasks for blocker prioritization
        candidates = pool

        # -------------------------------
        # PRIORITIZE BLOCKERS FIRST
        # -------------------------------
        blockers = []

        for t in candidates:
            reasons = t.get("reasons", [])

            if any("blocker" in str(r).lower() for r in reasons):
                print("🔥 BLOCKER DETECTED:", t.get("summary"))
                blockers.append(t)

        # ---------------------------------
        # PRIORITIZE BLOCKERS + TOP OTHERS
        # ---------------------------------
        sorted_candidates = sorted(
            candidates,
            key=lambda x: x.get("score", 0),
            reverse=True
        )

        if blockers:
            # keep blockers first, then fill remaining slots
            non_blockers = [t for t in sorted_candidates if t not in blockers]
            priority_pool = blockers + non_blockers
        else:
            priority_pool = sorted_candidates
        # -------------------------------
        # SELECT TOP 3 ACTIONS
        # -------------------------------
        sorted_tasks = sorted(
            priority_pool,
            key=lambda x: x.get("score", 0),
            reverse=True
        )

        top_tasks = sorted_tasks[:3]

        print("✅ TOP TASKS:", top_tasks)

        return top_tasks

    except Exception as e:
        import traceback
        print("🔥 NEXT ACTION ERROR:")
        traceback.print_exc()

        return {
            "id": None,
            "summary": "Error computing next action",
            "score": 0,
            "reasons": ["error"]
        }
