import json

from sqlmodel import Session, select

from app.db.session import engine
from app.db.models.memory import Memory
from app.db.models.memory_score import MemoryScore
from app.services.workspace.tenant_scope import (
    inherit_workspace_id,
    load_scoped_record,
    normalize_workspace_id,
)


SCORE_CACHE = {}


def _cache_key(
    workspace_id: str,
    memory_id: int,
) -> tuple[str, int]:
    return (
        normalize_workspace_id(workspace_id),
        int(memory_id),
    )


def save_score(
    memory_id: int,
    score: dict,
    workspace_id: str,
):
    resolved_workspace_id = normalize_workspace_id(workspace_id)

    with Session(engine) as session:
        memory = load_scoped_record(
            session,
            Memory,
            memory_id,
            resolved_workspace_id,
        )

        if memory is None:
            return None

        authoritative_workspace_id = inherit_workspace_id(memory)
        key = _cache_key(
            authoritative_workspace_id,
            memory_id,
        )
        SCORE_CACHE[key] = score

        existing = session.exec(
            select(MemoryScore).where(
                MemoryScore.workspace_id
                == authoritative_workspace_id,
                MemoryScore.memory_id == memory_id
            )
        ).first()

        payload = {
            "workspace_id": authoritative_workspace_id,
            "memory_id": memory_id,
            "importance": score["importance"],
            "confidence": score["confidence"],
            "freshness": score["freshness"],
            "priority": score["priority"],
            "composite": score["composite"],
            "factors_json": json.dumps(
                score.get(
                    "factors",
                    {}
                )
            ),
        }

        if existing:

            for key_name, value in payload.items():

                setattr(
                    existing,
                    key_name,
                    value
                )

            session.add(
                existing
            )

        else:

            session.add(
                MemoryScore(
                    **payload
                )
            )

        session.commit()

    return SCORE_CACHE[key]


def get_score(
    memory_id: int,
    workspace_id: str,
):
    resolved_workspace_id = normalize_workspace_id(workspace_id)
    key = _cache_key(
        resolved_workspace_id,
        memory_id,
    )
    cached = SCORE_CACHE.get(key)

    if cached:

        return cached

    with Session(engine) as session:

        score = session.exec(
            select(MemoryScore).where(
                MemoryScore.workspace_id
                == resolved_workspace_id,
                MemoryScore.memory_id == memory_id
            )
        ).first()

        if not score:

            return None

        return {
            "importance": score.importance,
            "confidence": score.confidence,
            "freshness": score.freshness,
            "priority": score.priority,
            "composite": score.composite,
            "factors": json.loads(
                score.factors_json
            ),
            "version": score.version,
            "last_calculated": str(
                score.last_calculated
            )
        }


def get_all_scores(
    workspace_id: str,
):
    resolved_workspace_id = normalize_workspace_id(workspace_id)

    with Session(engine) as session:

        scores = session.exec(
            select(MemoryScore).where(
                MemoryScore.workspace_id
                == resolved_workspace_id
            )
        ).all()

        return [
            {
                "memory_id": s.memory_id,
                "importance": s.importance,
                "confidence": s.confidence,
                "freshness": s.freshness,
                "priority": s.priority,
                "composite": s.composite,
                "version": s.version,
                "last_calculated": str(
                    s.last_calculated
                )
            }
            for s in scores
        ]


def get_memory_intelligence_dashboard(
    workspace_id: str,
):

    scores = get_all_scores(workspace_id)

    total = len(scores)

    if total == 0:

        return {
            "total_memories": 0,
            "average_composite": 0,
            "high_priority": 0,
            "low_confidence": 0,
            "top_memories": []
        }

    average = round(
        sum(
            s["composite"]
            for s in scores
        )
        / total,
        2
    )

    high_priority = len([
        s for s in scores
        if s["priority"] >= 80
    ])

    low_confidence = len([
        s for s in scores
        if s["confidence"] < 60
    ])

    top_memories = sorted(
        scores,
        key=lambda x: x["composite"],
        reverse=True
    )[:10]

    return {
        "total_memories": total,
        "average_composite": average,
        "high_priority": high_priority,
        "low_confidence": low_confidence,
        "top_memories": top_memories
    }
