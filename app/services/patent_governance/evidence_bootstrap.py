from __future__ import annotations

from datetime import date

from app.services.patent_governance.bootstrap import (
    CGMS_PATENT_MATTER_ID,
    bootstrap_confirmed_patent_records,
)
from app.services.patent_governance.evidence_registry import (
    PatentEvidenceRegistry,
    get_patent_evidence_registry,
)
from app.services.patent_governance.models import (
    ConfidentialityLevel,
    EvidenceCollection,
    EvidenceItem,
    EvidenceType,
    EvidenceVerification,
    FilingRelationship,
    PatentDocument,
    RecordStatus,
    SourceReference,
    VerificationStatus,
)
from app.services.patent_governance.registry import (
    PatentGovernanceRegistry,
    get_patent_governance_registry,
)


EVIDENCE_AUDIT_DATE = date(2026, 7, 20)


REPOSITORY_EVIDENCE_SOURCES: tuple[
    SourceReference,
    ...
] = (
    SourceReference(
        id="SRC-CGMS-EVD-001",
        label="CGMS Architecture Claims document",
        repository_path="docs/architecture_claims.md",
        verified=True,
        confidentiality=ConfidentialityLevel.CONFIDENTIAL,
        notes=(
            "Internal technical-positioning document. "
            "It is not a legally reviewed claim set."
        ),
    ),
    SourceReference(
        id="SRC-CGMS-EVD-002",
        label="Runtime Governance Claims document",
        repository_path="docs/runtime_governance_claims.md",
        verified=True,
        confidentiality=ConfidentialityLevel.CONFIDENTIAL,
        notes=(
            "Internal description of runtime-governance "
            "capabilities. It is not a legal opinion."
        ),
    ),
    SourceReference(
        id="SRC-CGMS-EVD-003",
        label="Patent Expansion Notes",
        repository_path="docs/patent_expansion_notes.md",
        verified=True,
        confidentiality=(
            ConfidentialityLevel.HIGHLY_CONFIDENTIAL
        ),
        notes=(
            "Potential future claim-expansion concepts. "
            "No legal coverage conclusion is implied."
        ),
    ),
    SourceReference(
        id="SRC-CGMS-EVD-004",
        label="CGMS Platform Architecture Map",
        repository_path=(
            "docs/architecture/"
            "CGMS_Platform_Architecture_Map.md"
        ),
        verified=True,
        confidentiality=ConfidentialityLevel.CONFIDENTIAL,
    ),
    SourceReference(
        id="SRC-CGMS-EVD-005",
        label="CGMS v2 Domain Model and Enterprise Architecture",
        repository_path=(
            "docs/architecture/"
            "CGMS_v2_Domain_Model_and_Enterprise_Architecture.md"
        ),
        verified=True,
        confidentiality=ConfidentialityLevel.CONFIDENTIAL,
    ),
    SourceReference(
        id="SRC-CGMS-EVD-006",
        label="CGMS Product Architecture Blueprint",
        repository_path=(
            "docs/product/"
            "CGMS_Product_Architecture_Blueprint.md"
        ),
        verified=True,
        confidentiality=ConfidentialityLevel.CONFIDENTIAL,
    ),
    SourceReference(
        id="SRC-CGMS-EVD-007",
        label="CGMS Product Capability Prioritisation Matrix",
        repository_path=(
            "docs/product/"
            "CGMS_Product_Capability_and_Feature_"
            "Prioritization_Matrix.md"
        ),
        verified=True,
        confidentiality=ConfidentialityLevel.CONFIDENTIAL,
    ),
    SourceReference(
        id="SRC-CGMS-EVD-008",
        label="CGMS v1.60 regression test report",
        repository_path="artifacts/test-report-v1.60.txt",
        release_tag="cgms-v1.60",
        verified=True,
        confidentiality=ConfidentialityLevel.INTERNAL,
        notes=(
            "Tracked regression report recording 32 passed "
            "tests and seven runtime warnings."
        ),
    ),
    SourceReference(
        id="SRC-CGMS-EVD-009",
        label="Event-driven orchestration implementation commit",
        git_commit="24e55cb",
        source_date=date(2026, 6, 11),
        verified=True,
        confidentiality=ConfidentialityLevel.CONFIDENTIAL,
    ),
    SourceReference(
        id="SRC-CGMS-EVD-010",
        label="Connector ingestion implementation commit",
        git_commit="a7f85d0",
        source_date=date(2026, 6, 13),
        verified=True,
        confidentiality=ConfidentialityLevel.CONFIDENTIAL,
    ),
    SourceReference(
        id="SRC-CGMS-EVD-011",
        label="Multi-workspace runtime implementation commit",
        git_commit="0231a32",
        source_date=date(2026, 6, 15),
        verified=True,
        confidentiality=ConfidentialityLevel.CONFIDENTIAL,
    ),
    SourceReference(
        id="SRC-CGMS-EVD-012",
        label="Tenant governance implementation commit",
        git_commit="9720e1c",
        source_date=date(2026, 6, 16),
        verified=True,
        confidentiality=ConfidentialityLevel.CONFIDENTIAL,
    ),
    SourceReference(
        id="SRC-CGMS-EVD-013",
        label="Connector adapter implementation commit",
        git_commit="9158388",
        source_date=date(2026, 6, 17),
        verified=True,
        confidentiality=ConfidentialityLevel.CONFIDENTIAL,
    ),
    SourceReference(
        id="SRC-CGMS-EVD-014",
        label="Memory Intelligence implementation commit",
        git_commit="37ccaec",
        release_tag="cgms-v1.74-memory-intelligence",
        source_date=date(2026, 6, 28),
        verified=True,
        confidentiality=ConfidentialityLevel.CONFIDENTIAL,
    ),
    SourceReference(
        id="SRC-CGMS-EVD-015",
        label="Enterprise Event Bus implementation commit",
        git_commit="918de5a",
        release_tag="cgms-v1.75-enterprise-event-bus",
        source_date=date(2026, 7, 6),
        verified=True,
        confidentiality=ConfidentialityLevel.CONFIDENTIAL,
    ),
    SourceReference(
        id="SRC-CGMS-EVD-016",
        label="Product Readiness dashboard implementation commit",
        git_commit="7e358a4",
        source_date=date(2026, 7, 18),
        verified=True,
        confidentiality=ConfidentialityLevel.CONFIDENTIAL,
    ),
    SourceReference(
        id="SRC-CGMS-EVD-017",
        label="Product Readiness CI gate implementation commit",
        git_commit="94e0c59",
        source_date=date(2026, 7, 20),
        verified=True,
        confidentiality=ConfidentialityLevel.CONFIDENTIAL,
    ),
)


