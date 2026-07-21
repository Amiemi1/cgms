from __future__ import annotations

import csv
import hashlib
import io
import json
import zipfile
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from threading import RLock

from app.services.patent_governance.bootstrap import (
    CGMS_PATENT_MATTER_ID,
    bootstrap_confirmed_patent_records,
)
from app.services.patent_governance.dashboard_service import (
    PatentDashboardService,
)
from app.services.patent_governance.evidence_bootstrap import (
    bootstrap_confirmed_patent_evidence,
)
from app.services.patent_governance.evidence_registry import (
    PatentEvidenceRegistry,
    get_patent_evidence_registry,
)
from app.services.patent_governance.innovation_bootstrap import (
    bootstrap_confirmed_innovation_map,
)
from app.services.patent_governance.innovation_registry import (
    PatentInnovationRegistry,
    get_patent_innovation_registry,
)
from app.services.patent_governance.registry import (
    PatentGovernanceRegistry,
    get_patent_governance_registry,
)


ZIP_MEDIA_TYPE = "application/zip"

_SENSITIVE_FIELD_NAMES = frozenset(
    {
        "application_number",
        "confirmation_number",
        "customer_number",
        "patent_center_number",
        "patent_center_transaction_number",
        "transaction_number",
    }
)


@dataclass(
    frozen=True,
    slots=True,
)
class PatentEvidencePackage:
    filename: str
    media_type: str
    content: bytes
    sha256: str
    generated_at: datetime
    matter_id: str
    includes_sensitive_identifiers: bool
    file_count: int

    @property
    def size_bytes(self) -> int:
        return len(self.content)


def _model_to_json_safe(
    value: Any,
) -> Any:
    if hasattr(value, "model_dump"):
        return value.model_dump(
            mode="json"
        )

    if hasattr(value, "dict"):
        return value.dict()

    if isinstance(value, dict):
        return {
            str(key): _model_to_json_safe(item)
            for key, item in value.items()
        }

    if isinstance(value, (list, tuple, set, frozenset)):
        return [
            _model_to_json_safe(item)
            for item in value
        ]

    return value


def _mask_identifier(
    value: Any,
) -> str:
    if value is None:
        return "Not recorded"

    text = str(value).strip()

    if not text:
        return "Not recorded"

    normalized = "".join(
        character
        for character in text
        if character.isalnum()
    )

    if len(normalized) <= 4:
        return "••••"

    return f"••••{normalized[-4:]}"


def _sanitize_payload(
    value: Any,
    *,
    include_sensitive: bool,
    sensitive_replacements: (
        dict[str, str] | None
    ) = None,
) -> Any:
    replacements = (
        sensitive_replacements
        if sensitive_replacements is not None
        else {}
    )

    if isinstance(value, dict):
        sanitized: dict[str, Any] = {}

        for key, item in value.items():
            normalized_key = str(key)

            if (
                normalized_key
                in _SENSITIVE_FIELD_NAMES
                and not include_sensitive
            ):
                sanitized[normalized_key] = (
                    _mask_identifier(item)
                )
            else:
                sanitized[normalized_key] = (
                    _sanitize_payload(
                        item,
                        include_sensitive=(
                            include_sensitive
                        ),
                        sensitive_replacements=(
                            replacements
                        ),
                    )
                )

        return sanitized

    if isinstance(value, list):
        return [
            _sanitize_payload(
                item,
                include_sensitive=include_sensitive,
                sensitive_replacements=replacements,
            )
            for item in value
        ]

    if (
        isinstance(value, str)
        and not include_sensitive
    ):
        sanitized_text = value

        for raw_value in sorted(
            replacements,
            key=len,
            reverse=True,
        ):
            sanitized_text = sanitized_text.replace(
                raw_value,
                replacements[raw_value],
            )

        return sanitized_text

    return value


def _json_bytes(
    payload: Any,
) -> bytes:
    return (
        json.dumps(
            payload,
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        )
        + "\n"
    ).encode("utf-8")


def _csv_value(
    value: Any,
) -> str:
    if value is None:
        return ""

    if isinstance(value, (dict, list)):
        return json.dumps(
            value,
            ensure_ascii=False,
            sort_keys=True,
        )

    if isinstance(value, bool):
        return "true" if value else "false"

    return str(value)


