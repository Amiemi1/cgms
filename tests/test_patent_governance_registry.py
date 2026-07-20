from datetime import date

import pytest

from app.services.patent_governance.bootstrap import (
    CGMS_PATENT_MATTER_ID,
    bootstrap_confirmed_patent_records,
)
from app.services.patent_governance.models import (
    AdministrativeMilestone,
    FilingRecord,
    FilingType,
    MatterType,
    PatentMatter,
    RecordStatus,
    SourceReference,
)
from app.services.patent_governance.registry import (
    DuplicatePatentRecordError,
    MissingPatentReferenceError,
    PatentGovernanceRegistry,
)


def build_source(
    source_id: str = "SRC-TEST-001",
) -> SourceReference:
    return SourceReference(
        id=source_id,
        label="Test source reference",
        verified=True,
    )


def build_matter(
    matter_id: str = "MAT-TEST-001",
    source_references: list[str] | None = None,
) -> PatentMatter:
    return PatentMatter(
        id=matter_id,
        title="Test Patent Matter",
        matter_type=MatterType.PROVISIONAL_PATENT,
        source_references=source_references or [],
    )


def test_bootstrap_loads_confirmed_patent_records() -> None:
    registry = PatentGovernanceRegistry()

    result = bootstrap_confirmed_patent_records(
        registry,
    )

    assert result == {
        "source_references": 4,
        "matters": 1,
        "filings": 1,
        "milestones": 5,
    }

    assert len(registry.list_source_references()) == 4
    assert len(registry.list_matters()) == 1
    assert len(registry.list_filings()) == 1
    assert len(registry.list_milestones()) == 5

    matter = registry.get_matter(
        CGMS_PATENT_MATTER_ID,
    )

    filing = registry.get_filing(
        "FIL-CGMS-001",
    )

    assert matter is not None
    assert filing is not None

    assert (
        filing.application_number
        == "63/987,873"
    )

    assert (
        filing.confirmation_number
        == "8158"
    )

    assert (
        filing.customer_number
        == "225429"
    )

    assert (
        filing.patent_center_number
        == "74563697"
    )


def test_bootstrap_is_idempotent() -> None:
    registry = PatentGovernanceRegistry()

    first_result = bootstrap_confirmed_patent_records(
        registry,
    )

    second_result = bootstrap_confirmed_patent_records(
        registry,
    )

    assert first_result == second_result

    assert len(registry.list_source_references()) == 4
    assert len(registry.list_matters()) == 1
    assert len(registry.list_filings()) == 1
    assert len(registry.list_milestones()) == 5


def test_duplicate_records_are_rejected_without_replace() -> None:
    registry = PatentGovernanceRegistry()

    source = build_source()

    registry.register_source_reference(source)

    with pytest.raises(
        DuplicatePatentRecordError,
        match="already exists",
    ):
        registry.register_source_reference(source)


def test_filing_requires_existing_matter() -> None:
    registry = PatentGovernanceRegistry()

    filing = FilingRecord(
        id="FIL-TEST-001",
        matter_id="MAT-MISSING",
        filing_type=FilingType.PROVISIONAL,
    )

    with pytest.raises(
        MissingPatentReferenceError,
        match="does not exist",
    ):
        registry.register_filing(filing)


def test_records_require_valid_source_references() -> None:
    registry = PatentGovernanceRegistry()

    matter = build_matter(
        source_references=[
            "SRC-MISSING",
        ],
    )

    with pytest.raises(
        MissingPatentReferenceError,
        match="Unknown source references",
    ):
        registry.register_matter(matter)


def test_registry_returns_defensive_copies() -> None:
    registry = PatentGovernanceRegistry()

    source = build_source()
    registry.register_source_reference(source)

    matter = build_matter(
        source_references=[source.id],
    )

    registry.register_matter(matter)

    retrieved = registry.get_matter(matter.id)

    assert retrieved is not None

    retrieved.title = "Unauthorized mutation"
    retrieved.source_references.append(
        "SRC-UNREGISTERED",
    )

    authoritative = registry.get_matter(matter.id)

    assert authoritative is not None
    assert authoritative.title == "Test Patent Matter"

    assert authoritative.source_references == [
        source.id,
    ]


def test_filings_and_milestones_are_ordered_by_date() -> None:
    registry = PatentGovernanceRegistry()

    registry.register_matter(
        build_matter(),
    )

    registry.register_filing(
        FilingRecord(
            id="FIL-TEST-002",
            matter_id="MAT-TEST-001",
            filing_type=FilingType.OTHER,
            filing_date=date(2026, 4, 1),
        )
    )

    registry.register_filing(
        FilingRecord(
            id="FIL-TEST-001",
            matter_id="MAT-TEST-001",
            filing_type=FilingType.PROVISIONAL,
            filing_date=date(2026, 2, 21),
        )
    )

    registry.register_milestone(
        AdministrativeMilestone(
            id="MIL-TEST-002",
            matter_id="MAT-TEST-001",
            title="Undated milestone",
            milestone_type="administrative",
            milestone_date=None,
        )
    )

    registry.register_milestone(
        AdministrativeMilestone(
            id="MIL-TEST-001",
            matter_id="MAT-TEST-001",
            title="Dated milestone",
            milestone_type="filing",
            milestone_date=date(2026, 2, 21),
        )
    )

    filings = registry.list_filings(
        matter_id="MAT-TEST-001",
    )

    milestones = registry.list_milestones(
        matter_id="MAT-TEST-001",
    )

    assert [
        filing.id
        for filing in filings
    ] == [
        "FIL-TEST-001",
        "FIL-TEST-002",
    ]

    assert [
        milestone.id
        for milestone in milestones
    ] == [
        "MIL-TEST-001",
        "MIL-TEST-002",
    ]


def test_snapshot_contains_governed_matter_records() -> None:
    registry = PatentGovernanceRegistry()

    bootstrap_confirmed_patent_records(
        registry,
    )

    snapshot = registry.build_snapshot(
        CGMS_PATENT_MATTER_ID,
    )

    assert (
        snapshot.matter.id
        == CGMS_PATENT_MATTER_ID
    )

    assert len(snapshot.filings) == 1
    assert len(snapshot.milestones) == 5
    assert len(snapshot.source_references) == 4

    assert (
        snapshot.filings[0].application_number
        == "63/987,873"
    )

    source_ids = {
        source.id
        for source in snapshot.source_references
    }

    assert source_ids == {
        "SRC-CGMS-PAT-001",
        "SRC-CGMS-PAT-002",
        "SRC-CGMS-PAT-003",
        "SRC-CGMS-PAT-004",
    }


def test_bootstrap_preserves_unrelated_registry_records() -> None:
    registry = PatentGovernanceRegistry()

    unrelated_source = build_source(
        "SRC-OTHER-001",
    )

    registry.register_source_reference(
        unrelated_source,
    )

    unrelated_matter = PatentMatter(
        id="MAT-OTHER-001",
        title="Unrelated Patent Matter",
        matter_type=MatterType.OTHER,
        status=RecordStatus.DRAFT,
        source_references=[
            unrelated_source.id,
        ],
    )

    registry.register_matter(
        unrelated_matter,
    )

    bootstrap_confirmed_patent_records(
        registry,
    )

    assert registry.get_matter(
        "MAT-OTHER-001"
    ) is not None

    assert registry.get_source_reference(
        "SRC-OTHER-001"
    ) is not None

    assert len(registry.list_matters()) == 2
    assert len(registry.list_source_references()) == 5