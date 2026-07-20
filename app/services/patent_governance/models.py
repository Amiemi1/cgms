from __future__ import annotations

from datetime import date, datetime, timezone
from decimal import Decimal
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class GovernedModel(BaseModel):
    """
    Base model for Patent and IP Governance records.

    Unknown fields are rejected so that patent records cannot
    silently accumulate uncontrolled or misspelled attributes.
    """

    model_config = ConfigDict(
        extra="forbid",
        validate_assignment=True,
        str_strip_whitespace=True,
    )


class ConfidentialityLevel(str, Enum):
    PUBLIC = "public"
    INTERNAL = "internal"
    CONFIDENTIAL = "confidential"
    HIGHLY_CONFIDENTIAL = "highly_confidential"


class RecordStatus(str, Enum):
    DRAFT = "draft"
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETE = "complete"
    VERIFIED = "verified"
    SUPERSEDED = "superseded"
    ARCHIVED = "archived"


class MatterType(str, Enum):
    PROVISIONAL_PATENT = "provisional_patent"
    NON_PROVISIONAL_PATENT = "non_provisional_patent"
    CONTINUATION = "continuation"
    CONTINUATION_IN_PART = "continuation_in_part"
    INTERNATIONAL_APPLICATION = "international_application"
    OTHER = "other"


class FilingType(str, Enum):
    PROVISIONAL = "provisional"
    NON_PROVISIONAL = "non_provisional"
    CONTINUATION = "continuation"
    CONTINUATION_IN_PART = "continuation_in_part"
    PCT = "pct"
    OTHER = "other"


class FilingRelationship(str, Enum):
    CORE_PROVISIONAL_DISCLOSURE = "core_provisional_disclosure"
    PARTIALLY_DISCLOSED = "partially_disclosed"
    POST_FILING_DEVELOPMENT = "post_filing_development"
    POTENTIAL_FUTURE_FILING = "potential_future_filing"
    COMMERCIALISATION_EVIDENCE = "commercialisation_evidence"
    ADMINISTRATIVE_ONLY = "administrative_only"
    NOT_ASSESSED = "not_assessed"


class EvidenceType(str, Enum):
    FILING_DOCUMENT = "filing_document"
    USPTO_CORRESPONDENCE = "uspto_correspondence"
    ARCHITECTURE_DOCUMENT = "architecture_document"
    SOURCE_CODE = "source_code"
    GIT_COMMIT = "git_commit"
    RELEASE_TAG = "release_tag"
    TEST_REPORT = "test_report"
    DEPLOYMENT_RECORD = "deployment_record"
    DIAGRAM = "diagram"
    PRODUCT_DOCUMENT = "product_document"
    EMAIL = "email"
    SCREENSHOT = "screenshot"
    OTHER = "other"


class InnovationStatus(str, Enum):
    CONCEPT = "concept"
    PLANNED = "planned"
    IN_PROGRESS = "in_progress"
    IMPLEMENTED = "implemented"
    TESTED = "tested"
    DEPLOYED = "deployed"
    SUPERSEDED = "superseded"


class CoveragePosition(str, Enum):
    CORE_DISCLOSED = "core_disclosed"
    PARTIALLY_DISCLOSED = "partially_disclosed"
    NOT_DISCLOSED = "not_disclosed"
    POST_FILING_EXPANSION = "post_filing_expansion"
    UNCERTAIN = "uncertain"
    NOT_ASSESSED = "not_assessed"


class ActionPriority(str, Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class CorrespondenceDirection(str, Enum):
    INBOUND = "inbound"
    OUTBOUND = "outbound"
    INTERNAL = "internal"


class SourceReference(GovernedModel):
    id: str = Field(min_length=1)
    label: str = Field(min_length=1)

    repository_path: str | None = None
    external_reference: str | None = None
    git_commit: str | None = None
    release_tag: str | None = None

    source_date: date | None = None
    verified: bool = False

    confidentiality: ConfidentialityLevel = (
        ConfidentialityLevel.CONFIDENTIAL
    )

    notes: str | None = None


class PatentMatter(GovernedModel):
    id: str = Field(min_length=1)
    title: str = Field(min_length=1)

    matter_type: MatterType
    jurisdiction: str = "US"

    status: RecordStatus = RecordStatus.IN_PROGRESS
    confidentiality: ConfidentialityLevel = (
        ConfidentialityLevel.HIGHLY_CONFIDENTIAL
    )

    inventors: list[str] = Field(default_factory=list)
    owner: str | None = None

    opened_date: date | None = None
    closed_date: date | None = None

    source_references: list[str] = Field(default_factory=list)
    notes: str | None = None

    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)


class FilingRecord(GovernedModel):
    id: str = Field(min_length=1)
    matter_id: str = Field(min_length=1)

    filing_type: FilingType
    jurisdiction: str = "US"

    application_number: str | None = None
    filing_date: date | None = None
    confirmation_number: str | None = None
    customer_number: str | None = None
    patent_center_number: str | None = None

    filing_fee: Decimal | None = Field(
        default=None,
        ge=Decimal("0"),
    )

    status: RecordStatus = RecordStatus.PENDING
    confidentiality: ConfidentialityLevel = (
        ConfidentialityLevel.HIGHLY_CONFIDENTIAL
    )

    source_references: list[str] = Field(default_factory=list)
    notes: str | None = None

    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)


class AdministrativeMilestone(GovernedModel):
    id: str = Field(min_length=1)
    matter_id: str = Field(min_length=1)

    title: str = Field(min_length=1)
    milestone_type: str = Field(min_length=1)
    milestone_date: date | None = None

    status: RecordStatus = RecordStatus.PENDING
    responsible_party: str | None = None

    source_references: list[str] = Field(default_factory=list)
    next_action: str | None = None
    notes: str | None = None

    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)