CONFIRMED_PATENT_DOCUMENTS: tuple[
    PatentDocument,
    ...
] = (
    PatentDocument(
        id="DOC-CGMS-001",
        matter_id=CGMS_PATENT_MATTER_ID,
        title="CGMS Architecture Claims",
        document_type="technical_positioning_note",
        filed=False,
        confidentiality=ConfidentialityLevel.CONFIDENTIAL,
        repository_path="docs/architecture_claims.md",
        source_references=["SRC-CGMS-EVD-001"],
        status=RecordStatus.COMPLETE,
        notes=(
            "Internal technical-positioning document. "
            "It is not recorded as a filed patent document."
        ),
    ),
    PatentDocument(
        id="DOC-CGMS-002",
        matter_id=CGMS_PATENT_MATTER_ID,
        title="Runtime Governance Claims",
        document_type="technical_positioning_note",
        filed=False,
        confidentiality=ConfidentialityLevel.CONFIDENTIAL,
        repository_path="docs/runtime_governance_claims.md",
        source_references=["SRC-CGMS-EVD-002"],
        status=RecordStatus.COMPLETE,
        notes=(
            "Internal capability summary. It is not recorded "
            "as a legally reviewed or filed claim set."
        ),
    ),
    PatentDocument(
        id="DOC-CGMS-003",
        matter_id=CGMS_PATENT_MATTER_ID,
        title="Patent Expansion Notes",
        document_type="claim_expansion_working_note",
        filed=False,
        confidentiality=(
            ConfidentialityLevel.HIGHLY_CONFIDENTIAL
        ),
        repository_path="docs/patent_expansion_notes.md",
        source_references=["SRC-CGMS-EVD-003"],
        status=RecordStatus.IN_PROGRESS,
        notes=(
            "Working concepts for possible future protection. "
            "Coverage remains unassessed."
        ),
    ),
)


