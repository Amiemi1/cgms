from pathlib import Path


FILES = {
    # Sprint 9 — Admin Console + Tenant Governance
    "app/services/workspace/admin.py": "",
    "app/services/workspace/quotas.py": "",
    "app/services/workspace/access_control.py": "",
    "app/dashboard/routes/workspace_admin.py": "",
    "app/dashboard/routes/workspace_quotas.py": "",
    "tests/test_workspace_admin.py": "",

    # Sprint 10 — Real Connector Adapters
    "app/services/connectors/slack_adapter.py": "",
    "app/services/connectors/teams_adapter.py": "",
    "app/services/connectors/gmail_adapter.py": "",
    "app/services/connectors/calendar_adapter.py": "",
    "app/dashboard/routes/connector_adapters.py": "",
    "tests/test_connector_adapters.py": "",

    # Sprint 11 — Persistent Storage Hardening
    "app/services/persistence/workspace_store.py": "",
    "app/services/persistence/connector_store.py": "",
    "app/services/persistence/audit_store.py": "",
    "app/services/persistence/session_store.py": "",
    "tests/test_persistence_layer.py": "",

    # Sprint 12 — UX / Admin Dashboard API
    "app/dashboard/routes/admin_summary.py": "",
    "app/dashboard/routes/product_console.py": "",
    "app/services/product/readiness.py": "",
    "tests/test_admin_summary.py": "",

    # Sprint 13 — Commercial / Packaging Layer
    "app/services/commercial/plan_registry.py": "",
    "app/services/commercial/billing_meter.py": "",
    "app/dashboard/routes/commercial.py": "",
    "tests/test_commercial_layer.py": "",

    # Sprint 14 — Patent / IP Expansion
    "docs/patent_expansion_notes.md": "",
    "docs/architecture_claims.md": "",
    "docs/runtime_governance_claims.md": "",

    # Sprint 15 — Release Readiness
    "docs/deployment_checklist.md": "",
    "docs/admin_guide.md": "",
    "docs/api_reference.md": "",
    "tests/test_release_readiness.py": "",
}


INIT_DIRS = [
    "app/services/workspace",
    "app/services/connectors",
    "app/services/persistence",
    "app/services/product",
    "app/services/commercial",
]


def create_file(path: str, content: str = ""):
    file_path = Path(path)
    file_path.parent.mkdir(parents=True, exist_ok=True)

    if file_path.exists():
        print(f"SKIPPED existing: {path}")
        return

    file_path.write_text(content, encoding="utf-8")
    print(f"CREATED: {path}")


def main():
    for folder in INIT_DIRS:
        init_file = Path(folder) / "__init__.py"
        create_file(str(init_file), "")

    for path, content in FILES.items():
        create_file(path, content)

    print("\n✅ Future sprint scaffold complete")


if __name__ == "__main__":
    main()