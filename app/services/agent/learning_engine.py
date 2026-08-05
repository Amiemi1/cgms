# =====================================================
# LEARNING ENGINE
# Records actions taken by the system
# =====================================================

from datetime import datetime
from app.db.models.learning_log import LearningLog
from app.services.workspace.tenant_scope import normalize_workspace_id


def record_action(
    session,
    action: str,
    context: str,
    result: str,
    workspace_id: str,
):
    log = LearningLog(
        workspace_id=normalize_workspace_id(workspace_id),
        action=action,
        context=context,
        result=result,
        created_at=datetime.utcnow()
    )

    session.add(log)
    session.commit()

    print("LEARNING RECORDED:", action)
