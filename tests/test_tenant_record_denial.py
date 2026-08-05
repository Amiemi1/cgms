from __future__ import annotations

from sqlalchemy.pool import StaticPool
from sqlmodel import Field, Session, SQLModel, create_engine

from app.services.workspace.tenant_scope import load_scoped_record


class DenialRecord(SQLModel, table=True):
    __tablename__ = "pwi_001_tenant_denial_record"

    id: int | None = Field(default=None, primary_key=True)
    workspace_id: str = Field(index=True)
    value: str


def external_lookup(
    session: Session,
    record_id: int,
    workspace_id: str,
) -> dict[str, str]:
    record = load_scoped_record(
        session,
        DenialRecord,
        record_id,
        workspace_id,
    )

    if record is None:
        return {
            "status": "not_found",
            "detail": "Record not found",
        }

    return {
        "status": "found",
        "detail": record.value,
    }


def test_missing_and_cross_workspace_records_share_denial_contract() -> None:
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    DenialRecord.__table__.create(engine, checkfirst=True)

    with Session(engine) as session:
        other = DenialRecord(
            workspace_id="workspace-b",
            value="other tenant",
        )
        session.add(other)
        session.commit()
        session.refresh(other)

        cross_workspace = external_lookup(
            session,
            other.id,
            "workspace-a",
        )
        missing = external_lookup(
            session,
            999_999,
            "workspace-a",
        )

    assert cross_workspace == missing == {
        "status": "not_found",
        "detail": "Record not found",
    }
    assert "workspace-b" not in str(cross_workspace)