CONFIRMED_EVIDENCE_ITEMS: tuple[
    EvidenceItem,
    ...
] = (
    EvidenceItem(
        id="EVD-CGMS-001",
        matter_id=CGMS_PATENT_MATTER_ID,
        title="Architecture claims technical positioning",
        evidence_type=EvidenceType.ARCHITECTURE_DOCUMENT,
        filing_relationship=FilingRelationship.NOT_ASSESSED,
        repository_path="docs/architecture_claims.md",
        confidentiality=ConfidentialityLevel.CONFIDENTIAL,
        status=RecordStatus.VERIFIED,
        verified=True,
        source_references=["SRC-CGMS-EVD-001"],
        notes=(
            "Supports the documented technical architecture "
            "position but does not establish legal claim scope."
        ),
    ),
    EvidenceItem(
        id="EVD-CGMS-002",
        matter_id=CGMS_PATENT_MATTER_ID,
        title="Runtime governance technical positioning",
        evidence_type=EvidenceType.ARCHITECTURE_DOCUMENT,
        filing_relationship=FilingRelationship.NOT_ASSESSED,
        repository_path="docs/runtime_governance_claims.md",
        confidentiality=ConfidentialityLevel.CONFIDENTIAL,
        status=RecordStatus.VERIFIED,
        verified=True,
        source_references=["SRC-CGMS-EVD-002"],
    ),
    EvidenceItem(
        id="EVD-CGMS-003",
        matter_id=CGMS_PATENT_MATTER_ID,
        title="Potential patent-expansion concepts",
        evidence_type=EvidenceType.PRODUCT_DOCUMENT,
        filing_relationship=(
            FilingRelationship.POTENTIAL_FUTURE_FILING
        ),
        repository_path="docs/patent_expansion_notes.md",
        confidentiality=(
            ConfidentialityLevel.HIGHLY_CONFIDENTIAL
        ),
        status=RecordStatus.IN_PROGRESS,
        verified=True,
        source_references=["SRC-CGMS-EVD-003"],
        notes=(
            "Records potential future subject matter only. "
            "No patentability or coverage conclusion is made."
        ),
    ),
    EvidenceItem(
        id="EVD-CGMS-004",
        matter_id=CGMS_PATENT_MATTER_ID,
        title="CGMS Platform Architecture Map",
        evidence_type=EvidenceType.ARCHITECTURE_DOCUMENT,
        filing_relationship=FilingRelationship.NOT_ASSESSED,
        repository_path=(
            "docs/architecture/"
            "CGMS_Platform_Architecture_Map.md"
        ),
        confidentiality=ConfidentialityLevel.CONFIDENTIAL,
        status=RecordStatus.COMPLETE,
        verified=True,
        source_references=["SRC-CGMS-EVD-004"],
    ),
    EvidenceItem(
        id="EVD-CGMS-005",
        matter_id=CGMS_PATENT_MATTER_ID,
        title="CGMS enterprise domain model",
        evidence_type=EvidenceType.ARCHITECTURE_DOCUMENT,
        filing_relationship=FilingRelationship.NOT_ASSESSED,
        repository_path=(
            "docs/architecture/"
            "CGMS_v2_Domain_Model_and_Enterprise_Architecture.md"
        ),
        confidentiality=ConfidentialityLevel.CONFIDENTIAL,
        status=RecordStatus.COMPLETE,
        verified=True,
        source_references=["SRC-CGMS-EVD-005"],
    ),
    EvidenceItem(
        id="EVD-CGMS-006",
        matter_id=CGMS_PATENT_MATTER_ID,
        title="CGMS Product Architecture Blueprint",
        evidence_type=EvidenceType.PRODUCT_DOCUMENT,
        filing_relationship=FilingRelationship.NOT_ASSESSED,
        repository_path=(
            "docs/product/"
            "CGMS_Product_Architecture_Blueprint.md"
        ),
        confidentiality=ConfidentialityLevel.CONFIDENTIAL,
        status=RecordStatus.COMPLETE,
        verified=True,
        source_references=["SRC-CGMS-EVD-006"],
    ),
    EvidenceItem(
        id="EVD-CGMS-007",
        matter_id=CGMS_PATENT_MATTER_ID,
        title="CGMS capability prioritisation matrix",
        evidence_type=EvidenceType.PRODUCT_DOCUMENT,
        filing_relationship=FilingRelationship.NOT_ASSESSED,
        repository_path=(
            "docs/product/"
            "CGMS_Product_Capability_and_Feature_"
            "Prioritization_Matrix.md"
        ),
        confidentiality=ConfidentialityLevel.CONFIDENTIAL,
        status=RecordStatus.COMPLETE,
        verified=True,
        source_references=["SRC-CGMS-EVD-007"],
    ),
    EvidenceItem(
        id="EVD-CGMS-008",
        matter_id=CGMS_PATENT_MATTER_ID,
        title="CGMS v1.60 regression test report",
        evidence_type=EvidenceType.TEST_REPORT,
        filing_relationship=FilingRelationship.NOT_ASSESSED,
        repository_path="artifacts/test-report-v1.60.txt",
        release_tag="cgms-v1.60",
        confidentiality=ConfidentialityLevel.INTERNAL,
        status=RecordStatus.VERIFIED,
        verified=True,
        source_references=["SRC-CGMS-EVD-008"],
        notes=(
            "Records 32 passed tests and seven runtime "
            "warnings. The warnings remain part of the record."
        ),
    ),
    EvidenceItem(
        id="EVD-CGMS-009",
        matter_id=CGMS_PATENT_MATTER_ID,
        title="Event-driven orchestration implementation",
        evidence_type=EvidenceType.GIT_COMMIT,
        evidence_date=date(2026, 6, 11),
        filing_relationship=(
            FilingRelationship.POST_FILING_DEVELOPMENT
        ),
        git_commit="24e55cb",
        confidentiality=ConfidentialityLevel.CONFIDENTIAL,
        status=RecordStatus.COMPLETE,
        verified=True,
        source_references=["SRC-CGMS-EVD-009"],
    ),
    EvidenceItem(
        id="EVD-CGMS-010",
        matter_id=CGMS_PATENT_MATTER_ID,
        title="Connector ingestion implementation",
        evidence_type=EvidenceType.GIT_COMMIT,
        evidence_date=date(2026, 6, 13),
        filing_relationship=(
            FilingRelationship.POST_FILING_DEVELOPMENT
        ),
        git_commit="a7f85d0",
        confidentiality=ConfidentialityLevel.CONFIDENTIAL,
        status=RecordStatus.COMPLETE,
        verified=True,
        source_references=["SRC-CGMS-EVD-010"],
    ),
    EvidenceItem(
        id="EVD-CGMS-011",
        matter_id=CGMS_PATENT_MATTER_ID,
        title="Multi-workspace runtime implementation",
        evidence_type=EvidenceType.GIT_COMMIT,
        evidence_date=date(2026, 6, 15),
        filing_relationship=(
            FilingRelationship.POST_FILING_DEVELOPMENT
        ),
        git_commit="0231a32",
        confidentiality=ConfidentialityLevel.CONFIDENTIAL,
        status=RecordStatus.COMPLETE,
        verified=True,
        source_references=["SRC-CGMS-EVD-011"],
    ),
    EvidenceItem(
        id="EVD-CGMS-012",
        matter_id=CGMS_PATENT_MATTER_ID,
        title="Tenant governance and quota enforcement",
        evidence_type=EvidenceType.GIT_COMMIT,
        evidence_date=date(2026, 6, 16),
        filing_relationship=(
            FilingRelationship.POST_FILING_DEVELOPMENT
        ),
        git_commit="9720e1c",
        confidentiality=ConfidentialityLevel.CONFIDENTIAL,
        status=RecordStatus.COMPLETE,
        verified=True,
        source_references=["SRC-CGMS-EVD-012"],
    ),
    EvidenceItem(
        id="EVD-CGMS-013",
        matter_id=CGMS_PATENT_MATTER_ID,
        title="Connector adapter layer implementation",
        evidence_type=EvidenceType.GIT_COMMIT,
        evidence_date=date(2026, 6, 17),
        filing_relationship=(
            FilingRelationship.POST_FILING_DEVELOPMENT
        ),
        git_commit="9158388",
        confidentiality=ConfidentialityLevel.CONFIDENTIAL,
        status=RecordStatus.COMPLETE,
        verified=True,
        source_references=["SRC-CGMS-EVD-013"],
    ),
    EvidenceItem(
        id="EVD-CGMS-014",
        matter_id=CGMS_PATENT_MATTER_ID,
        title="Memory Intelligence Engine implementation",
        evidence_type=EvidenceType.RELEASE_TAG,
        evidence_date=date(2026, 6, 28),
        filing_relationship=(
            FilingRelationship.POST_FILING_DEVELOPMENT
        ),
        git_commit="37ccaec",
        release_tag="cgms-v1.74-memory-intelligence",
        confidentiality=ConfidentialityLevel.CONFIDENTIAL,
        status=RecordStatus.COMPLETE,
        verified=True,
        source_references=["SRC-CGMS-EVD-014"],
    ),
    EvidenceItem(
        id="EVD-CGMS-015",
        matter_id=CGMS_PATENT_MATTER_ID,
        title="Enterprise Event Bus implementation",
        evidence_type=EvidenceType.RELEASE_TAG,
        evidence_date=date(2026, 7, 6),
        filing_relationship=(
            FilingRelationship.POST_FILING_DEVELOPMENT
        ),
        git_commit="918de5a",
        release_tag="cgms-v1.75-enterprise-event-bus",
        confidentiality=ConfidentialityLevel.CONFIDENTIAL,
        status=RecordStatus.COMPLETE,
        verified=True,
        source_references=["SRC-CGMS-EVD-015"],
    ),
    EvidenceItem(
        id="EVD-CGMS-016",
        matter_id=CGMS_PATENT_MATTER_ID,
        title="Integrated Product Readiness dashboard",
        evidence_type=EvidenceType.GIT_COMMIT,
        evidence_date=date(2026, 7, 18),
        filing_relationship=(
            FilingRelationship.POST_FILING_DEVELOPMENT
        ),
        git_commit="7e358a4",
        confidentiality=ConfidentialityLevel.CONFIDENTIAL,
        status=RecordStatus.COMPLETE,
        verified=True,
        source_references=["SRC-CGMS-EVD-016"],
    ),
    EvidenceItem(
        id="EVD-CGMS-017",
        matter_id=CGMS_PATENT_MATTER_ID,
        title="Product Readiness CI gates",
        evidence_type=EvidenceType.GIT_COMMIT,
        evidence_date=date(2026, 7, 20),
        filing_relationship=(
            FilingRelationship.POST_FILING_DEVELOPMENT
        ),
        git_commit="94e0c59",
        confidentiality=ConfidentialityLevel.CONFIDENTIAL,
        status=RecordStatus.COMPLETE,
        verified=True,
        source_references=["SRC-CGMS-EVD-017"],
    ),
)


