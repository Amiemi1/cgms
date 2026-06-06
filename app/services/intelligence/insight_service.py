from typing import List, Dict
from app.services.intelligence.prioritization_service import get_prioritized_tasks

def generate_insights(tasks: List[Dict]) -> List[Dict]:
    insights = []

    def has_reason(t, key):
        return any(key in str(r).lower() for r in t.get("reasons", []))

    # ✅ ADD THIS HERE (RIGHT BELOW)
    def is_executable(task, all_tasks):
        depends_on = task.get("depends_on")

        if not depends_on:
            return True

        for parent_id in depends_on:
            parent = next((t for t in all_tasks if t.get("id") == parent_id), None)

            if parent and parent.get("status") != "completed":
                return False

        return True

    # -------------------------------
    # 1) UNBLOCKING (WITH WHY)
    # -------------------------------
    blockers = [t for t in tasks if has_reason(t, "blocker")]

    if blockers:
        top_blocker = sorted(blockers, key=lambda x: x.get("score", 0), reverse=True)[0]
        insights.append({
            "type": "action",
            "priority": 1,
            "message": f"Unblock now: {top_blocker['summary']} — required to proceed"
        })

    # -------------------------------
    # 2) BLOCKED CHAIN (CLEAR COUNT)
    # -------------------------------
    blocked = [t for t in tasks if has_reason(t, "blocked")]

    if blocked and blockers:
        insights.append({
            "type": "explain",
            "priority": 2,
            "message": f"{len(blocked)} task(s) are blocked by unmet dependencies"
        })

    # -------------------------------
    # 3) CLUSTER / FOCUS AREA
    # -------------------------------
    distributor_tasks = [
        t for t in tasks
        if any("distributor" in str(r).lower() for r in t.get("reasons", []))
    ]
    if len(distributor_tasks) >= 2:
        insights.append({
            "type": "cluster",
            "priority": 3,
            "message": f"{len(distributor_tasks)} distributor-related actions active"
        })

    # -------------------------------
    # 4) SEQUENCE GUIDANCE
    # -------------------------------
    meeting_exists = any("meeting" in (t.get("summary") or "").lower() for t in tasks)
    prep_exists = any(
        "prepare" in (t.get("summary") or "").lower()
        or "slides" in (t.get("summary") or "").lower()
        or "talking points" in (t.get("summary") or "").lower()
        for t in tasks
    )


    if meeting_exists and prep_exists:
        insights.append({
            "type": "guidance",
            "priority": 1.1,
            "message": "Prepare materials before the meeting to avoid execution gaps"
        })

    # -------------------------------
    # 5) NEXT FOCUS (SMART + SAFE)
    # -------------------------------

    # ✅ STEP 1: FILTER FIRST (ONLY EXECUTABLE TASKS)
    filtered_tasks = []
    for t in tasks:
        reasons = [str(r).lower() for r in t.get("reasons", [])]

        status = t.get("status")

        is_blocked = any("blocked" in r for r in reasons)
        is_blocker = any("blocker" in r for r in reasons)
        is_completed = status == "completed"

        if (
            not is_blocked
            and not is_completed
            and not is_blocker
            and is_executable(t, tasks)
        ):
            filtered_tasks.append(t)

    # ✅ STEP 2: SORT ONLY VALID TASKS
    prioritized_tasks = sorted(filtered_tasks, key=lambda x: x.get("score", 0), reverse=True)

    # ✅ STEP 3: PICK BEST
    top = prioritized_tasks[0] if prioritized_tasks else None

    # -------------------------------
    # FORESIGHT — WHAT THIS ENABLES NEXT
    # -------------------------------
    if top:
        children = [
            t for t in tasks
            if top.get("id") in (t.get("depends_on") or [])
        ]

        if children:
            next_steps = [c.get("summary") for c in children][:2]

            insights.append({
                "type": "foresight",
                "priority": 0.6,
                "message": f"Next steps unlocked: {', '.join(next_steps)}"
            })


    # -------------------------------
    # STRATEGIC GROUPING — WORKSTREAM
    # -------------------------------
    prep_tasks = [
        t for t in tasks
        if "prepare" in (t.get("summary") or "").lower()
        or "talking" in (t.get("summary") or "").lower()
        or "slides" in (t.get("summary") or "").lower()
    ]

    if len(prep_tasks) >= 2:
        insights.append({
            "type": "strategy",
            "priority": 1.0,
            "message": f"{len(prep_tasks)} preparation-related tasks forming a workstream"
        })

    if top:
        insights.append({
            "type": "focus",
            "priority": 0,
            "message": f"Focus next: {top['summary']}",
            "id": top.get("id"),
            "meta": "subtask" if top.get("depends_on") else "primary"
        })

        # -------------------------------
        # NO ACTIVE TASKS (SYSTEM COMPLETE)
        # -------------------------------
        if not top:
            insights.append({
                "type": "meta",
                "priority": 0,
                "message": "✅ All tasks completed — you’re clear. Add new tasks or define the next objective."
            })    

        # -------------------------------
        # META-COGNITION — WHY THIS WAS SELECTED
        # -------------------------------
        insights.append({
            "type": "meta",
            "priority": 0.2,
            "message": "Selected as the highest-priority executable task based on dependencies and status"
        })

    # -------------------------------
    # ADAPTIVE GUIDANCE — CONTEXTUAL COACHING
    # -------------------------------
    if top:
        summary = (top.get("summary") or "").lower()

        coaching_message = ""

        if "prepare" in summary or "talking" in summary:
            coaching_message = "Focus on structuring key points first, then refine supporting data"

        elif "review" in summary:
            coaching_message = "Look for gaps, trends, and inconsistencies before forming conclusions"

        elif "meeting" in summary:
            coaching_message = "Ensure clarity of objectives and expected outcomes before the meeting"

        elif "price" in summary:
            coaching_message = "Validate impact and stakeholder alignment before execution"

        if coaching_message:
            insights.append({
                "type": "coaching",
                "priority": 1.2,
                "message": coaching_message
            })

    # -------------------------------
    # WHY THIS IS THE NEXT ACTION
    # -------------------------------
    reason_map = {
        "priority": "high priority",
        "goal": "aligned to goal",
        "review": "requires evaluation",
        "sequence": "correct execution order",
        "blocker": "unblocks other tasks"
    }

    if not top:
        return insights

    reasons = top.get("reasons", [])

    clean = []
    for r in reasons:
        for key in reason_map:
            if key in r:
                clean.append(reason_map[key])

    clean = list(dict.fromkeys(clean))[:2]  # remove duplicates, take top 2

    if clean:
        # -------------------------------
        # CONTEXT-AWARE WHY
        # -------------------------------
        context_reason = ""

        summary = (top.get("summary") or "").lower()

        if "review" in summary:
            context_reason = "provides insight needed for decision-making"

        elif "meeting" in summary:
            context_reason = "ensures readiness before scheduled discussion"

        elif "prepare" in summary:
            context_reason = "prevents last-minute execution gaps"

        elif "price" in summary:
            context_reason = "impacts commercial performance"

        base = ", ".join(clean)

        if context_reason:
            message = f"Why now: {base} — {context_reason}"
        else:
            message = f"Why now: {base}"

        insights.append({
            "type": "why",
            "priority": 0.5,
            "message": message
        })

        # -------------------------------
        # RISK / CONSEQUENCE IF DELAYED
        # -------------------------------
        risk_message = ""

        summary = (top.get("summary") or "").lower()

        if "review" in summary:
            risk_message = "Decisions may be made without proper performance insight"

        elif "meeting" in summary:
            risk_message = "Meeting effectiveness may be reduced due to poor preparation"

        elif "prepare" in summary:
            risk_message = "Execution quality may drop due to lack of readiness"

        elif "price" in summary:
            risk_message = "Revenue impact may occur due to delayed pricing action"

        # Only add if we found a risk
        if risk_message:
            insights.append({
                "type": "risk",
                "priority": 0.7,
                "message": f"Risk: {risk_message}"
            })

            # -------------------------------
            # UNLOCK / WHAT THIS ENABLES
            # -------------------------------
            unlock_message = ""

            summary = (top.get("summary") or "").lower()

            if "review" in summary:
                unlock_message = "Enables informed decisions and stronger execution planning"

            elif "meeting" in summary:
                unlock_message = "Enables a productive meeting with clear outcomes"

            elif "prepare" in summary:
                unlock_message = "Enables smooth execution without last-minute gaps"

            elif "price" in summary:
                unlock_message = "Enables timely market execution and revenue capture"

            if unlock_message:
                insights.append({
                    "type": "unlock",
                    "priority": 0.8,
                    "message": f"Unlock: {unlock_message}"
                })

    # -------------------------------
    # REMOVE DUPLICATES
    # -------------------------------
    seen = set()
    cleaned = []

    for ins in insights:
        msg = ins.get("message")
        if msg not in seen:
            cleaned.append(ins)
            seen.add(msg)

    insights = cleaned

    # -------------------------------
    # SORT BY PRIORITY
    # -------------------------------

    insights = sorted(insights, key=lambda x: x.get("priority", 99))
    return insights