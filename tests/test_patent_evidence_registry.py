from datetime import date

import pytest

from app.services.patent_governance.bootstrap import (
    CGMS_PATENT_MATTER_ID,
    bootstrap_confirmed_patent_records,
)
from app.services.patent_governance.evidence_bootstrap import (
    bootstrap_confirmed_patent_evidence,
)
from app.services.patent_governance.evidence_registry import (
    PatentEvidenceRegistry,
)
from app.services.patent_governance.models import (
    EvidenceCollection,
    EvidenceItem,
    EvidenceType,
    EvidenceVerification,
    FilingRelationship,
    MatterType,
    PatentDocument,
    PatentMatter,
    RecordStatus,
    SourceReference,
    VerificationStatus,
)
from app.services.patent_governance.registry import (
    MissingPatentReferenceError,
    PatentGovernanceRegistry,
)


def build_governance_registry() -> PatentGovernanceRegistry:
    registry = PatentGovernanceRegistry()

    bootstrap_confirmed_patent_records(
        registry,
    )

    return registry


def test_bootstrap_loads_confirmed_evidence_catalogue() -> None:
    governance_registry = PatentGovernanceRegistry()

    evidence_registry = PatentEvidenceRegistry(
        governance_registry
    )

    result = bootstrap_confirmed_patent_evidence(
        governance_registry,
        evidence_registry,
    )

    assert result == {
        "source_references": 17,
        "documents": 3,
        "evidence_items": 17,
        "verifications": 17,
        "collections": 4,
    }

    assert len(evidence_registry.list_documents()) == 3
    assert len(evidence_registry.list_evidence()) == 17

    assert (
        len(evidence_registry.list_verifications())
        == 17
    )

    assert len(evidence_registry.list_collections()) == 4


def test_evidence_bootstrap_is_idempotent() -> None:
    governance_registry = PatentGovernanceRegistry()

    evidence_registry = PatentEvidenceRegistry(
        governance_registry
    )

    first_result = bootstrap_confirmed_patent_evidence(
        governance_registry,
        evidence_registry,
    )

    second_result = bootstrap_confirmed_patent_evidence(
        governance_registry,
        evidence_registry,
    )

    assert first_result == second_result

    assert len(evidence_registry.list_documents()) == 3
    assert len(evidence_registry.list_evidence()) == 17

    assert (
        len(evidence_registry.list_verifications())
        == 17
    )

    assert len(evidence_registry.list_collections()) == 4


def test_document_requires_existing_patent_matter() -> None:
    governance_registry = PatentGovernanceRegistry()

    evidence_registry = PatentEvidenceRegistry(
        governance_registry
    )

    document = PatentDocument(
        id="DOC-TEST-001",
        matter_id="MAT-MISSING",
        title="Missing Matter Document",
        document_type="test_document",
    )

    with pytest.raises(
        MissingPatentReferenceError,
        match="does not exist",
    ):
        evidence_registry.register_document(
            document
        )


def test_evidence_requires_valid_source_references() -> None:
    governance_registry = build_governance_registry()

    evidence_registry = PatentEvidenceRegistry(
        governance_registry
    )

    evidence = EvidenceItem(
        id="EVD-TEST-001",
        matter_id=CGMS_PATENT_MATTER_ID,
        title="Evidence with missing source",
        evidence_type=EvidenceType.OTHER,
        source_references=[
            "SRC-MISSING",
        ],
    )

    with pytest.raises(
        MissingPatentReferenceError,
        match="Unknown source references",
    ):
        evidence_registry.register_evidence(
            evidence
        )


def test_verification_requires_existing_evidence() -> None:
    governance_registry = build_governance_registry()

    evidence_registry = PatentEvidenceRegistry(
        governance_registry
    )

    verification = EvidenceVerification(
        id="VER-TEST-001",
        matter_id=CGMS_PATENT_MATTER_ID,
        evidence_id="EVD-MISSING",
        status=VerificationStatus.UNVERIFIED,
    )

    with pytest.raises(
        MissingPatentReferenceError,
        match="does not exist",
    ):
        evidence_registry.register_verification(
            verification
        )


def test_collection_requires_existing_records() -> None:
    governance_registry = build_governance_registry()

    evidence_registry = PatentEvidenceRegistry(
        governance_registry
    )

    collection = EvidenceCollection(
        id="COL-TEST-001",
        matter_id=CGMS_PATENT_MATTER_ID,
        title="Invalid Evidence Collection",
        evidence_ids=[
            "EVD-MISSING",
        ],
    )

    with pytest.raises(
        MissingPatentReferenceError,
        match="does not exist",
    ):
        evidence_registry.register_collection(
            collection
        )