def _verification(
    *,
    verification_id: str,
    evidence_id: str,
    source_id: str,
    status: VerificationStatus,
    repository_path_confirmed: bool = False,
    git_reference_confirmed: bool = False,
    content_reviewed: bool = False,
    findings: str | None = None,
    limitations: str | None = None,
) -> EvidenceVerification:
    return EvidenceVerification(
        id=verification_id,
        matter_id=CGMS_PATENT_MATTER_ID,
        evidence_id=evidence_id,
        status=status,
        verified_by="CGMS repository evidence audit",
        verified_date=EVIDENCE_AUDIT_DATE,
        repository_path_confirmed=repository_path_confirmed,
        git_reference_confirmed=git_reference_confirmed,
        content_reviewed=content_reviewed,
        findings=findings,
        limitations=limitations,
        source_references=[source_id],
    )


CONFIRMED_EVIDENCE_VERIFICATIONS: tuple[
    EvidenceVerification,
    ...
] = (
    _verification(
        verification_id="VER-CGMS-001",
        evidence_id="EVD-CGMS-001",
        source_id="SRC-CGMS-EVD-001",
        status=VerificationStatus.VERIFIED,
        repository_path_confirmed=True,
        content_reviewed=True,
        findings=(
            "The document identifies workspace-aware, "
            "event-driven and governed runtime components."
        ),
        limitations=(
            "Technical content review only; no legal claim "
            "interpretation was performed."
        ),
    ),
    _verification(
        verification_id="VER-CGMS-002",
        evidence_id="EVD-CGMS-002",
        source_id="SRC-CGMS-EVD-002",
        status=VerificationStatus.VERIFIED,
        repository_path_confirmed=True,
        content_reviewed=True,
        findings=(
            "The document identifies health, kill-switch, "
            "quarantine, workspace and commercial controls."
        ),
        limitations=(
            "Technical content review only; no legal claim "
            "interpretation was performed."
        ),
    ),
    _verification(
        verification_id="VER-CGMS-003",
        evidence_id="EVD-CGMS-003",
        source_id="SRC-CGMS-EVD-003",
        status=VerificationStatus.VERIFIED,
        repository_path_confirmed=True,
        content_reviewed=True,
        findings=(
            "Five potential expansion concepts and defensive "
            "positioning principles are recorded."
        ),
        limitations=(
            "The concepts are working notes and have not been "
            "evaluated for patentability or filing coverage."
        ),
    ),
    _verification(
        verification_id="VER-CGMS-004",
        evidence_id="EVD-CGMS-004",
        source_id="SRC-CGMS-EVD-004",
        status=VerificationStatus.PARTIALLY_VERIFIED,
        repository_path_confirmed=True,
        limitations=(
            "Repository path confirmed; full content review "
            "has not yet been recorded."
        ),
    ),
    _verification(
        verification_id="VER-CGMS-005",
        evidence_id="EVD-CGMS-005",
        source_id="SRC-CGMS-EVD-005",
        status=VerificationStatus.PARTIALLY_VERIFIED,
        repository_path_confirmed=True,
        limitations=(
            "Repository path confirmed; full content review "
            "has not yet been recorded."
        ),
    ),
    _verification(
        verification_id="VER-CGMS-006",
        evidence_id="EVD-CGMS-006",
        source_id="SRC-CGMS-EVD-006",
        status=VerificationStatus.PARTIALLY_VERIFIED,
        repository_path_confirmed=True,
        limitations=(
            "Repository path confirmed; full content review "
            "has not yet been recorded."
        ),
    ),
    _verification(
        verification_id="VER-CGMS-007",
        evidence_id="EVD-CGMS-007",
        source_id="SRC-CGMS-EVD-007",
        status=VerificationStatus.PARTIALLY_VERIFIED,
        repository_path_confirmed=True,
        limitations=(
            "Repository path confirmed; full content review "
            "has not yet been recorded."
        ),
    ),
    _verification(
        verification_id="VER-CGMS-008",
        evidence_id="EVD-CGMS-008",
        source_id="SRC-CGMS-EVD-008",
        status=VerificationStatus.VERIFIED,
        repository_path_confirmed=True,
        content_reviewed=True,
        findings="The report records 32 passed tests.",
        limitations=(
            "The same report records seven runtime warnings; "
            "those warnings must not be omitted."
        ),
    ),
    *(
        _verification(
            verification_id=f"VER-CGMS-{index:03d}",
            evidence_id=f"EVD-CGMS-{index:03d}",
            source_id=f"SRC-CGMS-EVD-{index:03d}",
            status=VerificationStatus.PARTIALLY_VERIFIED,
            git_reference_confirmed=True,
            findings=(
                "The Git reference and commit metadata were "
                "confirmed in repository history."
            ),
            limitations=(
                "The verification confirms repository history "
                "only; a complete diff-level technical review "
                "has not yet been recorded."
            ),
        )
        for index in range(9, 18)
    ),
)


