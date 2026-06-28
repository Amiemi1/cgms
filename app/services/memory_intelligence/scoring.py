from app.services.memory_intelligence.models import MemoryScore


def clamp(value: int) -> int:
    return max(0, min(100, int(value)))


def calculate_memory_score(memory) -> MemoryScore:

    memory_type = getattr(memory, "memory_type", "note")
    status = getattr(memory, "status", "active")
    explicit_priority = getattr(memory, "priority", None)

    type_weight = {
        "decision": 90,
        "task": 80,
        "goal": 75,
        "insight": 70,
        "event": 60,
        "note": 50,
    }.get(memory_type, 50)

    status_weight = {
        "active": 80,
        "completed": 50,
        "archived": 30,
        "deleted": 0,
    }.get(status, 60)

    importance = clamp(type_weight)
    confidence = 80
    freshness = 75

    if explicit_priority is not None:
        priority = clamp(explicit_priority)
    else:
        priority = clamp(
            round(
                (type_weight * 0.6)
                +
                (status_weight * 0.4)
            )
        )

    composite = clamp(
        round(
            importance * 0.40
            + confidence * 0.25
            + priority * 0.20
            + freshness * 0.15
        )
    )

    return MemoryScore(
        importance=importance,
        confidence=confidence,
        freshness=freshness,
        priority=priority,
        composite=composite,
        factors={
            "memory_type": type_weight,
            "status": status_weight,
            "explicit_priority": priority,
        },
    )