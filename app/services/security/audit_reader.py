from sqlmodel import select
from app.db.models.audit_record import AuditRecord
from app.services.persistence.audit_store import (
    SECURITY_AUDIT,
)


def get_security_logs(
    session,
    workspace_id: str,
    limit=10,
):

    logs = session.exec(
        select(AuditRecord)
        .where(
            AuditRecord.category
            == SECURITY_AUDIT,
            AuditRecord.workspace_id
            == workspace_id,
        )
        .order_by(
            AuditRecord.occurred_at.desc()
        )
        .limit(limit)
    ).all()

    return logs