CONFIRMED_EVIDENCE_COLLECTIONS: tuple[
    EvidenceCollection,
    ...
] = (
    EvidenceCollection(
        id="COL-CGMS-001",
        matter_id=CGMS_PATENT_MATTER_ID,
        title="Patent and technical positioning documents",
        description=(
            "Internal documents describing architecture, "
            "governance and possible future claim expansion."
        ),
        evidence_ids=[
            "EVD-CGMS-001",
            "EVD-CGMS-002",
            "EVD-CGMS-003",
        ],
        document_ids=[
            "DOC-CGMS-001",
            "DOC-CGMS-002",
            "DOC-CGMS-003",
        ],
        confidentiality=(
            ConfidentialityLevel.HIGHLY_CONFIDENTIAL
        ),
        status=RecordStatus.IN_PROGRESS,
        source_references=[
            "SRC-CGMS-EVD-001",
            "SRC-CGMS-EVD-002",
            "SRC-CGMS-EVD-003",
        ],
        notes=(
            "Requires later legal review before it can support "
            "any formal claim-coverage conclusion."
        ),
    ),
    EvidenceCollection(
        id="COL-CGMS-002",
        matter_id=CGMS_PATENT_MATTER_ID,
        title="Architecture and product evidence",
        description=(
            "Architecture and product-definition records "
            "supporting the technical evolution of CGMS."
        ),
        evidence_ids=[
            "EVD-CGMS-004",
            "EVD-CGMS-005",
            "EVD-CGMS-006",
            "EVD-CGMS-007",
        ],
        confidentiality=ConfidentialityLevel.CONFIDENTIAL,
        status=RecordStatus.IN_PROGRESS,
        source_references=[
            "SRC-CGMS-EVD-004",
            "SRC-CGMS-EVD-005",
            "SRC-CGMS-EVD-006",
            "SRC-CGMS-EVD-007",
        ],
    ),
    EvidenceCollection(
        id="COL-CGMS-003",
        matter_id=CGMS_PATENT_MATTER_ID,
        title="Implementation and release history",
        description=(
            "Dated Git and release evidence for major "
            "post-filing technical developments."
        ),
        evidence_ids=[
            f"EVD-CGMS-{index:03d}"
            for index in range(9, 18)
        ],
        confidentiality=ConfidentialityLevel.CONFIDENTIAL,
        status=RecordStatus.IN_PROGRESS,
        source_references=[
            f"SRC-CGMS-EVD-{index:03d}"
            for index in range(9, 18)
        ],
    ),
    EvidenceCollection(
        id="COL-CGMS-004",
        matter_id=CGMS_PATENT_MATTER_ID,
        title="Regression and validation evidence",
        description=(
            "Tracked regression evidence retained with both "
            "successful results and recorded limitations."
        ),
        evidence_ids=["EVD-CGMS-008"],
        confidentiality=ConfidentialityLevel.INTERNAL,
        status=RecordStatus.COMPLETE,
        source_references=["SRC-CGMS-EVD-008"],
    ),
)


