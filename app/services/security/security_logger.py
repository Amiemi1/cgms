from datetime import datetime
from app.db.models import SecurityLog
from app.services.persistence.audit_store import (
    SECURITY_AUDIT,
    add_audit_record,
)


def log_security_event(session, chat_id, action, details):

    log = SecurityLog(
        user_id=chat_id,
        action=action,
        details=details,
        created_at=datetime.utcnow()
    )

    session.add(log)
    session.flush()
    add_audit_record(
        session,
        category=SECURITY_AUDIT,
        action=action,
        source="security_guard",
        actor_id=chat_id,
        outcome="denied",
        details={
            "message": details,
        },
        occurred_at=log.created_at,
        origin_id=(
            "legacy.security_log:"
            f"{log.id}"
        ),
    )
    session.commit()
