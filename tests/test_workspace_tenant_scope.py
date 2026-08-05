from __future__ import annotations

import pytest
from sqlalchemy.pool import StaticPool
from sqlmodel import Field, Session, SQLModel, create_engine

from app.services.auth.auth_dependency import AuthenticatedPrincipal
from app.services.workspace.tenant_scope import (
    TenantScopeError,
    belongs_to_workspace,
    bind_workspace,
    get_current_workspace_id,
    inherit_workspace_id,
    load_scoped_record,
    normalize_workspace_id,
    resolve_legacy_workspace_id,
    scoped_select,
)


class TenantScopeExample(SQLModel, table=True):
    __tablename__ = "pwi_001_tenant_scope_example"

    id: int | None = Field(
        default=None,
        primary_key=True,
    )
    workspace_id: str = Field(index=True)
    value: str


def build_engine():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TenantScopeExample.__table__.create(
        engine,
        checkfirst=True,
    )
    return engine


@pytest.mark.parametrize(
    "workspace_id",
    (
        None,
        "",
        "   ",
        "contains/slash",
        "x" * 65,
    ),
)
def test_rejects_invalid_workspace_ids(
    workspace_id,
) -> None:
    with pytest.raises(
        TenantScopeError,
        match="Workspace context is invalid",
    ):
        normalize_workspace_id(workspace_id)


def test_legacy_resolution_is_explicit() -> None:
    assert resolve_legacy_workspace_id() == "default"



def test_authenticated_workspace_resolution_uses_principal() -> None:
    principal = AuthenticatedPrincipal(
        user_id="1",
        workspace_id="Workspace-A",
        role="viewer",
        permissions=frozenset(),
    )

    assert get_current_workspace_id(principal) == "workspace-a"


def test_authenticated_workspace_resolution_fails_closed() -> None:
    with pytest.raises(
        TenantScopeError,
        match="Authenticated workspace context is required",
    ):
        get_current_workspace_id(None)

def test_binds_and_inherits_workspace() -> None:
    record = TenantScopeExample(
        workspace_id="default",
        value="record",
    )

    assert bind_workspace(record, "default") is record
    assert inherit_workspace_id(record) == "default"
    assert belongs_to_workspace(record, "default")
    assert not belongs_to_workspace(record, "other")

    with pytest.raises(
        TenantScopeError,
        match="ownership conflicts",
    ):
        bind_workspace(record, "other")


def test_scoped_load_does_not_disclose_other_workspace() -> None:
    engine = build_engine()

    with Session(engine) as session:
        own = TenantScopeExample(
            workspace_id="workspace-a",
            value="own",
        )
        other = TenantScopeExample(
            workspace_id="workspace-b",
            value="other",
        )
        session.add(own)
        session.add(other)
        session.commit()
        session.refresh(own)
        session.refresh(other)

        selected = session.exec(
            scoped_select(
                TenantScopeExample,
                "workspace-a",
            )
        ).all()

        assert [
            record.value
            for record in selected
        ] == ["own"]

        assert (
            load_scoped_record(
                session,
                TenantScopeExample,
                own.id,
                "workspace-a",
            )
            is not None
        )
        assert (
            load_scoped_record(
                session,
                TenantScopeExample,
                other.id,
                "workspace-a",
            )
            is None
        )
        assert (
            load_scoped_record(
                session,
                TenantScopeExample,
                999_999,
                "workspace-a",
            )
            is None
        )
