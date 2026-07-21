from __future__ import annotations

from datetime import date

from app.services.patent_governance.bootstrap import (
    CGMS_PATENT_MATTER_ID,
    bootstrap_confirmed_patent_records,
)
from app.services.patent_governance.evidence_bootstrap import (
    bootstrap_confirmed_patent_evidence,
)
from app.services.patent_governance.evidence_registry import (
    PatentEvidenceRegistry,
    get_patent_evidence_registry,
)
from app.services.patent_governance.innovation_registry import (
    PatentInnovationRegistry,
    get_patent_innovation_registry,
)
from app.services.patent_governance.models import (
    ClaimCandidate,
    ClaimCandidateStatus,
    ClaimCandidateType,
    ConfidentialityLevel,
    CoverageAssessment,
    CoveragePosition,
    FilingRelationship,
    InnovationClaimLink,
    InnovationRecord,
    InnovationStatus,
    LegalReviewStatus,
    RecordStatus,
)
from app.services.patent_governance.registry import (
    PatentGovernanceRegistry,
    get_patent_governance_registry,
)


CONFIRMED_INNOVATIONS: tuple[
    InnovationRecord,
    ...
] = (
    InnovationRecord(
        id="INN-CGMS-001",
        matter_id=CGMS_PATENT_MATTER_ID,
        title="Event-driven memory orchestration",
        technical_area="Runtime orchestration",
        summary=(
            "A runtime arrangement in which governed events "
            "initiate memory-processing and orchestration flows."
        ),
        status=InnovationStatus.IMPLEMENTED,
        filing_relationship=(
            FilingRelationship.POST_FILING_DEVELOPMENT
        ),
        first_evidence_date=date(2026, 6, 11),
        implementation_date=date(2026, 6, 11),
        evidence_ids=[
            "EVD-CGMS-009",
            "EVD-CGMS-015",
        ],
        source_references=[
            "SRC-CGMS-EVD-009",
            "SRC-CGMS-EVD-015",
        ],
        commercial_significance=(
            "Supports extensible runtime automation across "
            "multiple communication and memory workflows."
        ),
        novelty_significance=(
            "Technical differentiation requires comparison "
            "against the prior art and professional review."
        ),
    ),
    InnovationRecord(
        id="INN-CGMS-002",
        matter_id=CGMS_PATENT_MATTER_ID,
        title="Connector-triggered runtime orchestration",
        technical_area="Connector ingestion",
        summary=(
            "Connector events are normalized and admitted into "
            "a governed runtime orchestration process."
        ),
        status=InnovationStatus.IMPLEMENTED,
        filing_relationship=(
            FilingRelationship.POST_FILING_DEVELOPMENT
        ),
        first_evidence_date=date(2026, 6, 13),
        implementation_date=date(2026, 6, 17),
        evidence_ids=[
            "EVD-CGMS-010",
            "EVD-CGMS-013",
            "EVD-CGMS-015",
        ],
        source_references=[
            "SRC-CGMS-EVD-010",
            "SRC-CGMS-EVD-013",
            "SRC-CGMS-EVD-015",
        ],
        commercial_significance=(
            "Enables multiple external systems to participate "
            "in the CGMS operating model."
        ),
    ),
    InnovationRecord(
        id="INN-CGMS-003",
        matter_id=CGMS_PATENT_MATTER_ID,
        title="Workspace-aware memory execution",
        technical_area="Multi-tenant memory runtime",
        summary=(
            "Memory operations execute within a governed "
            "workspace context with tenant-specific controls."
        ),
        status=InnovationStatus.IMPLEMENTED,
        filing_relationship=(
            FilingRelationship.POST_FILING_DEVELOPMENT
        ),
        first_evidence_date=date(2026, 6, 15),
        implementation_date=date(2026, 6, 16),
        evidence_ids=[
            "EVD-CGMS-011",
            "EVD-CGMS-012",
            "EVD-CGMS-014",
        ],
        source_references=[
            "SRC-CGMS-EVD-011",
            "SRC-CGMS-EVD-012",
            "SRC-CGMS-EVD-014",
        ],
        commercial_significance=(
            "Supports enterprise separation, tenant governance "
            "and controlled multi-workspace deployment."
        ),
    ),
    InnovationRecord(
        id="INN-CGMS-004",
        matter_id=CGMS_PATENT_MATTER_ID,
        title="Commercially governed autonomous operation",
        technical_area="Commercial governance",
        summary=(
            "Autonomous runtime behaviour is constrained by "
            "workspace quotas, product plans and commercial "
            "enforcement controls."
        ),
        status=InnovationStatus.IN_PROGRESS,
        filing_relationship=(
            FilingRelationship.POST_FILING_DEVELOPMENT
        ),
        first_evidence_date=date(2026, 6, 16),
        implementation_date=date(2026, 6, 16),
        evidence_ids=[
            "EVD-CGMS-006",
            "EVD-CGMS-007",
            "EVD-CGMS-012",
        ],
        source_references=[
            "SRC-CGMS-EVD-006",
            "SRC-CGMS-EVD-007",
            "SRC-CGMS-EVD-012",
        ],
        commercial_significance=(
            "Connects runtime autonomy to product packaging, "
            "usage controls and enterprise operating policy."
        ),
        notes=(
            "Recorded as in progress because complete product "
            "and commercial hardening remains outstanding."
        ),
    ),
    InnovationRecord(
        id="INN-CGMS-005",
        matter_id=CGMS_PATENT_MATTER_ID,
        title="Policy-based event admission and quarantine",
        technical_area="Runtime governance",
        summary=(
            "Events and subsystems are evaluated against "
            "runtime policy and may be admitted, restricted, "
            "quarantined or released."
        ),
        status=InnovationStatus.IMPLEMENTED,
        filing_relationship=(
            FilingRelationship.POST_FILING_DEVELOPMENT
        ),
        first_evidence_date=date(2026, 7, 6),
        implementation_date=date(2026, 7, 6),
        evidence_ids=[
            "EVD-CGMS-002",
            "EVD-CGMS-015",
        ],
        source_references=[
            "SRC-CGMS-EVD-002",
            "SRC-CGMS-EVD-015",
        ],
        commercial_significance=(
            "Supports controlled autonomy, operational safety "
            "and auditable runtime intervention."
        ),
    ),
    InnovationRecord(
        id="INN-CGMS-006",
        matter_id=CGMS_PATENT_MATTER_ID,
        title="Memory Intelligence Engine",
        technical_area="Memory intelligence",
        summary=(
            "Memory records are assessed and governed using "
            "memory-quality, relevance and operational signals."
        ),
        status=InnovationStatus.DEPLOYED,
        filing_relationship=(
            FilingRelationship.POST_FILING_DEVELOPMENT
        ),
        first_evidence_date=date(2026, 6, 28),
        implementation_date=date(2026, 6, 28),
        evidence_ids=[
            "EVD-CGMS-014",
        ],
        source_references=[
            "SRC-CGMS-EVD-014",
        ],
        commercial_significance=(
            "Improves the reliability and enterprise usability "
            "of persistent contextual memory."
        ),
    ),
    InnovationRecord(
        id="INN-CGMS-007",
        matter_id=CGMS_PATENT_MATTER_ID,
        title="Enterprise Event Bus",
        technical_area="Event infrastructure",
        summary=(
            "A governed event infrastructure provides domain "
            "event registration, dispatch and subscriber-based "
            "runtime integration."
        ),
        status=InnovationStatus.DEPLOYED,
        filing_relationship=(
            FilingRelationship.POST_FILING_DEVELOPMENT
        ),
        first_evidence_date=date(2026, 7, 6),
        implementation_date=date(2026, 7, 6),
        evidence_ids=[
            "EVD-CGMS-015",
        ],
        source_references=[
            "SRC-CGMS-EVD-015",
        ],
        commercial_significance=(
            "Provides a scalable integration foundation for "
            "enterprise CGMS capabilities."
        ),
    ),
    InnovationRecord(
        id="INN-CGMS-008",
        matter_id=CGMS_PATENT_MATTER_ID,
        title="Integrated Product Readiness visibility",
        technical_area="Product governance",
        summary=(
            "Product capabilities are registered, scored and "
            "presented through a readiness dashboard and "
            "machine-enforced continuous-integration gates."
        ),
        status=InnovationStatus.DEPLOYED,
        filing_relationship=(
            FilingRelationship.POST_FILING_DEVELOPMENT
        ),
        first_evidence_date=date(2026, 7, 18),
        implementation_date=date(2026, 7, 20),
        evidence_ids=[
            "EVD-CGMS-016",
            "EVD-CGMS-017",
        ],
        source_references=[
            "SRC-CGMS-EVD-016",
            "SRC-CGMS-EVD-017",
        ],
        commercial_significance=(
            "Creates unified visibility across product "
            "capabilities, readiness gaps and release controls."
        ),
    ),
    InnovationRecord(
        id="INN-CGMS-009",
        matter_id=CGMS_PATENT_MATTER_ID,
        title="Provider-independent defensive architecture",
        technical_area="Defensive architecture",
        summary=(
            "The architecture is positioned to avoid strict "
            "dependence on a single connector, model provider "
            "or runtime implementation."
        ),
        status=InnovationStatus.IN_PROGRESS,
        filing_relationship=(
            FilingRelationship.POTENTIAL_FUTURE_FILING
        ),
        evidence_ids=[
            "EVD-CGMS-001",
            "EVD-CGMS-003",
            "EVD-CGMS-004",
            "EVD-CGMS-005",
        ],
        source_references=[
            "SRC-CGMS-EVD-001",
            "SRC-CGMS-EVD-003",
            "SRC-CGMS-EVD-004",
            "SRC-CGMS-EVD-005",
        ],
        commercial_significance=(
            "Reduces platform concentration risk and supports "
            "technology-provider substitution."
        ),
        notes=(
            "This is a technical defensive-positioning record, "
            "not a conclusion that the subject matter is "
            "independently patentable."
        ),
    ),
)


