import pytest

from app.services.patent_governance.bootstrap import (
    CGMS_PATENT_MATTER_ID,
)
from app.services.patent_governance.evidence_bootstrap import (
    bootstrap_confirmed_patent_evidence,
)
from app.services.patent_governance.evidence_registry import (
    PatentEvidenceRegistry,
)
from app.services.patent_governance.innovation_bootstrap import (
    bootstrap_confirmed_innovation_map,
)
from app.services.patent_governance.innovation_registry import (
    PatentInnovationRegistry,
)
from app.services.patent_governance.models import (
    ClaimCandidate,
    ClaimCandidateStatus,
    ClaimCandidateType,
    CoverageAssessment,
    CoveragePosition,
    EvidenceItem,
    EvidenceType,
    FilingRelationship,
    InnovationClaimLink,
    InnovationRecord,
    InnovationStatus,
    LegalReviewStatus,
    MatterType,
    PatentMatter,
)
from app.services.patent_governance.registry import (
    MissingPatentReferenceError,
    PatentGovernanceRegistry,
)


def build_registries() -> tuple[
    PatentGovernanceRegistry,
    PatentEvidenceRegistry,
    PatentInnovationRegistry,
]:
    governance_registry = PatentGovernanceRegistry()

    evidence_registry = PatentEvidenceRegistry(
        governance_registry
    )

    bootstrap_confirmed_patent_evidence(
        governance_registry,
        evidence_registry,
    )

    innovation_registry = PatentInnovationRegistry(
        governance_registry,
        evidence_registry,
    )

    return (
        governance_registry,
        evidence_registry,
        innovation_registry,
    )


def test_bootstrap_loads_confirmed_innovation_map() -> None:
    (
        governance_registry,
        evidence_registry,
        innovation_registry,
    ) = build_registries()

    result = bootstrap_confirmed_innovation_map(
        governance_registry,
        evidence_registry,
        innovation_registry,
    )

    assert result == {
        "innovations": 9,
        "claim_candidates": 6,
        "links": 10,
        "coverage_assessments": 9,
    }

    assert len(
        innovation_registry.list_innovations()
    ) == 9

    assert len(
        innovation_registry.list_claim_candidates()
    ) == 6

    assert len(
        innovation_registry.list_links()
    ) == 10

    assert len(
        innovation_registry.list_coverage_assessments()
    ) == 9


def test_innovation_bootstrap_is_idempotent() -> None:
    (
        governance_registry,
        evidence_registry,
        innovation_registry,
    ) = build_registries()

    first_result = bootstrap_confirmed_innovation_map(
        governance_registry,
        evidence_registry,
        innovation_registry,
    )

    second_result = bootstrap_confirmed_innovation_map(
        governance_registry,
        evidence_registry,
        innovation_registry,
    )

    assert first_result == second_result

    assert len(
        innovation_registry.list_innovations()
    ) == 9

    assert len(
        innovation_registry.list_claim_candidates()
    ) == 6

    assert len(
        innovation_registry.list_links()
    ) == 10

    assert len(
        innovation_registry.list_coverage_assessments()
    ) == 9


def test_innovation_requires_existing_evidence() -> None:
    (
        _,
        _,
        innovation_registry,
    ) = build_registries()

    innovation = InnovationRecord(
        id="INN-TEST-001",
        matter_id=CGMS_PATENT_MATTER_ID,
        title="Invalid Innovation",
        technical_area="Testing",
        summary=(
            "An innovation referencing evidence that "
            "does not exist."
        ),
        status=InnovationStatus.CONCEPT,
        evidence_ids=[
            "EVD-MISSING",
        ],
    )

    with pytest.raises(
        MissingPatentReferenceError,
        match="Unknown evidence items",
    ):
        innovation_registry.register_innovation(
            innovation
        )


def test_claim_candidate_requires_existing_innovation() -> None:
    (
        _,
        _,
        innovation_registry,
    ) = build_registries()

    claim_candidate = ClaimCandidate(
        id="CLM-TEST-001",
        matter_id=CGMS_PATENT_MATTER_ID,
        title="Invalid Claim Candidate",
        technical_summary=(
            "A technical candidate referencing a missing "
            "innovation record."
        ),
        innovation_ids=[
            "INN-MISSING",
        ],
    )

    with pytest.raises(
        MissingPatentReferenceError,
        match="Unknown innovation records",
    ):
        innovation_registry.register_claim_candidate(
            claim_candidate
        )


def test_link_requires_existing_claim_candidate() -> None:
    (
        _,
        _,
        innovation_registry,
    ) = build_registries()

    innovation = InnovationRecord(
        id="INN-TEST-001",
        matter_id=CGMS_PATENT_MATTER_ID,
        title="Test Innovation",
        technical_area="Testing",
        summary="A valid technical innovation record.",
        status=InnovationStatus.CONCEPT,
    )

    innovation_registry.register_innovation(
        innovation
    )

    link = InnovationClaimLink(
        id="LNK-TEST-001",
        matter_id=CGMS_PATENT_MATTER_ID,
        innovation_id=innovation.id,
        claim_candidate_id="CLM-MISSING",
    )

    with pytest.raises(
        MissingPatentReferenceError,
        match="does not exist",
    ):
        innovation_registry.register_link(
            link
        )


def test_coverage_requires_existing_innovation() -> None:
    (
        _,
        _,
        innovation_registry,
    ) = build_registries()

    assessment = CoverageAssessment(
        id="COV-TEST-001",
        matter_id=CGMS_PATENT_MATTER_ID,
        innovation_id="INN-MISSING",
        position=CoveragePosition.NOT_ASSESSED,
        confidence=0,
    )

    with pytest.raises(
        MissingPatentReferenceError,
        match="does not exist",
    ):
        innovation_registry.register_coverage_assessment(
            assessment
        )


