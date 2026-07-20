from datetime import date
from decimal import Decimal

import pytest
from pydantic import ValidationError

from app.services.patent_governance.models import (
    AdministrativeMilestone,
    ConfidentialityLevel,
    CoverageAssessment,
    CoveragePosition,
    FilingRecord,
    FilingType,
    MatterType,
    PatentGovernanceSnapshot,
    PatentMatter,
    RecordStatus,
)


def build_matter() -> PatentMatter:
    return PatentMatter(
        id="MAT-CGMS-001",
        title=(
            "Contextual Group Memory System for "
            "Chat-Based Communication Platforms"
        ),
        matter_type=MatterType.PROVISIONAL_PATENT,
        jurisdiction="US",
        status=RecordStatus.IN_PROGRESS,
        opened_date=date(2026, 2, 21),
    )


def test_patent_matter_uses_confidential_defaults() -> None:
    matter = build_matter()

    assert matter.id == "MAT-CGMS-001"
    assert matter.jurisdiction == "US"
    assert matter.status == RecordStatus.IN_PROGRESS

    assert (
        matter.confidentiality
        == ConfidentialityLevel.HIGHLY_CONFIDENTIAL
    )

    assert matter.created_at.tzinfo is not None
    assert matter.updated_at.tzinfo is not None


def test_filing_record_preserves_identifiers_and_fee() -> None:
    filing = FilingRecord(
        id="FIL-CGMS-001",
        matter_id="MAT-CGMS-001",
        filing_type=FilingType.PROVISIONAL,
        jurisdiction="US",
        application_number="63/987,873",
        filing_date=date(2026, 2, 21),
        confirmation_number="8158",
        customer_number="225429",
        patent_center_number="74563697",
        filing_fee=Decimal("130.00"),
        status=RecordStatus.COMPLETE,
    )

    assert filing.application_number == "63/987,873"
    assert filing.filing_fee == Decimal("130.00")
    assert filing.status == RecordStatus.COMPLETE

    assert (
        filing.confidentiality
        == ConfidentialityLevel.HIGHLY_CONFIDENTIAL
    )


def test_unknown_fields_are_rejected() -> None:
    with pytest.raises(ValidationError):
        PatentMatter(
            id="MAT-CGMS-001",
            title="CGMS Patent Matter",
            matter_type=MatterType.PROVISIONAL_PATENT,
            unsupported_field="not permitted",
        )


def test_assignment_validation_prevents_invalid_updates() -> None:
    assessment = CoverageAssessment(
        id="COV-CGMS-001",
        matter_id="MAT-CGMS-001",
        innovation_id="INN-CGMS-001",
        position=CoveragePosition.NOT_ASSESSED,
        confidence=0,
    )

    with pytest.raises(ValidationError):
        assessment.confidence = 101


def test_mutable_defaults_are_isolated() -> None:
    first_matter = build_matter()

    second_matter = PatentMatter(
        id="MAT-CGMS-002",
        title="Second Patent Matter",
        matter_type=MatterType.OTHER,
    )

    first_matter.inventors.append("Inventor One")
    first_matter.source_references.append("SRC-001")

    assert second_matter.inventors == []
    assert second_matter.source_references == []


def test_governance_snapshot_serializes_nested_records() -> None:
    matter = build_matter()

    filing = FilingRecord(
        id="FIL-CGMS-001",
        matter_id=matter.id,
        filing_type=FilingType.PROVISIONAL,
        application_number="63/987,873",
        filing_date=date(2026, 2, 21),
        filing_fee=Decimal("130.00"),
        status=RecordStatus.COMPLETE,
    )

    milestone = AdministrativeMilestone(
        id="MIL-CGMS-001",
        matter_id=matter.id,
        title="Provisional application filed",
        milestone_type="filing",
        milestone_date=date(2026, 2, 21),
        status=RecordStatus.COMPLETE,
    )

    snapshot = PatentGovernanceSnapshot(
        matter=matter,
        filings=[filing],
        milestones=[milestone],
    )

    payload = snapshot.model_dump(mode="json")

    assert payload["schema_version"] == "1.0"
    assert payload["matter"]["id"] == "MAT-CGMS-001"

    assert (
        payload["filings"][0]["application_number"]
        == "63/987,873"
    )

    assert (
        payload["milestones"][0]["title"]
        == "Provisional application filed"
    )

    assert isinstance(payload["generated_at"], str)