class PatentDocument(GovernedModel):
    id: str = Field(min_length=1)
    matter_id: str = Field(min_length=1)

    title: str = Field(min_length=1)
    document_type: str = Field(min_length=1)

    document_date: date | None = None
    filed: bool = False
    filed_date: date | None = None
    page_count: int | None = Field(default=None, ge=1)

    confidentiality: ConfidentialityLevel = (
        ConfidentialityLevel.HIGHLY_CONFIDENTIAL
    )

    repository_path: str | None = None
    external_reference: str | None = None

    source_references: list[str] = Field(default_factory=list)
    status: RecordStatus = RecordStatus.DRAFT
    notes: str | None = None

    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)


class EvidenceItem(GovernedModel):
    id: str = Field(min_length=1)
    matter_id: str = Field(min_length=1)

    title: str = Field(min_length=1)
    evidence_type: EvidenceType

    evidence_date: date | None = None
    filing_relationship: FilingRelationship = (
        FilingRelationship.NOT_ASSESSED
    )

    repository_path: str | None = None
    external_reference: str | None = None
    git_commit: str | None = None
    release_tag: str | None = None

    confidentiality: ConfidentialityLevel = (
        ConfidentialityLevel.CONFIDENTIAL
    )

    status: RecordStatus = RecordStatus.PENDING
    verified: bool = False

    source_references: list[str] = Field(default_factory=list)
    notes: str | None = None

    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)


class InnovationRecord(GovernedModel):
    id: str = Field(min_length=1)
    matter_id: str = Field(min_length=1)

    title: str = Field(min_length=1)
    technical_area: str = Field(min_length=1)
    summary: str = Field(min_length=1)

    status: InnovationStatus
    filing_relationship: FilingRelationship = (
        FilingRelationship.NOT_ASSESSED
    )

    first_evidence_date: date | None = None
    implementation_date: date | None = None

    evidence_ids: list[str] = Field(default_factory=list)
    source_references: list[str] = Field(default_factory=list)

    commercial_significance: str | None = None
    novelty_significance: str | None = None
    notes: str | None = None

    confidentiality: ConfidentialityLevel = (
        ConfidentialityLevel.HIGHLY_CONFIDENTIAL
    )

    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)


class CoverageAssessment(GovernedModel):
    id: str = Field(min_length=1)
    matter_id: str = Field(min_length=1)
    innovation_id: str = Field(min_length=1)

    position: CoveragePosition = CoveragePosition.NOT_ASSESSED
    confidence: int = Field(default=0, ge=0, le=100)

    rationale: str | None = None
    review_required: bool = True
    reviewed_by: str | None = None
    reviewed_date: date | None = None

    source_references: list[str] = Field(default_factory=list)
    status: RecordStatus = RecordStatus.DRAFT

    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)


class PatentAction(GovernedModel):
    id: str = Field(min_length=1)
    matter_id: str = Field(min_length=1)

    title: str = Field(min_length=1)
    description: str | None = None

    priority: ActionPriority = ActionPriority.MEDIUM
    status: RecordStatus = RecordStatus.PENDING

    owner: str | None = None
    due_date: date | None = None
    completed_date: date | None = None

    dependency_ids: list[str] = Field(default_factory=list)
    evidence_ids: list[str] = Field(default_factory=list)
    source_references: list[str] = Field(default_factory=list)

    notes: str | None = None

    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)


class CorrespondenceRecord(GovernedModel):
    id: str = Field(min_length=1)
    matter_id: str = Field(min_length=1)

    correspondence_date: date
    direction: CorrespondenceDirection

    sender: str | None = None
    recipient: str | None = None
    subject: str = Field(min_length=1)
    summary: str = Field(min_length=1)

    confidentiality: ConfidentialityLevel = (
        ConfidentialityLevel.HIGHLY_CONFIDENTIAL
    )

    evidence_ids: list[str] = Field(default_factory=list)
    source_references: list[str] = Field(default_factory=list)

    status: RecordStatus = RecordStatus.COMPLETE
    notes: str | None = None

    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)


class DeadlineRecord(GovernedModel):
    id: str = Field(min_length=1)
    matter_id: str = Field(min_length=1)

    title: str = Field(min_length=1)
    deadline_type: str = Field(min_length=1)
    due_date: date

    status: RecordStatus = RecordStatus.PENDING
    action_id: str | None = None
    responsible_party: str | None = None

    source_references: list[str] = Field(default_factory=list)
    notes: str | None = None

    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)


class PatentGovernanceSnapshot(GovernedModel):
    schema_version: str = "1.0"

    generated_at: datetime = Field(default_factory=utc_now)

    matter: PatentMatter
    filings: list[FilingRecord] = Field(default_factory=list)
    milestones: list[AdministrativeMilestone] = Field(
        default_factory=list
    )
    documents: list[PatentDocument] = Field(default_factory=list)
    evidence: list[EvidenceItem] = Field(default_factory=list)
    innovations: list[InnovationRecord] = Field(default_factory=list)
    coverage_assessments: list[CoverageAssessment] = Field(
        default_factory=list
    )
    actions: list[PatentAction] = Field(default_factory=list)
    correspondence: list[CorrespondenceRecord] = Field(
        default_factory=list
    )
    deadlines: list[DeadlineRecord] = Field(default_factory=list)
    source_references: list[SourceReference] = Field(
        default_factory=list
    )