def test_registry_returns_defensive_copies() -> None:
    (
        _,
        _,
        innovation_registry,
    ) = build_registries()

    innovation = InnovationRecord(
        id="INN-TEST-001",
        matter_id=CGMS_PATENT_MATTER_ID,
        title="Original Innovation",
        technical_area="Testing",
        summary="Original technical summary.",
        status=InnovationStatus.CONCEPT,
    )

    innovation_registry.register_innovation(
        innovation
    )

    retrieved = innovation_registry.get_innovation(
        innovation.id
    )

    assert retrieved is not None

    retrieved.title = "Unauthorized Change"
    retrieved.evidence_ids.append(
        "EVD-UNREGISTERED"
    )

    authoritative = innovation_registry.get_innovation(
        innovation.id
    )

    assert authoritative is not None
    assert authoritative.title == "Original Innovation"
    assert authoritative.evidence_ids == []


def test_snapshot_reports_innovation_map_metrics() -> None:
    (
        governance_registry,
        evidence_registry,
        innovation_registry,
    ) = build_registries()

    bootstrap_confirmed_innovation_map(
        governance_registry,
        evidence_registry,
        innovation_registry,
    )

    snapshot = innovation_registry.build_snapshot(
        CGMS_PATENT_MATTER_ID
    )

    assert snapshot.total_innovations == 9
    assert snapshot.total_claim_candidates == 6
    assert snapshot.total_links == 10

    assert snapshot.legally_reviewed_candidates == 0
    assert snapshot.review_required_candidates == 6

    assert snapshot.innovation_status_counts == {
        "deployed": 3,
        "implemented": 4,
        "in_progress": 2,
    }

    assert snapshot.claim_status_counts == {
        "evidence_linked": 5,
        "technically_mapped": 1,
    }

    assert snapshot.filing_relationship_counts == {
        "post_filing_development": 8,
        "potential_future_filing": 1,
    }

    assert len(snapshot.coverage_assessments) == 9
    assert len(snapshot.source_references) == 16


def test_claim_candidates_remain_unreviewed_working_records() -> None:
    (
        governance_registry,
        evidence_registry,
        innovation_registry,
    ) = build_registries()

    bootstrap_confirmed_innovation_map(
        governance_registry,
        evidence_registry,
        innovation_registry,
    )

    claim_candidates = (
        innovation_registry.list_claim_candidates(
            matter_id=CGMS_PATENT_MATTER_ID
        )
    )

    assert len(claim_candidates) == 6

    assert all(
        candidate.legal_review_required
        for candidate in claim_candidates
    )

    assert all(
        candidate.legal_review_status
        == LegalReviewStatus.NOT_REVIEWED
        for candidate in claim_candidates
    )

    defensive_candidate = (
        innovation_registry.get_claim_candidate(
            "CLM-CGMS-006"
        )
    )

    assert defensive_candidate is not None

    assert (
        defensive_candidate.candidate_type
        == ClaimCandidateType.DEFENSIVE_POSITIONING
    )

    assert (
        defensive_candidate.status
        == ClaimCandidateStatus.TECHNICALLY_MAPPED
    )


def test_coverage_remains_unassessed_without_specification() -> None:
    (
        governance_registry,
        evidence_registry,
        innovation_registry,
    ) = build_registries()

    bootstrap_confirmed_innovation_map(
        governance_registry,
        evidence_registry,
        innovation_registry,
    )

    assessments = (
        innovation_registry.list_coverage_assessments(
            matter_id=CGMS_PATENT_MATTER_ID
        )
    )

    assert len(assessments) == 9

    assert all(
        assessment.position
        == CoveragePosition.NOT_ASSESSED
        for assessment in assessments
    )

    assert all(
        assessment.confidence == 0
        for assessment in assessments
    )

    assert all(
        assessment.review_required
        for assessment in assessments
    )

    assert all(
        "filed provisional specification" in (
            assessment.rationale or ""
        )
        for assessment in assessments
    )


def test_bootstrap_preserves_unrelated_innovation_records() -> None:
    (
        governance_registry,
        evidence_registry,
        innovation_registry,
    ) = build_registries()

    unrelated_matter = PatentMatter(
        id="MAT-OTHER-001",
        title="Unrelated Patent Matter",
        matter_type=MatterType.OTHER,
    )

    governance_registry.register_matter(
        unrelated_matter
    )

    unrelated_evidence = EvidenceItem(
        id="EVD-OTHER-001",
        matter_id=unrelated_matter.id,
        title="Unrelated Evidence",
        evidence_type=EvidenceType.OTHER,
    )

    evidence_registry.register_evidence(
        unrelated_evidence
    )

    unrelated_innovation = InnovationRecord(
        id="INN-OTHER-001",
        matter_id=unrelated_matter.id,
        title="Unrelated Innovation",
        technical_area="Other",
        summary="An unrelated technical innovation.",
        status=InnovationStatus.CONCEPT,
        filing_relationship=FilingRelationship.NOT_ASSESSED,
        evidence_ids=[
            unrelated_evidence.id,
        ],
    )

    innovation_registry.register_innovation(
        unrelated_innovation
    )

    bootstrap_confirmed_innovation_map(
        governance_registry,
        evidence_registry,
        innovation_registry,
    )

    assert innovation_registry.get_innovation(
        unrelated_innovation.id
    ) is not None

    assert len(
        innovation_registry.list_innovations()
    ) == 10