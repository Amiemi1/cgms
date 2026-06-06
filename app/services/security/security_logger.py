from datetime import datetime
from app.db.models import SecurityLog


def log_security_event(session, chat_id, action, details):

    log = SecurityLog(
        chat_id=chat_id,
        action=action,
        details=details,
        created_at=datetime.utcnow()
    )

    session.add(log)
    session.commit()