# ==============================================================
# GOVERNANCE AUDIT SERVICE
# ==============================================================

import json

from sqlmodel import select

from app.db.models.audit_record import AuditRecord
from app.services.persistence.audit_store import (
    GOVERNANCE_AUDIT,
    add_audit_record,
)


def record_audit(
    session,
    user_id,
    action,
    details,
    *,
    workspace_id=None,
    subject_type="account",
    subject_id=None,
    commit=True,
):

    print(f"[DEBUG] Governance | Audit record | user={user_id} action={action}")

    record = add_audit_record(
        session,
        category=GOVERNANCE_AUDIT,
        action=action,
        source="governance_service",
        workspace_id=workspace_id,
        actor_id=user_id,
        subject_type=subject_type,
        subject_id=(
            subject_id
            if subject_id is not None
            else user_id
        ),
        outcome="changed",
        details={
            "message": details,
        },
    )

    if commit:
        session.commit()

    return record


def get_recent_audit(
    session,
    limit=10,
    *,
    workspace_id=None,
):

    statement = select(AuditRecord).where(
        AuditRecord.category
        == GOVERNANCE_AUDIT
    )

    if workspace_id is None:
        statement = statement.where(
            AuditRecord.workspace_id.is_(
                None
            )
        )
    else:
        statement = statement.where(
            AuditRecord.workspace_id
            == workspace_id
        )

    records = session.exec(
        statement.order_by(
            AuditRecord.occurred_at.desc(),
            AuditRecord.id.desc(),
        ).limit(limit)
    ).all()

    return [
        (
            record.actor_id,
            record.action,
            json.dumps(
                record.details,
                sort_keys=True,
            ),
            record.occurred_at,
        )
        for record in records
    ]