CONFIRMED_CLAIM_CANDIDATES: tuple[
    ClaimCandidate,
    ...
] = (
    ClaimCandidate(
        id="CLM-CGMS-001",
        matter_id=CGMS_PATENT_MATTER_ID,
        title="Workspace-aware memory execution",
        technical_summary=(
            "A system or method for executing contextual memory "
            "operations within a governed workspace context."
        ),
        candidate_type=ClaimCandidateType.SYSTEM,
        status=ClaimCandidateStatus.EVIDENCE_LINKED,
        filing_relationship=(
            FilingRelationship.POTENTIAL_FUTURE_FILING
        ),
        innovation_ids=[
            "INN-CGMS-003",
            "INN-CGMS-006",
        ],
        evidence_ids=[
            "EVD-CGMS-003",
            "EVD-CGMS-011",
            "EVD-CGMS-012",
            "EVD-CGMS-014",
        ],
        source_references=[
            "SRC-CGMS-EVD-003",
            "SRC-CGMS-EVD-011",
            "SRC-CGMS-EVD-012",
            "SRC-CGMS-EVD-014",
        ],
        legal_review_required=True,
        legal_review_status=LegalReviewStatus.NOT_REVIEWED,
        notes=(
            "Technical working candidate only. The provisional "
            "specification has not been assessed for coverage."
        ),
    ),
    ClaimCandidate(
        id="CLM-CGMS-002",
        matter_id=CGMS_PATENT_MATTER_ID,
        title="Connector-triggered runtime orchestration",
        technical_summary=(
            "A system or method in which normalized connector "
            "events initiate governed runtime orchestration."
        ),
        candidate_type=ClaimCandidateType.METHOD,
        status=ClaimCandidateStatus.EVIDENCE_LINKED,
        filing_relationship=(
            FilingRelationship.POTENTIAL_FUTURE_FILING
        ),
        innovation_ids=[
            "INN-CGMS-001",
            "INN-CGMS-002",
            "INN-CGMS-007",
        ],
        evidence_ids=[
            "EVD-CGMS-003",
            "EVD-CGMS-009",
            "EVD-CGMS-010",
            "EVD-CGMS-013",
            "EVD-CGMS-015",
        ],
        source_references=[
            "SRC-CGMS-EVD-003",
            "SRC-CGMS-EVD-009",
            "SRC-CGMS-EVD-010",
            "SRC-CGMS-EVD-013",
            "SRC-CGMS-EVD-015",
        ],
        legal_review_required=True,
        legal_review_status=LegalReviewStatus.NOT_REVIEWED,
    ),
    ClaimCandidate(
        id="CLM-CGMS-003",
        matter_id=CGMS_PATENT_MATTER_ID,
        title="Commercially governed autonomous operation",
        technical_summary=(
            "A platform in which autonomous runtime behaviour "
            "is constrained by tenant, policy, quota and "
            "commercial product controls."
        ),
        candidate_type=ClaimCandidateType.PLATFORM,
        status=ClaimCandidateStatus.EVIDENCE_LINKED,
        filing_relationship=(
            FilingRelationship.POTENTIAL_FUTURE_FILING
        ),
        innovation_ids=[
            "INN-CGMS-004",
            "INN-CGMS-005",
        ],
        evidence_ids=[
            "EVD-CGMS-002",
            "EVD-CGMS-006",
            "EVD-CGMS-007",
            "EVD-CGMS-012",
            "EVD-CGMS-015",
        ],
        source_references=[
            "SRC-CGMS-EVD-002",
            "SRC-CGMS-EVD-006",
            "SRC-CGMS-EVD-007",
            "SRC-CGMS-EVD-012",
            "SRC-CGMS-EVD-015",
        ],
        legal_review_required=True,
        legal_review_status=LegalReviewStatus.NOT_REVIEWED,
    ),
    ClaimCandidate(
        id="CLM-CGMS-004",
        matter_id=CGMS_PATENT_MATTER_ID,
        title="Policy-based event admission",
        technical_summary=(
            "A system or method for applying runtime policy to "
            "event admission, restriction, quarantine, release "
            "and recovery."
        ),
        candidate_type=ClaimCandidateType.METHOD,
        status=ClaimCandidateStatus.EVIDENCE_LINKED,
        filing_relationship=(
            FilingRelationship.POTENTIAL_FUTURE_FILING
        ),
        innovation_ids=[
            "INN-CGMS-005",
            "INN-CGMS-007",
        ],
        evidence_ids=[
            "EVD-CGMS-002",
            "EVD-CGMS-003",
            "EVD-CGMS-015",
        ],
        source_references=[
            "SRC-CGMS-EVD-002",
            "SRC-CGMS-EVD-003",
            "SRC-CGMS-EVD-015",
        ],
        legal_review_required=True,
        legal_review_status=LegalReviewStatus.NOT_REVIEWED,
    ),
    ClaimCandidate(
        id="CLM-CGMS-005",
        matter_id=CGMS_PATENT_MATTER_ID,
        title="Integrated Product Readiness visibility",
        technical_summary=(
            "A system for registering, scoring, presenting and "
            "continuously enforcing product-capability "
            "readiness conditions."
        ),
        candidate_type=ClaimCandidateType.SYSTEM,
        status=ClaimCandidateStatus.EVIDENCE_LINKED,
        filing_relationship=(
            FilingRelationship.POTENTIAL_FUTURE_FILING
        ),
        innovation_ids=[
            "INN-CGMS-008",
        ],
        evidence_ids=[
            "EVD-CGMS-003",
            "EVD-CGMS-016",
            "EVD-CGMS-017",
        ],
        source_references=[
            "SRC-CGMS-EVD-003",
            "SRC-CGMS-EVD-016",
            "SRC-CGMS-EVD-017",
        ],
        legal_review_required=True,
        legal_review_status=LegalReviewStatus.NOT_REVIEWED,
    ),
    ClaimCandidate(
        id="CLM-CGMS-006",
        matter_id=CGMS_PATENT_MATTER_ID,
        title="Provider-independent defensive architecture",
        technical_summary=(
            "A defensive architectural position that avoids "
            "dependence on a single connector, model or runtime."
        ),
        candidate_type=(
            ClaimCandidateType.DEFENSIVE_POSITIONING
        ),
        status=ClaimCandidateStatus.TECHNICALLY_MAPPED,
        filing_relationship=(
            FilingRelationship.POTENTIAL_FUTURE_FILING
        ),
        innovation_ids=[
            "INN-CGMS-009",
        ],
        evidence_ids=[
            "EVD-CGMS-001",
            "EVD-CGMS-003",
            "EVD-CGMS-004",
            "EVD-CGMS-005",
        ],
        source_references=[
            "SRC-CGMS-EVD-001",
            "SRC-CGMS-EVD-003",
            "SRC-CGMS-EVD-004",
            "SRC-CGMS-EVD-005",
        ],
        legal_review_required=True,
        legal_review_status=LegalReviewStatus.NOT_REVIEWED,
        notes=(
            "Defensive-positioning concept only. It may support "
            "drafting strategy but is not recorded as a filed "
            "or legally reviewed claim."
        ),
    ),
)


