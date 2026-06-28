import json

from sqlmodel import Session, select

from app.db.session import engine
from app.db.models.memory_score import MemoryScore


SCORE_CACHE = {}


def save_score(
    memory_id: int,
    score: dict
):

    SCORE_CACHE[
        memory_id
    ] = score

    with Session(engine) as session:

        existing = session.exec(
            select(MemoryScore).where(
                MemoryScore.memory_id == memory_id
            )
        ).first()

        payload = {
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

            for key, value in payload.items():

                setattr(
                    existing,
                    key,
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

    return SCORE_CACHE[
        memory_id
    ]


def get_score(
    memory_id: int
):

    cached = SCORE_CACHE.get(
        memory_id
    )

    if cached:

        return cached

    with Session(engine) as session:

        score = session.exec(
            select(MemoryScore).where(
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


def get_all_scores():

    with Session(engine) as session:

        scores = session.exec(
            select(MemoryScore)
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
    
def get_memory_intelligence_dashboard():

    scores = get_all_scores()

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