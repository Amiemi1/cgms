from __future__ import annotations

from datetime import date
from decimal import Decimal

from app.services.patent_governance.models import (
    AdministrativeMilestone,
    ConfidentialityLevel,
    FilingRecord,
    FilingType,
    MatterType,
    PatentMatter,
    RecordStatus,
    SourceReference,
)
from app.services.patent_governance.registry import (
    PatentGovernanceRegistry,
    get_patent_governance_registry,
)


CGMS_PATENT_MATTER_ID = "MAT-CGMS-001"


CONFIRMED_SOURCE_REFERENCES: tuple[SourceReference, ...] = (
    SourceReference(
        id="SRC-CGMS-PAT-001",
        label="USPTO provisional filing submission record",
        external_reference=(
            "USPTO Patent Center provisional filing record"
        ),
        source_date=date(2026, 2, 21),
        verified=True,
        confidentiality=(
            ConfidentialityLevel.HIGHLY_CONFIDENTIAL
        ),
        notes=(
            "Supports the confirmed provisional filing date, "
            "application number and filing transaction."
        ),
    ),
    SourceReference(
        id="SRC-CGMS-PAT-002",
        label="USPTO Official Filing Receipt",
        external_reference=(
            "Official Filing Receipt issued for the CGMS "
            "provisional patent application"
        ),
        source_date=date(2026, 3, 31),
        verified=True,
        confidentiality=(
            ConfidentialityLevel.HIGHLY_CONFIDENTIAL
        ),
        notes=(
            "Supports the official filing acknowledgement, "
            "confirmation number and related filing identifiers."
        ),
    ),
    SourceReference(
        id="SRC-CGMS-PAT-003",
        label="AIA/122 customer-number association submission",
        external_reference=(
            "USPTO Patent Center AIA/122 submission record"
        ),
        verified=True,
        confidentiality=(
            ConfidentialityLevel.HIGHLY_CONFIDENTIAL
        ),
        notes=(
            "Exact submission date is not assigned until the "
            "underlying evidence is stored in the governed "
            "evidence register."
        ),
    ),
    SourceReference(
        id="SRC-CGMS-PAT-004",
        label="Patent Center Receipt History",
        external_reference=(
            "USPTO Patent Center Receipt History view"
        ),
        verified=True,
        confidentiality=(
            ConfidentialityLevel.HIGHLY_CONFIDENTIAL
        ),
        notes=(
            "Supports confirmation that the later submission "
            "became visible in Receipt History and was assigned "
            "a Patent Center transaction number."
        ),
    ),
)


CONFIRMED_PATENT_MATTERS: tuple[PatentMatter, ...] = (
    PatentMatter(
        id=CGMS_PATENT_MATTER_ID,
        title=(
            "Contextual Group Memory System for "
            "Chat-Based Communication Platforms"
        ),
        matter_type=MatterType.PROVISIONAL_PATENT,
        jurisdiction="US",
        status=RecordStatus.IN_PROGRESS,
        confidentiality=(
            ConfidentialityLevel.HIGHLY_CONFIDENTIAL
        ),
        opened_date=date(2026, 2, 21),
        source_references=[
            "SRC-CGMS-PAT-001",
            "SRC-CGMS-PAT-002",
        ],
        notes=(
            "Primary governed patent matter for the CGMS "
            "provisional filing and subsequent IP development."
        ),
    ),
)


CONFIRMED_FILINGS: tuple[FilingRecord, ...] = (
    FilingRecord(
        id="FIL-CGMS-001",
        matter_id=CGMS_PATENT_MATTER_ID,
        filing_type=FilingType.PROVISIONAL,
        jurisdiction="US",
        application_number="63/987,873",
        filing_date=date(2026, 2, 21),
        confirmation_number="8158",
        customer_number="225429",
        patent_center_number="74563697",
        filing_fee=Decimal("130.00"),
        status=RecordStatus.COMPLETE,
        confidentiality=(
            ConfidentialityLevel.HIGHLY_CONFIDENTIAL
        ),
        source_references=[
            "SRC-CGMS-PAT-001",
            "SRC-CGMS-PAT-002",
            "SRC-CGMS-PAT-004",
        ],
        notes=(
            "Confirmed provisional filing record. The Patent "
            "Center number represents the later transaction "
            "identifier observed in Receipt History."
        ),
    ),
)


