from __future__ import annotations

import hashlib
import io
import json
import zipfile
from datetime import datetime, timezone

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.dashboard.main import app as production_app
from app.dashboard.routes.patent_evidence_export import (
    get_patent_export_service,
    router as patent_export_router,
)
from app.services.auth.jwt_handler import (
    create_access_token,
)
from app.services.patent_governance.evidence_registry import (
    PatentEvidenceRegistry,
)
from app.services.patent_governance.export_service import (
    PatentEvidenceExportService,
)
from app.services.patent_governance.innovation_registry import (
    PatentInnovationRegistry,
)
from app.services.patent_governance.registry import (
    PatentGovernanceRegistry,
)


TEST_JWT_SECRET = (
    "cgms-export-test-secret-with-more-than-32-characters"
)

FIXED_EXPORT_TIME = datetime(
    2026,
    7,
    21,
    12,
    30,
    0,
    tzinfo=timezone.utc,
)

EXPECTED_PACKAGE_FILES = {
    "README.md",
    "manifest.json",
    "checksums.sha256",
    "governance/governance_snapshot.json",
    "governance/dashboard_summary.json",
    "governance/governance_notices.md",
    "governance/filings.csv",
    "governance/milestones.csv",
    "evidence/evidence_snapshot.json",
    "evidence/documents.csv",
    "evidence/evidence_items.csv",
    "evidence/verifications.csv",
    "evidence/collections.csv",
    "innovation/innovation_snapshot.json",
    "innovation/innovations.csv",
    "innovation/claim_candidates.csv",
    "innovation/innovation_claim_links.csv",
    "innovation/coverage_assessments.csv",
}

RAW_IDENTIFIERS = {
    "63/987,873",
    "63987873",
    "8158",
    "225429",
    "74563697",
}


