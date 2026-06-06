# =====================================================
# LEARNING ENGINE
# Records actions taken by the system
# =====================================================

from datetime import datetime
from app.db.models.learning_log import LearningLog


def record_action(session, action: str, context: str, result: str):

    log = LearningLog(
        action=action,
        context=context,
        result=result,
        created_at=datetime.utcnow()
    )

    session.add(log)
    session.commit()

    print("LEARNING RECORDED:", action)