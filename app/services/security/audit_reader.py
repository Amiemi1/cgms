from sqlmodel import select
from app.db.models import SecurityLog


def get_security_logs(session, limit=10):

    logs = session.exec(
        select(SecurityLog)
        .order_by(SecurityLog.created_at.desc())
        .limit(limit)
    ).all()

    return logs