def _link(
    *,
    link_id: str,
    innovation_id: str,
    claim_candidate_id: str,
    linkage_strength: int,
    evidence_ids: list[str],
    source_references: list[str],
    rationale: str,
) -> InnovationClaimLink:
    return InnovationClaimLink(
        id=link_id,
        matter_id=CGMS_PATENT_MATTER_ID,
        innovation_id=innovation_id,
        claim_candidate_id=claim_candidate_id,
        linkage_strength=linkage_strength,
        rationale=rationale,
        evidence_ids=evidence_ids,
        source_references=source_references,
        status=RecordStatus.DRAFT,
        review_required=True,
    )


CONFIRMED_INNOVATION_CLAIM_LINKS: tuple[
    InnovationClaimLink,
    ...
] = (
    _link(
        link_id="LNK-CGMS-001",
        innovation_id="INN-CGMS-003",
        claim_candidate_id="CLM-CGMS-001",
        linkage_strength=90,
        evidence_ids=[
            "EVD-CGMS-011",
            "EVD-CGMS-012",
        ],
        source_references=[
            "SRC-CGMS-EVD-011",
            "SRC-CGMS-EVD-012",
        ],
        rationale=(
            "The workspace runtime and tenant-governance "
            "records directly support the technical theme."
        ),
    ),
    _link(
        link_id="LNK-CGMS-002",
        innovation_id="INN-CGMS-006",
        claim_candidate_id="CLM-CGMS-001",
        linkage_strength=70,
        evidence_ids=["EVD-CGMS-014"],
        source_references=["SRC-CGMS-EVD-014"],
        rationale=(
            "Memory Intelligence contributes governed memory "
            "processing within the workspace context."
        ),
    ),
    _link(
        link_id="LNK-CGMS-003",
        innovation_id="INN-CGMS-002",
        claim_candidate_id="CLM-CGMS-002",
        linkage_strength=95,
        evidence_ids=[
            "EVD-CGMS-010",
            "EVD-CGMS-013",
        ],
        source_references=[
            "SRC-CGMS-EVD-010",
            "SRC-CGMS-EVD-013",
        ],
        rationale=(
            "Connector ingestion and adapter evidence directly "
            "supports connector-triggered execution."
        ),
    ),
    _link(
        link_id="LNK-CGMS-004",
        innovation_id="INN-CGMS-007",
        claim_candidate_id="CLM-CGMS-002",
        linkage_strength=80,
        evidence_ids=["EVD-CGMS-015"],
        source_references=["SRC-CGMS-EVD-015"],
        rationale=(
            "The Enterprise Event Bus supplies the governed "
            "dispatch infrastructure for connector events."
        ),
    ),
    _link(
        link_id="LNK-CGMS-005",
        innovation_id="INN-CGMS-004",
        claim_candidate_id="CLM-CGMS-003",
        linkage_strength=90,
        evidence_ids=[
            "EVD-CGMS-006",
            "EVD-CGMS-007",
            "EVD-CGMS-012",
        ],
        source_references=[
            "SRC-CGMS-EVD-006",
            "SRC-CGMS-EVD-007",
            "SRC-CGMS-EVD-012",
        ],
        rationale=(
            "Commercial governance, tenant controls and product "
            "architecture support the technical theme."
        ),
    ),
    _link(
        link_id="LNK-CGMS-006",
        innovation_id="INN-CGMS-005",
        claim_candidate_id="CLM-CGMS-003",
        linkage_strength=75,
        evidence_ids=[
            "EVD-CGMS-002",
            "EVD-CGMS-015",
        ],
        source_references=[
            "SRC-CGMS-EVD-002",
            "SRC-CGMS-EVD-015",
        ],
        rationale=(
            "Policy and quarantine controls constrain runtime "
            "autonomy and provide operational governance."
        ),
    ),
    _link(
        link_id="LNK-CGMS-007",
        innovation_id="INN-CGMS-005",
        claim_candidate_id="CLM-CGMS-004",
        linkage_strength=95,
        evidence_ids=[
            "EVD-CGMS-002",
            "EVD-CGMS-015",
        ],
        source_references=[
            "SRC-CGMS-EVD-002",
            "SRC-CGMS-EVD-015",
        ],
        rationale=(
            "The runtime-governance and event-bus records "
            "directly support policy-based event handling."
        ),
    ),
    _link(
        link_id="LNK-CGMS-008",
        innovation_id="INN-CGMS-007",
        claim_candidate_id="CLM-CGMS-004",
        linkage_strength=80,
        evidence_ids=["EVD-CGMS-015"],
        source_references=["SRC-CGMS-EVD-015"],
        rationale=(
            "The Event Bus provides the event-admission and "
            "dispatch boundary to which policy may be applied."
        ),
    ),
    _link(
        link_id="LNK-CGMS-009",
        innovation_id="INN-CGMS-008",
        claim_candidate_id="CLM-CGMS-005",
        linkage_strength=95,
        evidence_ids=[
            "EVD-CGMS-016",
            "EVD-CGMS-017",
        ],
        source_references=[
            "SRC-CGMS-EVD-016",
            "SRC-CGMS-EVD-017",
        ],
        rationale=(
            "The dashboard and CI gate directly support "
            "integrated readiness visibility and enforcement."
        ),
    ),
    _link(
        link_id="LNK-CGMS-010",
        innovation_id="INN-CGMS-009",
        claim_candidate_id="CLM-CGMS-006",
        linkage_strength=70,
        evidence_ids=[
            "EVD-CGMS-001",
            "EVD-CGMS-003",
            "EVD-CGMS-004",
            "EVD-CGMS-005",
        ],
        source_references=[
            "SRC-CGMS-EVD-001",
            "SRC-CGMS-EVD-003",
            "SRC-CGMS-EVD-004",
            "SRC-CGMS-EVD-005",
        ],
        rationale=(
            "Architecture and expansion notes document the "
            "provider-independence positioning."
        ),
    ),
)


