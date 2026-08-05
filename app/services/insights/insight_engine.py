from sqlmodel import select
from collections import Counter
from datetime import datetime, timedelta

from app.db.session import SessionLocal
from app.db.models.memory import Memory
from app.db.models.insight import Insight
from app.db.models.memory_relationship import MemoryRelationship
from app.services.workspace.tenant_scope import normalize_workspace_id


def generate_insights(
    chat_id: int,
    workspace_id: str,
):

    session = SessionLocal()

    scored_insights = []
    resolved_workspace_id = normalize_workspace_id(workspace_id)

    try:

        memories = session.exec(
            select(Memory).where(
                Memory.workspace_id == resolved_workspace_id,
                Memory.chat_id == chat_id,
            )
        ).all()

        memory_ids = [m.id for m in memories if m.id is not None]

        relationships = (
            session.exec(
                select(MemoryRelationship).where(
                    MemoryRelationship.workspace_id
                    == resolved_workspace_id,
                    MemoryRelationship.source_memory_id.in_(
                        memory_ids
                    ),
                )
            ).all()
            if memory_ids
            else []
        )

        memory_map = {m.id: m for m in memories}

        now = datetime.utcnow()

        # ------------------------------------------------
        # GRAPH INSIGHTS
        # ------------------------------------------------

        for rel in relationships:

            if rel.relationship_type == "triggered_by":

                task = memory_map.get(rel.source_memory_id)
                event = memory_map.get(rel.target_memory_id)

                if task and event:

                    scored_insights.append({
                        "score": 80,
                        "message": f"Task '{task.summary}' is required for event '{event.summary}'."
                    })

            if rel.relationship_type == "resolves":

                decision = memory_map.get(rel.source_memory_id)
                task = memory_map.get(rel.target_memory_id)

                if decision and task:

                    scored_insights.append({
                        "score": 90,
                        "message": f"Decision '{decision.summary}' impacts task '{task.summary}'."
                    })

        # ------------------------------------------------
        # UPCOMING EVENTS
        # ------------------------------------------------

        upcoming = [
            m for m in memories
            if m.memory_type == "event"
            and m.reminder_time
            and m.reminder_time < now + timedelta(hours=24)
        ]

        for event in upcoming:

            scored_insights.append({
                "score": 100,
                "message": f"Upcoming event within 24 hours: {event.summary}"
            })

        # ------------------------------------------------
        # TASKS WITHOUT DECISIONS
        # ------------------------------------------------

        for task in memories:

            if task.memory_type != "task":
                continue

            rel = [
                r for r in relationships
                if r.target_memory_id == task.id
                and r.relationship_type == "resolves"
            ]

            if not rel:

                scored_insights.append({
                    "score": 85,
                    "message": f"Task awaiting decision: {task.summary}"
                })

        # ------------------------------------------------
        # TOPIC PATTERN DETECTION
        # ------------------------------------------------

        stopwords = {"prepare", "meeting", "task", "plan", "slides"}

        words = []

        for m in memories:

            tokens = m.summary.lower().split()

            for token in tokens:

                if len(token) > 4 and token not in stopwords:
                    words.append(token)

        common = Counter(words).most_common(3)

        for word, count in common:

            if count >= 3:

                scored_insights.append({
                    "score": 50,
                    "message": f"You appear to be focusing heavily on '{word}' related activities."
                })

        # ------------------------------------------------
        # MEMORY TYPE BALANCE
        # ------------------------------------------------

        types = Counter([m.memory_type for m in memories])

        if types["task"] > types["decision"]:

            scored_insights.append({
                "score": 40,
                "message": "You have more tasks than decisions. Some tasks may require approvals."
            })

        if types["event"] > 0 and types["task"] == 0:

            scored_insights.append({
                "score": 40,
                "message": "You have events scheduled but no supporting tasks."
            })

        # ------------------------------------------------
        # RANK AND DEDUPLICATE INSIGHTS
        # ------------------------------------------------

        unique = {}

        for item in scored_insights:

            msg = item["message"]
            score = item["score"]

            if msg not in unique or score > unique[msg]:
                unique[msg] = score

        sorted_insights = sorted(
            [{"message": m, "score": s} for m, s in unique.items()],
            key=lambda x: x["score"],
            reverse=True
        )

        final_insights = [i["message"] for i in sorted_insights[:10]]

        # ------------------------------------------------
        # STORE INSIGHTS
        # ------------------------------------------------

        for msg in final_insights:

            insight = Insight(
                workspace_id=resolved_workspace_id,
                chat_id=chat_id,
                message=msg,
                insight_type="predictive"
            )

            session.add(insight)

        session.commit()

        return final_insights

    finally:
        session.close()