def bootstrap_confirmed_patent_evidence(
    governance_registry: PatentGovernanceRegistry | None = None,
    evidence_registry: PatentEvidenceRegistry | None = None,
) -> dict[str, int]:
    """
    Register the confirmed CGMS patent evidence catalogue.

    The operation is idempotent and replaces only governed
    records with matching IDs.
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

    for source_reference in REPOSITORY_EVIDENCE_SOURCES:
        target_governance_registry.register_source_reference(
            source_reference,
            replace=True,
        )

    for document in CONFIRMED_PATENT_DOCUMENTS:
        target_evidence_registry.register_document(
            document,
            replace=True,
        )

    for evidence in CONFIRMED_EVIDENCE_ITEMS:
        target_evidence_registry.register_evidence(
            evidence,
            replace=True,
        )

    for verification in CONFIRMED_EVIDENCE_VERIFICATIONS:
        target_evidence_registry.register_verification(
            verification,
            replace=True,
        )

    for collection in CONFIRMED_EVIDENCE_COLLECTIONS:
        target_evidence_registry.register_collection(
            collection,
            replace=True,
        )

    return {
        "source_references": len(
            REPOSITORY_EVIDENCE_SOURCES
        ),
        "documents": len(CONFIRMED_PATENT_DOCUMENTS),
        "evidence_items": len(CONFIRMED_EVIDENCE_ITEMS),
        "verifications": len(
            CONFIRMED_EVIDENCE_VERIFICATIONS
        ),
        "collections": len(
            CONFIRMED_EVIDENCE_COLLECTIONS
        ),
    }