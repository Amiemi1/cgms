from __future__ import annotations

import pytest

from app.db.models.candidate_memory import CandidateMemory
from app.db.models.decision_lineage import DecisionLineage
from app.db.models.goal import Goal
from app.db.models.insight import Insight
from app.db.models.learning import Learning
from app.db.models.learning_log import LearningLog
from app.db.models.memory import Memory
from app.db.models.memory_access import MemoryAccess
from app.db.models.memory_relationship import MemoryRelationship
from app.db.models.memory_score import MemoryScore
from app.db.models.message import Message


TENANT_MODELS = (
    CandidateMemory,
    DecisionLineage,
    Goal,
    Insight,
    Learning,
    LearningLog,
    Memory,
    MemoryAccess,
    MemoryRelationship,
    MemoryScore,
    Message,
)


@pytest.mark.parametrize("model", TENANT_MODELS)
def test_tenant_model_requires_workspace_id(model) -> None:
    field = model.model_fields["workspace_id"]
    column = model.__table__.c.workspace_id

    assert field.is_required()
    assert column.nullable is False
    assert column.index is True
    assert getattr(column.type, "length", None) == 64


def test_all_expected_tenant_models_are_covered() -> None:
    assert {model.__name__ for model in TENANT_MODELS} == {
        "CandidateMemory",
        "DecisionLineage",
        "Goal",
        "Insight",
        "Learning",
        "LearningLog",
        "Memory",
        "MemoryAccess",
        "MemoryRelationship",
        "MemoryScore",
        "Message",
    }