def _coverage_assessment(
    *,
    assessment_id: str,
    innovation_id: str,
    source_references: list[str],
) -> CoverageAssessment:
    return CoverageAssessment(
        id=assessment_id,
        matter_id=CGMS_PATENT_MATTER_ID,
        innovation_id=innovation_id,
        position=CoveragePosition.NOT_ASSESSED,
        confidence=0,
        rationale=(
            "The filed provisional specification is not stored "
            "in the governed repository and has not been "
            "compared against this innovation."
        ),
        review_required=True,
        source_references=source_references,
        status=RecordStatus.DRAFT,
    )


CONFIRMED_COVERAGE_ASSESSMENTS: tuple[
    CoverageAssessment,
    ...
] = (
    _coverage_assessment(
        assessment_id="COV-CGMS-001",
        innovation_id="INN-CGMS-001",
        source_references=[
            "SRC-CGMS-EVD-009",
            "SRC-CGMS-EVD-015",
        ],
    ),
    _coverage_assessment(
        assessment_id="COV-CGMS-002",
        innovation_id="INN-CGMS-002",
        source_references=[
            "SRC-CGMS-EVD-010",
            "SRC-CGMS-EVD-013",
        ],
    ),
    _coverage_assessment(
        assessment_id="COV-CGMS-003",
        innovation_id="INN-CGMS-003",
        source_references=[
            "SRC-CGMS-EVD-011",
            "SRC-CGMS-EVD-012",
        ],
    ),
    _coverage_assessment(
        assessment_id="COV-CGMS-004",
        innovation_id="INN-CGMS-004",
        source_references=[
            "SRC-CGMS-EVD-006",
            "SRC-CGMS-EVD-007",
            "SRC-CGMS-EVD-012",
        ],
    ),
    _coverage_assessment(
        assessment_id="COV-CGMS-005",
        innovation_id="INN-CGMS-005",
        source_references=[
            "SRC-CGMS-EVD-002",
            "SRC-CGMS-EVD-015",
        ],
    ),
    _coverage_assessment(
        assessment_id="COV-CGMS-006",
        innovation_id="INN-CGMS-006",
        source_references=[
            "SRC-CGMS-EVD-014",
        ],
    ),
    _coverage_assessment(
        assessment_id="COV-CGMS-007",
        innovation_id="INN-CGMS-007",
        source_references=[
            "SRC-CGMS-EVD-015",
        ],
    ),
    _coverage_assessment(
        assessment_id="COV-CGMS-008",
        innovation_id="INN-CGMS-008",
        source_references=[
            "SRC-CGMS-EVD-016",
            "SRC-CGMS-EVD-017",
        ],
    ),
    _coverage_assessment(
        assessment_id="COV-CGMS-009",
        innovation_id="INN-CGMS-009",
        source_references=[
            "SRC-CGMS-EVD-001",
            "SRC-CGMS-EVD-003",
        ],
    ),
)