@pytest.fixture(autouse=True)
def configure_test_jwt(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv(
        "CGMS_JWT_SECRET",
        TEST_JWT_SECRET,
    )

    monkeypatch.setenv(
        "CGMS_JWT_EXPIRE_MINUTES",
        "60",
    )

    monkeypatch.setenv(
        "CGMS_JWT_ISSUER",
        "cgms-export-test",
    )

    monkeypatch.setenv(
        "CGMS_JWT_AUDIENCE",
        "cgms-export-dashboard-test",
    )


def build_export_service() -> PatentEvidenceExportService:
    governance_registry = PatentGovernanceRegistry()

    evidence_registry = PatentEvidenceRegistry(
        governance_registry
    )

    innovation_registry = PatentInnovationRegistry(
        governance_registry,
        evidence_registry,
    )

    return PatentEvidenceExportService(
        governance_registry=governance_registry,
        evidence_registry=evidence_registry,
        innovation_registry=innovation_registry,
    )


def build_isolated_client() -> TestClient:
    isolated_app = FastAPI()

    service = build_export_service()

    isolated_app.dependency_overrides[
        get_patent_export_service
    ] = lambda: service

    isolated_app.include_router(
        patent_export_router
    )

    return TestClient(isolated_app)


def create_test_token(
    role: str,
    *,
    user_id: str = "export-test-user",
) -> str:
    return create_access_token(
        {
            "user_id": user_id,
            "role": role,
        }
    )


def bearer_headers(
    token: str,
    **additional_headers: str,
) -> dict[str, str]:
    headers = {
        "Authorization": f"Bearer {token}",
    }

    headers.update(additional_headers)

    return headers


def open_package(
    content: bytes,
) -> zipfile.ZipFile:
    return zipfile.ZipFile(
        io.BytesIO(content),
        mode="r",
    )


def read_text_entries(
    content: bytes,
) -> dict[str, str]:
    with open_package(content) as archive:
        return {
            filename: archive.read(
                filename
            ).decode("utf-8")
            for filename in archive.namelist()
        }


def test_export_package_contains_expected_files() -> None:
    service = build_export_service()

    package = service.build_package(
        generated_at=FIXED_EXPORT_TIME,
    )

    assert package.filename == (
        "cgms_patent_evidence_package_"
        "20260721_123000Z.zip"
    )

    assert package.media_type == "application/zip"
    assert package.matter_id == "MAT-CGMS-001"
    assert package.file_count == 18
    assert package.includes_sensitive_identifiers is False
    assert package.size_bytes > 0

    assert package.sha256 == hashlib.sha256(
        package.content
    ).hexdigest()

    with open_package(package.content) as archive:
        assert set(archive.namelist()) == (
            EXPECTED_PACKAGE_FILES
        )

        assert archive.testzip() is None


def test_package_manifest_records_governance_metadata() -> None:
    service = build_export_service()

    package = service.build_package(
        generated_at=FIXED_EXPORT_TIME,
    )

    with open_package(package.content) as archive:
        manifest = json.loads(
            archive.read(
                "manifest.json"
            ).decode("utf-8")
        )

    assert manifest["package_type"] == (
        "CGMS Patent Evidence Package"
    )

    assert manifest["schema_version"] == "1.0"
    assert manifest["matter_id"] == "MAT-CGMS-001"

    assert manifest["generated_at"] == (
        "2026-07-21T12:30:00+00:00"
    )

    assert manifest["confidentiality"] == "confidential"

    assert (
        manifest["includes_sensitive_identifiers"]
        is False
    )

    assert manifest["official_status_system"] is False
    assert manifest["legal_advice"] is False

    manifest_paths = {
        record["path"]
        for record in manifest["files"]
    }

    assert manifest_paths == (
        EXPECTED_PACKAGE_FILES
        - {
            "manifest.json",
            "checksums.sha256",
        }
    )


def test_manifest_file_hashes_match_archive_entries() -> None:
    service = build_export_service()

    package = service.build_package(
        generated_at=FIXED_EXPORT_TIME,
    )

    with open_package(package.content) as archive:
        manifest = json.loads(
            archive.read(
                "manifest.json"
            ).decode("utf-8")
        )

        for record in manifest["files"]:
            content = archive.read(
                record["path"]
            )

            assert len(content) == (
                record["size_bytes"]
            )

            assert hashlib.sha256(
                content
            ).hexdigest() == record["sha256"]


def test_checksum_file_matches_exported_entries() -> None:
    service = build_export_service()

    package = service.build_package(
        generated_at=FIXED_EXPORT_TIME,
    )

    with open_package(package.content) as archive:
        checksum_lines = (
            archive.read(
                "checksums.sha256"
            )
            .decode("utf-8")
            .strip()
            .splitlines()
        )

        checksum_records = {}

        for line in checksum_lines:
            digest, filename = line.split(
                "  ",
                maxsplit=1,
            )

            checksum_records[filename] = digest

        assert set(checksum_records) == (
            EXPECTED_PACKAGE_FILES
            - {
                "checksums.sha256",
            }
        )

        for filename, digest in checksum_records.items():
            assert hashlib.sha256(
                archive.read(filename)
            ).hexdigest() == digest


def test_masked_package_contains_no_raw_identifiers() -> None:
    service = build_export_service()

    package = service.build_package(
        include_sensitive=False,
        generated_at=FIXED_EXPORT_TIME,
    )

    entries = read_text_entries(
        package.content
    )

    governed_text = "\n".join(
        content
        for filename, content in entries.items()
        if filename not in {
            "manifest.json",
            "checksums.sha256",
        }
    )

    for identifier in RAW_IDENTIFIERS:
        assert identifier not in governed_text

    assert "••••7873" in governed_text
    assert "••••5429" in governed_text
    assert "••••3697" in governed_text

    manifest = json.loads(
        entries["manifest.json"]
    )

    assert (
        manifest["includes_sensitive_identifiers"]
        is False
    )


def test_sensitive_package_contains_governed_identifiers() -> None:
    service = build_export_service()

    package = service.build_package(
        include_sensitive=True,
        generated_at=FIXED_EXPORT_TIME,
    )

    entries = read_text_entries(
        package.content
    )

    governed_text = "\n".join(
        content
        for filename, content in entries.items()
        if filename not in {
            "manifest.json",
            "checksums.sha256",
        }
    )

    assert "63/987,873" in governed_text
    assert "8158" in governed_text
    assert "225429" in governed_text
    assert "74563697" in governed_text

    manifest = json.loads(
        entries["manifest.json"]
    )

    assert (
        manifest["includes_sensitive_identifiers"]
        is True
    )

    assert (
        package.includes_sensitive_identifiers
        is True
    )


def test_package_readme_preserves_legal_limitations() -> None:
    service = build_export_service()

    package = service.build_package(
        generated_at=FIXED_EXPORT_TIME,
    )

    entries = read_text_entries(
        package.content
    )

    readme = entries["README.md"]

    assert "Classification: Confidential" in readme
    assert "It is not legal advice." in readme

    assert (
        "It is not an official USPTO status system."
        in readme
    )

    assert (
        "does not determine patentability"
        in readme
    )

    assert (
        "does not automatically include the underlying "
        "repository files"
        in readme
    )


def test_repeated_fixed_time_export_is_deterministic() -> None:
    service = build_export_service()

    first_package = service.build_package(
        include_sensitive=False,
        generated_at=FIXED_EXPORT_TIME,
    )

    second_package = service.build_package(
        include_sensitive=False,
        generated_at=FIXED_EXPORT_TIME,
    )

    assert first_package.filename == (
        second_package.filename
    )

    assert first_package.content == (
        second_package.content
    )

    assert first_package.sha256 == (
        second_package.sha256
    )


def test_missing_authentication_is_denied() -> None:
    client = build_isolated_client()

    response = client.get(
        "/patent-readiness/evidence-package"
    )

    assert response.status_code == 401

    assert response.json() == {
        "detail": "Authentication required."
    }


def test_viewer_cannot_export_package() -> None:
    client = build_isolated_client()

    token = create_test_token("viewer")

    response = client.get(
        "/patent-readiness/evidence-package",
        headers=bearer_headers(token),
    )

    assert response.status_code == 403

    assert response.json() == {
        "detail": (
            "Permission denied: "
            "view_patent_governance"
        )
    }


def test_operator_receives_masked_export() -> None:
    client = build_isolated_client()

    token = create_test_token(
        "operator",
        user_id="operator-export-user",
    )

    response = client.get(
        (
            "/patent-readiness/evidence-package"
            "?include_sensitive=true"
        ),
        headers=bearer_headers(
            token,
            **{
                "X-User-Role": "admin",
            },
        ),
    )

    assert response.status_code == 200

    assert response.headers[
        "x-cgms-sensitive-identifiers"
    ] == "masked"

    assert response.headers[
        "x-cgms-matter-id"
    ] == "MAT-CGMS-001"

    entries = read_text_entries(
        response.content
    )

    governed_text = "\n".join(
        content
        for filename, content in entries.items()
        if filename not in {
            "manifest.json",
            "checksums.sha256",
        }
    )

    assert "63/987,873" not in governed_text
    assert "225429" not in governed_text
    assert "74563697" not in governed_text

    assert "••••7873" in governed_text
    assert "••••5429" in governed_text
    assert "••••3697" in governed_text


def test_admin_receives_sensitive_export() -> None:
    client = build_isolated_client()

    token = create_test_token(
        "admin",
        user_id="admin-export-user",
    )

    response = client.get(
        "/patent-readiness/evidence-package",
        headers=bearer_headers(token),
    )

    assert response.status_code == 200

    assert response.headers[
        "x-cgms-sensitive-identifiers"
    ] == "included"

    entries = read_text_entries(
        response.content
    )

    governed_text = "\n".join(
        content
        for filename, content in entries.items()
        if filename not in {
            "manifest.json",
            "checksums.sha256",
        }
    )

    assert "63/987,873" in governed_text
    assert "8158" in governed_text
    assert "225429" in governed_text
    assert "74563697" in governed_text


def test_export_response_contains_integrity_and_security_headers() -> None:
    client = build_isolated_client()

    token = create_test_token("operator")

    response = client.get(
        "/patent-readiness/evidence-package",
        headers=bearer_headers(token),
    )

    assert response.status_code == 200

    assert response.headers[
        "content-type"
    ].startswith("application/zip")

    assert (
        "attachment; filename="
        in response.headers["content-disposition"]
    )

    assert int(
        response.headers["content-length"]
    ) == len(response.content)

    assert response.headers[
        "x-cgms-package-sha256"
    ] == hashlib.sha256(
        response.content
    ).hexdigest()

    assert response.headers["cache-control"] == (
        "no-store, no-cache, must-revalidate, "
        "private, max-age=0"
    )

    assert response.headers["pragma"] == "no-cache"
    assert response.headers["expires"] == "0"

    assert (
        response.headers["x-content-type-options"]
        == "nosniff"
    )

    assert (
        response.headers["x-frame-options"]
        == "DENY"
    )

    assert (
        response.headers["referrer-policy"]
        == "no-referrer"
    )

    content_security_policy = response.headers[
        "content-security-policy"
    ]

    assert "default-src 'none'" in (
        content_security_policy
    )

    assert "frame-ancestors 'none'" in (
        content_security_policy
    )


def test_production_registers_protected_export_route() -> None:
    production_paths = {
        route.path
        for route in production_app.routes
    }

    assert (
        "/patent-readiness/evidence-package"
        in production_paths
    )

    with TestClient(production_app) as client:
        response = client.get(
            "/patent-readiness/evidence-package"
        )

    assert response.status_code == 401

    assert response.json() == {
        "detail": "Authentication required."
    }