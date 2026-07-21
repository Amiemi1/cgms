from __future__ import annotations

from threading import RLock
from typing import TypeVar

from pydantic import BaseModel

from app.services.patent_governance.evidence_registry import (
    PatentEvidenceRegistry,
    get_patent_evidence_registry,
)
from app.services.patent_governance.models import (
    ClaimCandidate,
    ClaimCandidateStatus,
    CoverageAssessment,
    InnovationClaimLink,
    InnovationMapSnapshot,
    InnovationRecord,
    LegalReviewStatus,
)
from app.services.patent_governance.registry import (
    DuplicatePatentRecordError,
    MissingPatentReferenceError,
    PatentGovernanceRegistry,
    get_patent_governance_registry,
)


RecordType = TypeVar(
    "RecordType",
    bound=BaseModel,
)


def _copy_record(
    record: RecordType,
) -> RecordType:
    return record.model_copy(deep=True)


class PatentInnovationRegistry:
    """
    Thread-safe registry for technical innovations, possible
    claim candidates, innovation-to-claim links and technical
    filing-coverage assessments.

    Records in this registry are technical governance records.
    They do not constitute filed claims, legal opinions or
    conclusions concerning patentability or enforceability.
    """

    def __init__(
        self,
        governance_registry: PatentGovernanceRegistry | None = None,
        evidence_registry: PatentEvidenceRegistry | None = None,
    ) -> None:
        self._lock = RLock()

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

        self._innovations: dict[
            str,
            InnovationRecord,
        ] = {}

        self._claim_candidates: dict[
            str,
            ClaimCandidate,
        ] = {}

        self._links: dict[
            str,
            InnovationClaimLink,
        ] = {}

        self._coverage_assessments: dict[
            str,
            CoverageAssessment,
        ] = {}

    def _assert_unique(
        self,
        record_id: str,
        records: dict[str, BaseModel],
        record_type: str,
        replace: bool,
    ) -> None:
        if record_id in records and not replace:
            raise DuplicatePatentRecordError(
                f"{record_type} '{record_id}' already exists."
            )

    def _assert_matter_exists(
        self,
        matter_id: str,
    ) -> None:
        if (
            self._governance_registry.get_matter(
                matter_id
            )
            is None
        ):
            raise MissingPatentReferenceError(
                f"Patent matter '{matter_id}' does not exist."
            )

    def _assert_sources_exist(
        self,
        source_reference_ids: list[str],
    ) -> None:
        missing = sorted(
            source_id
            for source_id in source_reference_ids
            if (
                self._governance_registry.get_source_reference(
                    source_id
                )
                is None
            )
        )

        if missing:
            raise MissingPatentReferenceError(
                "Unknown source references: "
                + ", ".join(missing)
                + "."
            )

    def _assert_evidence_exists(
        self,
        evidence_ids: list[str],
    ) -> None:
        missing = sorted(
            evidence_id
            for evidence_id in evidence_ids
            if (
                self._evidence_registry.get_evidence(
                    evidence_id
                )
                is None
            )
        )

        if missing:
            raise MissingPatentReferenceError(
                "Unknown evidence items: "
                + ", ".join(missing)
                + "."
            )

    def _assert_evidence_matches_matter(
        self,
        matter_id: str,
        evidence_ids: list[str],
    ) -> None:
        mismatched = []

        for evidence_id in evidence_ids:
            evidence = self._evidence_registry.get_evidence(
                evidence_id
            )

            if (
                evidence is not None
                and evidence.matter_id != matter_id
            ):
                mismatched.append(evidence_id)

        if mismatched:
            raise MissingPatentReferenceError(
                "Evidence matter mismatch: "
                + ", ".join(sorted(mismatched))
                + "."
            )

    def _assert_innovation_exists(
        self,
        innovation_id: str,
    ) -> None:
        if innovation_id not in self._innovations:
            raise MissingPatentReferenceError(
                f"Innovation record '{innovation_id}' "
                "does not exist."
            )

    def _assert_claim_candidate_exists(
        self,
        claim_candidate_id: str,
    ) -> None:
        if claim_candidate_id not in self._claim_candidates:
            raise MissingPatentReferenceError(
                f"Claim candidate '{claim_candidate_id}' "
                "does not exist."
            )

    def register_innovation(
        self,
        innovation: InnovationRecord,
        *,
        replace: bool = False,
    ) -> None:
        with self._lock:
            self._assert_matter_exists(
                innovation.matter_id
            )

            self._assert_sources_exist(
                innovation.source_references
            )

            self._assert_evidence_exists(
                innovation.evidence_ids
            )

            self._assert_evidence_matches_matter(
                innovation.matter_id,
                innovation.evidence_ids,
            )

            self._assert_unique(
                innovation.id,
                self._innovations,
                "Innovation record",
                replace,
            )

            self._innovations[
                innovation.id
            ] = _copy_record(innovation)

    def register_claim_candidate(
        self,
        claim_candidate: ClaimCandidate,
        *,
        replace: bool = False,
    ) -> None:
        with self._lock:
            self._assert_matter_exists(
                claim_candidate.matter_id
            )

            self._assert_sources_exist(
                claim_candidate.source_references
            )

            self._assert_evidence_exists(
                claim_candidate.evidence_ids
            )

            self._assert_evidence_matches_matter(
                claim_candidate.matter_id,
                claim_candidate.evidence_ids,
            )

            missing_innovation_ids = sorted(
                innovation_id
                for innovation_id
                in claim_candidate.innovation_ids
                if innovation_id not in self._innovations
            )

            if missing_innovation_ids:
                raise MissingPatentReferenceError(
                    "Unknown innovation records: "
                    + ", ".join(
                        missing_innovation_ids
                    )
                    + "."
                )

            mismatched_innovation_ids = sorted(
                innovation_id
                for innovation_id
                in claim_candidate.innovation_ids
                if (
                    self._innovations[
                        innovation_id
                    ].matter_id
                    != claim_candidate.matter_id
                )
            )

            if mismatched_innovation_ids:
                raise MissingPatentReferenceError(
                    "Innovation matter mismatch: "
                    + ", ".join(
                        mismatched_innovation_ids
                    )
                    + "."
                )

            self._assert_unique(
                claim_candidate.id,
                self._claim_candidates,
                "Claim candidate",
                replace,
            )

            self._claim_candidates[
                claim_candidate.id
            ] = _copy_record(claim_candidate)

    def register_link(
        self,
        link: InnovationClaimLink,
        *,
        replace: bool = False,
    ) -> None:
        with self._lock:
            self._assert_matter_exists(
                link.matter_id
            )

            self._assert_innovation_exists(
                link.innovation_id
            )

            self._assert_claim_candidate_exists(
                link.claim_candidate_id
            )

            innovation = self._innovations[
                link.innovation_id
            ]

            claim_candidate = self._claim_candidates[
                link.claim_candidate_id
            ]

            if (
                innovation.matter_id != link.matter_id
                or claim_candidate.matter_id
                != link.matter_id
            ):
                raise MissingPatentReferenceError(
                    "Innovation-claim link matter does not "
                    "match its referenced records."
                )

            self._assert_sources_exist(
                link.source_references
            )

            self._assert_evidence_exists(
                link.evidence_ids
            )

            self._assert_evidence_matches_matter(
                link.matter_id,
                link.evidence_ids,
            )

            self._assert_unique(
                link.id,
                self._links,
                "Innovation-claim link",
                replace,
            )

            self._links[
                link.id
            ] = _copy_record(link)

    def register_coverage_assessment(
        self,
        assessment: CoverageAssessment,
        *,
        replace: bool = False,
    ) -> None:
        with self._lock:
            self._assert_matter_exists(
                assessment.matter_id
            )

            self._assert_innovation_exists(
                assessment.innovation_id
            )

            innovation = self._innovations[
                assessment.innovation_id
            ]

            if innovation.matter_id != assessment.matter_id:
                raise MissingPatentReferenceError(
                    "Coverage-assessment matter does not "
                    "match the referenced innovation."
                )

            self._assert_sources_exist(
                assessment.source_references
            )

            self._assert_unique(
                assessment.id,
                self._coverage_assessments,
                "Coverage assessment",
                replace,
            )

            self._coverage_assessments[
                assessment.id
            ] = _copy_record(assessment)

    def get_innovation(
        self,
        innovation_id: str,
    ) -> InnovationRecord | None:
        with self._lock:
            record = self._innovations.get(
                innovation_id
            )

            if record is None:
                return None

            return _copy_record(record)

    def get_claim_candidate(
        self,
        claim_candidate_id: str,
    ) -> ClaimCandidate | None:
        with self._lock:
            record = self._claim_candidates.get(
                claim_candidate_id
            )

            if record is None:
                return None

            return _copy_record(record)

    def get_link(
        self,
        link_id: str,
    ) -> InnovationClaimLink | None:
        with self._lock:
            record = self._links.get(
                link_id
            )

            if record is None:
                return None

            return _copy_record(record)

    def get_coverage_assessment(
        self,
        assessment_id: str,
    ) -> CoverageAssessment | None:
        with self._lock:
            record = self._coverage_assessments.get(
                assessment_id
            )

            if record is None:
                return None

            return _copy_record(record)

    def list_innovations(
        self,
        *,
        matter_id: str | None = None,
    ) -> list[InnovationRecord]:
        with self._lock:
            records = [
                record
                for record in self._innovations.values()
                if (
                    matter_id is None
                    or record.matter_id == matter_id
                )
            ]

            return [
                _copy_record(record)
                for record in sorted(
                    records,
                    key=lambda item: item.id,
                )
            ]

    def list_claim_candidates(
        self,
        *,
        matter_id: str | None = None,
    ) -> list[ClaimCandidate]:
        with self._lock:
            records = [
                record
                for record
                in self._claim_candidates.values()
                if (
                    matter_id is None
                    or record.matter_id == matter_id
                )
            ]

            return [
                _copy_record(record)
                for record in sorted(
                    records,
                    key=lambda item: item.id,
                )
            ]

    def list_links(
        self,
        *,
        matter_id: str | None = None,
        innovation_id: str | None = None,
        claim_candidate_id: str | None = None,
    ) -> list[InnovationClaimLink]:
        with self._lock:
            records = [
                record
                for record in self._links.values()
                if (
                    matter_id is None
                    or record.matter_id == matter_id
                )
                and (
                    innovation_id is None
                    or record.innovation_id
                    == innovation_id
                )
                and (
                    claim_candidate_id is None
                    or record.claim_candidate_id
                    == claim_candidate_id
                )
            ]

            return [
                _copy_record(record)
                for record in sorted(
                    records,
                    key=lambda item: item.id,
                )
            ]

    def list_coverage_assessments(
        self,
        *,
        matter_id: str | None = None,
        innovation_id: str | None = None,
    ) -> list[CoverageAssessment]:
        with self._lock:
            records = [
                record
                for record
                in self._coverage_assessments.values()
                if (
                    matter_id is None
                    or record.matter_id == matter_id
                )
                and (
                    innovation_id is None
                    or record.innovation_id
                    == innovation_id
                )
            ]

            return [
                _copy_record(record)
                for record in sorted(
                    records,
                    key=lambda item: item.id,
                )
            ]

    def build_snapshot(
        self,
        matter_id: str,
    ) -> InnovationMapSnapshot:
        with self._lock:
            self._assert_matter_exists(
                matter_id
            )

            innovations = self.list_innovations(
                matter_id=matter_id
            )

            claim_candidates = (
                self.list_claim_candidates(
                    matter_id=matter_id
                )
            )

            links = self.list_links(
                matter_id=matter_id
            )

            coverage_assessments = (
                self.list_coverage_assessments(
                    matter_id=matter_id
                )
            )

            innovation_status_counts: dict[
                str,
                int,
            ] = {}

            claim_status_counts: dict[
                str,
                int,
            ] = {}

            filing_relationship_counts: dict[
                str,
                int,
            ] = {}

            referenced_source_ids: set[str] = set()

            for innovation in innovations:
                status_key = innovation.status.value

                innovation_status_counts[
                    status_key
                ] = (
                    innovation_status_counts.get(
                        status_key,
                        0,
                    )
                    + 1
                )

                relationship_key = (
                    innovation.filing_relationship.value
                )

                filing_relationship_counts[
                    relationship_key
                ] = (
                    filing_relationship_counts.get(
                        relationship_key,
                        0,
                    )
                    + 1
                )

                referenced_source_ids.update(
                    innovation.source_references
                )

            for claim_candidate in claim_candidates:
                status_key = claim_candidate.status.value

                claim_status_counts[
                    status_key
                ] = (
                    claim_status_counts.get(
                        status_key,
                        0,
                    )
                    + 1
                )

                referenced_source_ids.update(
                    claim_candidate.source_references
                )

            for link in links:
                referenced_source_ids.update(
                    link.source_references
                )

            for assessment in coverage_assessments:
                referenced_source_ids.update(
                    assessment.source_references
                )

            source_references = []

            for source_id in sorted(
                referenced_source_ids
            ):
                source_reference = (
                    self._governance_registry
                    .get_source_reference(source_id)
                )

                if source_reference is not None:
                    source_references.append(
                        source_reference
                    )

            legally_reviewed_candidates = sum(
                1
                for candidate in claim_candidates
                if (
                    candidate.legal_review_status
                    == LegalReviewStatus.REVIEWED
                    or candidate.status
                    == ClaimCandidateStatus.LEGALLY_REVIEWED
                )
            )

            review_required_candidates = sum(
                1
                for candidate in claim_candidates
                if candidate.legal_review_required
                and (
                    candidate.legal_review_status
                    != LegalReviewStatus.REVIEWED
                )
            )

            return InnovationMapSnapshot(
                matter_id=matter_id,
                innovations=innovations,
                claim_candidates=claim_candidates,
                links=links,
                coverage_assessments=coverage_assessments,
                source_references=source_references,
                total_innovations=len(innovations),
                total_claim_candidates=len(
                    claim_candidates
                ),
                total_links=len(links),
                legally_reviewed_candidates=(
                    legally_reviewed_candidates
                ),
                review_required_candidates=(
                    review_required_candidates
                ),
                innovation_status_counts=dict(
                    sorted(
                        innovation_status_counts.items()
                    )
                ),
                claim_status_counts=dict(
                    sorted(
                        claim_status_counts.items()
                    )
                ),
                filing_relationship_counts=dict(
                    sorted(
                        filing_relationship_counts.items()
                    )
                ),
            )

    def clear(self) -> None:
        with self._lock:
            self._innovations.clear()
            self._claim_candidates.clear()
            self._links.clear()
            self._coverage_assessments.clear()


_INNOVATION_REGISTRY = PatentInnovationRegistry()


def get_patent_innovation_registry() -> PatentInnovationRegistry:
    return _INNOVATION_REGISTRY


def clear_patent_innovation_registry() -> None:
    _INNOVATION_REGISTRY.clear()