def test_registry_returns_defensive_copies() -> None:
    governance_registry = build_governance_registry()

    evidence_registry = PatentEvidenceRegistry(
        governance_registry
    )

    evidence = EvidenceItem(
        id="EVD-TEST-001",
        matter_id=CGMS_PATENT_MATTER_ID,
        title="Original Evidence Title",
        evidence_type=EvidenceType.OTHER,
        status=RecordStatus.COMPLETE,
    )

    evidence_registry.register_evidence(
        evidence
    )

    retrieved = evidence_registry.get_evidence(
        evidence.id
    )

    assert retrieved is not None

    retrieved.title = "Unauthorized Change"
    retrieved.source_references.append(
        "SRC-UNREGISTERED"
    )

    authoritative = evidence_registry.get_evidence(
        evidence.id
    )

    assert authoritative is not None

    assert (
        authoritative.title
        == "Original Evidence Title"
    )

    assert authoritative.source_references == []


def test_snapshot_reports_evidence_metrics() -> None:
    governance_registry = PatentGovernanceRegistry()

    evidence_registry = PatentEvidenceRegistry(
        governance_registry
    )

    bootstrap_confirmed_patent_evidence(
        governance_registry,
        evidence_registry,
    )

    snapshot = evidence_registry.build_snapshot(
        CGMS_PATENT_MATTER_ID
    )

    assert snapshot.total_documents == 3
    assert snapshot.total_evidence_items == 17
    assert snapshot.verified_evidence_items == 4

    assert snapshot.filing_relationship_counts == {
        "not_assessed": 7,
        "post_filing_development": 9,
        "potential_future_filing": 1,
    }

    assert snapshot.evidence_type_counts == {
        "architecture_document": 4,
        "git_commit": 7,
        "product_document": 3,
        "release_tag": 2,
        "test_report": 1,
    }

    assert len(snapshot.source_references) == 17
    assert len(snapshot.collections) == 4
    assert len(snapshot.verifications) == 17


def test_positioning_documents_are_not_recorded_as_filed() -> None:
    governance_registry = PatentGovernanceRegistry()

    evidence_registry = PatentEvidenceRegistry(
        governance_registry
    )

    bootstrap_confirmed_patent_evidence(
        governance_registry,
        evidence_registry,
    )

    documents = evidence_registry.list_documents(
        matter_id=CGMS_PATENT_MATTER_ID
    )

    assert all(
        document.filed is False
        for document in documents
    )

    expansion_evidence = evidence_registry.get_evidence(
        "EVD-CGMS-003"
    )

    assert expansion_evidence is not None

    assert (
        expansion_evidence.filing_relationship
        == FilingRelationship.POTENTIAL_FUTURE_FILING
    )


def test_regression_limitations_and_untracked_outputs_are_preserved() -> None:
    governance_registry = PatentGovernanceRegistry()

    evidence_registry = PatentEvidenceRegistry(
        governance_registry
    )

    bootstrap_confirmed_patent_evidence(
        governance_registry,
        evidence_registry,
    )

    regression_evidence = evidence_registry.get_evidence(
        "EVD-CGMS-008"
    )

    regression_verification = (
        evidence_registry.get_verification(
            "VER-CGMS-008"
        )
    )

    assert regression_evidence is not None
    assert regression_verification is not None

    assert "seven runtime warnings" in (
        regression_evidence.notes or ""
    )

    assert "seven runtime warnings" in (
        regression_verification.limitations or ""
    )

    repository_paths = {
        item.repository_path
        for item in evidence_registry.list_evidence()
        if item.repository_path is not None
    }

    assert not any(
        path.startswith(
            "artifacts/product-readiness/"
        )
        for path in repository_paths
    )


def test_bootstrap_preserves_unrelated_evidence_records() -> None:
    governance_registry = PatentGovernanceRegistry()

    unrelated_source = SourceReference(
        id="SRC-OTHER-001",
        label="Unrelated evidence source",
        verified=True,
    )

    governance_registry.register_source_reference(
        unrelated_source
    )

    unrelated_matter = PatentMatter(
        id="MAT-OTHER-001",
        title="Unrelated Patent Matter",
        matter_type=MatterType.OTHER,
        source_references=[
            unrelated_source.id,
        ],
    )

    governance_registry.register_matter(
        unrelated_matter
    )

    evidence_registry = PatentEvidenceRegistry(
        governance_registry
    )

    unrelated_evidence = EvidenceItem(
        id="EVD-OTHER-001",
        matter_id=unrelated_matter.id,
        title="Unrelated Evidence",
        evidence_type=EvidenceType.OTHER,
        evidence_date=date(2026, 1, 1),
        source_references=[
            unrelated_source.id,
        ],
    )

    evidence_registry.register_evidence(
        unrelated_evidence
    )

    bootstrap_confirmed_patent_evidence(
        governance_registry,
        evidence_registry,
    )

    assert evidence_registry.get_evidence(
        "EVD-OTHER-001"
    ) is not None

    assert len(evidence_registry.list_evidence()) == 18