def bootstrap_confirmed_innovation_map(
    governance_registry: PatentGovernanceRegistry | None = None,
    evidence_registry: PatentEvidenceRegistry | None = None,
    innovation_registry: PatentInnovationRegistry | None = None,
) -> dict[str, int]:
    """
    Register the confirmed CGMS technical innovation map.

    The records are technical working materials only and do not
    represent legal advice, filed claims or conclusions regarding
    patentability, validity, scope or enforceability.
    """
    target_governance_registry = (
        governance_registry
        if governance_registry is not None
        else get_patent_governance_registry()
    )

    if (
        target_governance_registry.get_matter(
            CGMS_PATENT_MATTER_ID
        )
        is None
    ):
        bootstrap_confirmed_patent_records(
            target_governance_registry
        )

    if evidence_registry is not None:
        target_evidence_registry = evidence_registry
    elif governance_registry is None:
        target_evidence_registry = (
            get_patent_evidence_registry()
        )
    else:
        target_evidence_registry = PatentEvidenceRegistry(
            target_governance_registry
        )

    if (
        target_evidence_registry.get_evidence(
            "EVD-CGMS-001"
        )
        is None
    ):
        bootstrap_confirmed_patent_evidence(
            target_governance_registry,
            target_evidence_registry,
        )

    if innovation_registry is not None:
        target_innovation_registry = innovation_registry
    elif (
        governance_registry is None
        and evidence_registry is None
    ):
        target_innovation_registry = (
            get_patent_innovation_registry()
        )
    else:
        target_innovation_registry = PatentInnovationRegistry(
            target_governance_registry,
            target_evidence_registry,
        )

    for innovation in CONFIRMED_INNOVATIONS:
        target_innovation_registry.register_innovation(
            innovation,
            replace=True,
        )

    for claim_candidate in CONFIRMED_CLAIM_CANDIDATES:
        target_innovation_registry.register_claim_candidate(
            claim_candidate,
            replace=True,
        )

    for link in CONFIRMED_INNOVATION_CLAIM_LINKS:
        target_innovation_registry.register_link(
            link,
            replace=True,
        )

    for assessment in CONFIRMED_COVERAGE_ASSESSMENTS:
        target_innovation_registry.register_coverage_assessment(
            assessment,
            replace=True,
        )

    return {
        "innovations": len(CONFIRMED_INNOVATIONS),
        "claim_candidates": len(
            CONFIRMED_CLAIM_CANDIDATES
        ),
        "links": len(
            CONFIRMED_INNOVATION_CLAIM_LINKS
        ),
        "coverage_assessments": len(
            CONFIRMED_COVERAGE_ASSESSMENTS
        ),
    }