def _csv_bytes(
    records: list[dict[str, Any]],
) -> bytes:
    if not records:
        return b""

    fieldnames = sorted(
        {
            key
            for record in records
            for key in record
        }
    )

    stream = io.StringIO(
        newline=""
    )

    writer = csv.DictWriter(
        stream,
        fieldnames=fieldnames,
        extrasaction="ignore",
    )

    writer.writeheader()

    for record in records:
        writer.writerow(
            {
                key: _csv_value(
                    record.get(key)
                )
                for key in fieldnames
            }
        )

    return stream.getvalue().encode(
        "utf-8"
    )


def _sha256(
    content: bytes,
) -> str:
    return hashlib.sha256(
        content
    ).hexdigest()


def _archive_name(
    generated_at: datetime,
) -> str:
    timestamp = generated_at.strftime(
        "%Y%m%d_%H%M%SZ"
    )

    return (
        "cgms_patent_evidence_package_"
        f"{timestamp}.zip"
    )


def _write_zip_entry(
    archive: zipfile.ZipFile,
    *,
    filename: str,
    content: bytes,
) -> None:
    information = zipfile.ZipInfo(
        filename=filename,
        date_time=(
            1980,
            1,
            1,
            0,
            0,
            0,
        ),
    )

    information.compress_type = (
        zipfile.ZIP_DEFLATED
    )

    information.external_attr = (
        0o600 << 16
    )

    archive.writestr(
        information,
        content,
    )