CONFIRMED_ADMINISTRATIVE_MILESTONES: tuple[
    AdministrativeMilestone,
    ...
] = (
    AdministrativeMilestone(
        id="MIL-CGMS-001",
        matter_id=CGMS_PATENT_MATTER_ID,
        title="Provisional patent application submitted",
        milestone_type="provisional_filing",
        milestone_date=date(2026, 2, 21),
        status=RecordStatus.COMPLETE,
        responsible_party="Applicant",
        source_references=[
            "SRC-CGMS-PAT-001",
        ],
        notes=(
            "CGMS provisional patent application submitted "
            "through USPTO Patent Center."
        ),
    ),
    AdministrativeMilestone(
        id="MIL-CGMS-002",
        matter_id=CGMS_PATENT_MATTER_ID,
        title="Official Filing Receipt issued",
        milestone_type="official_filing_receipt",
        milestone_date=date(2026, 3, 31),
        status=RecordStatus.VERIFIED,
        responsible_party="USPTO",
        source_references=[
            "SRC-CGMS-PAT-002",
        ],
        notes=(
            "USPTO formally acknowledged the provisional "
            "application and filing particulars."
        ),
    ),
    AdministrativeMilestone(
        id="MIL-CGMS-003",
        matter_id=CGMS_PATENT_MATTER_ID,
        title="AIA/122 customer-number association submitted",
        milestone_type="customer_number_association",
        milestone_date=None,
        status=RecordStatus.COMPLETE,
        responsible_party="Applicant",
        source_references=[
            "SRC-CGMS-PAT-003",
        ],
        next_action=(
            "Confirm that the application is fully associated "
            "with the approved customer number."
        ),
        notes=(
            "The exact submission date will be added when the "
            "submission evidence is registered under PIP-003."
        ),
    ),
    AdministrativeMilestone(
        id="MIL-CGMS-004",
        matter_id=CGMS_PATENT_MATTER_ID,
        title="AIA/122 submission visible in Receipt History",
        milestone_type="receipt_history_confirmation",
        milestone_date=None,
        status=RecordStatus.VERIFIED,
        responsible_party="USPTO Patent Center",
        source_references=[
            "SRC-CGMS-PAT-004",
        ],
        next_action=(
            "Retain the Receipt History evidence and confirm "
            "completion of customer-number association."
        ),
    ),
    AdministrativeMilestone(
        id="MIL-CGMS-005",
        matter_id=CGMS_PATENT_MATTER_ID,
        title=(
            "Application dispatched from pre-examination "
            "and awaiting docketing"
        ),
        milestone_type="pre_examination_processing",
        milestone_date=None,
        status=RecordStatus.IN_PROGRESS,
        responsible_party="USPTO",
        source_references=[
            "SRC-CGMS-PAT-004",
        ],
        next_action=(
            "Monitor Patent Center for further docketing or "
            "administrative-status updates."
        ),
        notes=(
            "Recorded as an administrative status observation, "
            "not as a substantive examination event."
        ),
    ),
)


def bootstrap_confirmed_patent_records(
    registry: PatentGovernanceRegistry | None = None,
) -> dict[str, int]:
    """
    Register the confirmed CGMS patent filing and milestone records.

    Existing records with the same governed IDs are replaced,
    making the operation idempotent while preserving unrelated
    future records in the registry.
    """
    target_registry = (
        registry
        if registry is not None
        else get_patent_governance_registry()
    )

    for source_reference in CONFIRMED_SOURCE_REFERENCES:
        target_registry.register_source_reference(
            source_reference,
            replace=True,
        )

    for matter in CONFIRMED_PATENT_MATTERS:
        target_registry.register_matter(
            matter,
            replace=True,
        )

    for filing in CONFIRMED_FILINGS:
        target_registry.register_filing(
            filing,
            replace=True,
        )

    for milestone in CONFIRMED_ADMINISTRATIVE_MILESTONES:
        target_registry.register_milestone(
            milestone,
            replace=True,
        )

    return {
        "source_references": len(
            CONFIRMED_SOURCE_REFERENCES
        ),
        "matters": len(CONFIRMED_PATENT_MATTERS),
        "filings": len(CONFIRMED_FILINGS),
        "milestones": len(
            CONFIRMED_ADMINISTRATIVE_MILESTONES
        ),
    }