class PatentEvidenceExportService:
    """
    Creates a governed ZIP evidence package in memory.

    The package contains registry records, structured summaries,
    operational notices and integrity checksums. It does not
    determine patentability, validity, enforceability or claim
    scope and is not an official USPTO record.
    """

    def __init__(
        self,
        governance_registry: (
            PatentGovernanceRegistry | None
        ) = None,
        evidence_registry: (
            PatentEvidenceRegistry | None
        ) = None,
        innovation_registry: (
            PatentInnovationRegistry | None
        ) = None,
    ) -> None:
        self._governance_registry = (
            governance_registry
            if governance_registry is not None
            else get_patent_governance_registry()
        )

        self._evidence_registry = (
            evidence_registry
            if evidence_registry is not None
            else get_patent_evidence_registry()
        )

        self._innovation_registry = (
            innovation_registry
            if innovation_registry is not None
            else get_patent_innovation_registry()
        )

        self._dashboard_service = (
            PatentDashboardService(
                governance_registry=(
                    self._governance_registry
                ),
                evidence_registry=(
                    self._evidence_registry
                ),
                innovation_registry=(
                    self._innovation_registry
                ),
            )
        )

        self._bootstrap_lock = RLock()
        self._bootstrapped = False

    def ensure_bootstrapped(self) -> None:
        """
        Bootstrap the governed export state once per service
        instance.

        Rebuilding bootstrap records on every export can change
        volatile model metadata and prevent deterministic package
        generation even when the requested export time and
        governed business records are unchanged.
        """
        if self._bootstrapped:
            return

        with self._bootstrap_lock:
            if self._bootstrapped:
                return

            bootstrap_confirmed_patent_records(
                self._governance_registry
            )

            bootstrap_confirmed_patent_evidence(
                self._governance_registry,
                self._evidence_registry,
            )

            bootstrap_confirmed_innovation_map(
                self._governance_registry,
                self._evidence_registry,
                self._innovation_registry,
            )

            self._bootstrapped = True

    def build_package(
        self,
        *,
        matter_id: str = CGMS_PATENT_MATTER_ID,
        include_sensitive: bool = False,
        generated_at: datetime | None = None,
    ) -> PatentEvidencePackage:
        self.ensure_bootstrapped()

        export_time = (
            generated_at
            if generated_at is not None
            else datetime.now(timezone.utc)
        )

        if export_time.tzinfo is None:
            export_time = export_time.replace(
                tzinfo=timezone.utc
            )
        else:
            export_time = export_time.astimezone(
                timezone.utc
            )

        governance_snapshot = (
            self._governance_registry
            .build_snapshot(matter_id)
        )

        evidence_snapshot = (
            self._evidence_registry
            .build_snapshot(matter_id)
        )

        innovation_snapshot = (
            self._innovation_registry
            .build_snapshot(matter_id)
        )

        dashboard_view = (
            self._dashboard_service.build_view(
                matter_id=matter_id,
                include_sensitive=include_sensitive,
                production_access_enabled=False,
                bootstrap_records=False,
            )
        )

        raw_governance_payload = _model_to_json_safe(
            governance_snapshot
        )

        raw_evidence_payload = _model_to_json_safe(
            evidence_snapshot
        )

        raw_innovation_payload = _model_to_json_safe(
            innovation_snapshot
        )

        raw_dashboard_payload = _model_to_json_safe(
            dashboard_view
        )

        snapshot_generated_at = (
            export_time.isoformat()
            .replace(
                "+00:00",
                "Z",
            )
        )

        for snapshot_payload in (
            raw_governance_payload,
            raw_evidence_payload,
            raw_innovation_payload,
        ):
            if isinstance(
                snapshot_payload,
                dict,
            ):
                snapshot_payload[
                    "generated_at"
                ] = snapshot_generated_at

        sensitive_replacements = (
            _collect_sensitive_replacements(
                {
                    "governance": raw_governance_payload,
                    "evidence": raw_evidence_payload,
                    "innovation": raw_innovation_payload,
                    "dashboard": raw_dashboard_payload,
                }
            )
        )

        governance_payload = _sanitize_payload(
            raw_governance_payload,
            include_sensitive=include_sensitive,
            sensitive_replacements=(
                sensitive_replacements
            ),
        )

        evidence_payload = _sanitize_payload(
            raw_evidence_payload,
            include_sensitive=include_sensitive,
            sensitive_replacements=(
                sensitive_replacements
            ),
        )

        innovation_payload = _sanitize_payload(
            raw_innovation_payload,
            include_sensitive=include_sensitive,
            sensitive_replacements=(
                sensitive_replacements
            ),
        )

        dashboard_payload = _sanitize_payload(
            raw_dashboard_payload,
            include_sensitive=include_sensitive,
            sensitive_replacements=(
                sensitive_replacements
            ),
        )

        entries: dict[str, bytes] = {
            "README.md": self._build_readme(
                matter_id=matter_id,
                generated_at=export_time,
                include_sensitive=include_sensitive,
            ),
            (
                "governance/"
                "governance_snapshot.json"
            ): _json_bytes(
                governance_payload
            ),
            (
                "governance/"
                "dashboard_summary.json"
            ): _json_bytes(
                dashboard_payload
            ),
            (
                "evidence/"
                "evidence_snapshot.json"
            ): _json_bytes(
                evidence_payload
            ),
            (
                "innovation/"
                "innovation_snapshot.json"
            ): _json_bytes(
                innovation_payload
            ),
            (
                "governance/"
                "governance_notices.md"
            ): self._build_governance_notices(
                dashboard_payload
            ),
        }

        entries.update(
            self._build_csv_entries(
                governance_payload=(
                    governance_payload
                ),
                evidence_payload=(
                    evidence_payload
                ),
                innovation_payload=(
                    innovation_payload
                ),
            )
        )

        content_hashes = {
            filename: _sha256(content)
            for filename, content
            in sorted(entries.items())
        }

        manifest = {
            "package_type": (
                "CGMS Patent Evidence Package"
            ),
            "schema_version": "1.0",
            "matter_id": matter_id,
            "generated_at": (
                export_time.isoformat()
            ),
            "confidentiality": (
                "confidential"
            ),
            "includes_sensitive_identifiers": (
                include_sensitive
            ),
            "official_status_system": False,
            "legal_advice": False,
            "file_count_excluding_manifest": (
                len(entries)
            ),
            "files": [
                {
                    "path": filename,
                    "sha256": content_hashes[
                        filename
                    ],
                    "size_bytes": len(
                        entries[filename]
                    ),
                }
                for filename
                in sorted(entries)
            ],
        }

        entries["manifest.json"] = _json_bytes(
            manifest
        )

        checksums = "\n".join(
            (
                f"{_sha256(entries[filename])}  "
                f"{filename}"
            )
            for filename in sorted(entries)
        )

        entries["checksums.sha256"] = (
            checksums + "\n"
        ).encode("utf-8")

        package_stream = io.BytesIO()

        with zipfile.ZipFile(
            package_stream,
            mode="w",
            compression=zipfile.ZIP_DEFLATED,
        ) as archive:
            for filename in sorted(entries):
                _write_zip_entry(
                    archive,
                    filename=filename,
                    content=entries[filename],
                )

        package_content = (
            package_stream.getvalue()
        )

        return PatentEvidencePackage(
            filename=_archive_name(
                export_time
            ),
            media_type=ZIP_MEDIA_TYPE,
            content=package_content,
            sha256=_sha256(
                package_content
            ),
            generated_at=export_time,
            matter_id=matter_id,
            includes_sensitive_identifiers=(
                include_sensitive
            ),
            file_count=len(entries),
        )

    def _build_csv_entries(
        self,
        *,
        governance_payload: dict[str, Any],
        evidence_payload: dict[str, Any],
        innovation_payload: dict[str, Any],
    ) -> dict[str, bytes]:
        mappings = {
            "governance/filings.csv": (
                governance_payload.get(
                    "filings",
                    [],
                )
            ),
            "governance/milestones.csv": (
                governance_payload.get(
                    "milestones",
                    [],
                )
            ),
            "evidence/documents.csv": (
                evidence_payload.get(
                    "documents",
                    [],
                )
            ),
            "evidence/evidence_items.csv": (
                evidence_payload.get(
                    "evidence",
                    [],
                )
            ),
            "evidence/verifications.csv": (
                evidence_payload.get(
                    "verifications",
                    [],
                )
            ),
            "evidence/collections.csv": (
                evidence_payload.get(
                    "collections",
                    [],
                )
            ),
            "innovation/innovations.csv": (
                innovation_payload.get(
                    "innovations",
                    [],
                )
            ),
            (
                "innovation/"
                "claim_candidates.csv"
            ): innovation_payload.get(
                "claim_candidates",
                [],
            ),
            (
                "innovation/"
                "innovation_claim_links.csv"
            ): innovation_payload.get(
                "links",
                [],
            ),
            (
                "innovation/"
                "coverage_assessments.csv"
            ): innovation_payload.get(
                "coverage_assessments",
                [],
            ),
        }

        csv_entries: dict[str, bytes] = {}

        for filename, records in mappings.items():
            normalized_records = (
                records
                if isinstance(records, list)
                else []
            )

            csv_entries[filename] = (
                _csv_bytes(
                    [
                        record
                        for record
                        in normalized_records
                        if isinstance(
                            record,
                            dict,
                        )
                    ]
                )
            )

        return csv_entries

    def _build_readme(
        self,
        *,
        matter_id: str,
        generated_at: datetime,
        include_sensitive: bool,
    ) -> bytes:
        disclosure = (
            "Complete governed filing identifiers "
            "are included."
            if include_sensitive
            else (
                "Governed filing identifiers are "
                "masked."
            )
        )

        text = f"""# CGMS Patent Evidence Package

Matter: {matter_id}

Generated: {generated_at.isoformat()}

Classification: Confidential

Identifier treatment: {disclosure}

## Purpose

This package consolidates governed administrative,
technical-evidence and innovation records maintained by CGMS.

## Contents

- governance records and administrative milestones;
- evidence records, documents and verification status;
- innovation and technical claim-candidate records;
- filing-coverage assessment records;
- operational dashboard summary;
- machine-readable JSON;
- tabular CSV exports;
- SHA-256 integrity checksums.

## Important limitations

This package is an internal operational record.

It is not legal advice.

It is not an official USPTO status system.

It does not determine patentability, novelty, validity,
enforceability, ownership or claim scope.

Technical claim candidates must be reviewed by qualified
patent counsel before being treated as legal claims.

The package contains metadata and governed summaries.

It does not automatically include the underlying repository files,
source code, filed specification or external correspondence.
"""

        return text.encode("utf-8")

    def _build_governance_notices(
        self,
        dashboard_payload: dict[str, Any],
    ) -> bytes:
        governance = dashboard_payload.get(
            "governance",
            {},
        )

        text = f"""# Governance Notices

## Legal status

{governance.get("legal_disclaimer", "Not recorded")}

## Confidentiality

{governance.get("confidentiality_notice", "Not recorded")}

## Filing coverage

{governance.get("coverage_notice", "Not recorded")}
"""

        return text.encode("utf-8")


def build_patent_evidence_package(
    *,
    include_sensitive: bool = False,
) -> PatentEvidencePackage:
    return PatentEvidenceExportService().build_package(
        include_sensitive=include_sensitive
    )

def _collect_sensitive_replacements(
    value: Any,
) -> dict[str, str]:
    """
    Build a replacement map from governed identifier fields.

    This prevents an identifier from leaking when it has also
    been copied into a note, description or other text field.
    """
    replacements: dict[str, str] = {}

    def collect(item: Any) -> None:
        if isinstance(item, dict):
            for key, child in item.items():
                normalized_key = str(key)

                if (
                    normalized_key
                    in _SENSITIVE_FIELD_NAMES
                    and child is not None
                ):
                    raw_value = str(child).strip()

                    if raw_value:
                        masked_value = _mask_identifier(
                            raw_value
                        )

                        replacements[
                            raw_value
                        ] = masked_value

                        normalized_value = "".join(
                            character
                            for character in raw_value
                            if character.isalnum()
                        )

                        if normalized_value:
                            replacements[
                                normalized_value
                            ] = masked_value

                collect(child)

        elif isinstance(item, list):
            for child in item:
                collect(child)

    collect(value)

    return replacements