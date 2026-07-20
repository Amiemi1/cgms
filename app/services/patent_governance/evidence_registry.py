from __future__ import annotations

from datetime import date
from threading import RLock
from typing import TypeVar

from pydantic import BaseModel

from app.services.patent_governance.models import (
    EvidenceCollection,
    EvidenceItem,
    EvidenceSnapshot,
    EvidenceVerification,
    PatentDocument,
    VerificationStatus,
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


class PatentEvidenceRegistry:
    """
    Thread-safe registry for patent documents, evidence,
    verification records and evidence collections.

    Patent matters and source references remain authoritative
    in PatentGovernanceRegistry and are validated before
    evidence records are accepted.
    """

    def __init__(
        self,
        governance_registry: PatentGovernanceRegistry | None = None,
    ) -> None:
        self._lock = RLock()

        self._governance_registry = (
            governance_registry
            if governance_registry is not None
            else get_patent_governance_registry()
        )

        self._documents: dict[str, PatentDocument] = {}
        self._evidence: dict[str, EvidenceItem] = {}
        self._verifications: dict[
            str,
            EvidenceVerification,
        ] = {}
        self._collections: dict[
            str,
            EvidenceCollection,
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
        evidence_id: str,
    ) -> None:
        if evidence_id not in self._evidence:
            raise MissingPatentReferenceError(
                f"Evidence item '{evidence_id}' does not exist."
            )

    def _assert_document_exists(
        self,
        document_id: str,
    ) -> None:
        if document_id not in self._documents:
            raise MissingPatentReferenceError(
                f"Patent document '{document_id}' does not exist."
            )

    def register_document(
        self,
        document: PatentDocument,
        *,
        replace: bool = False,
    ) -> None:
        with self._lock:
            self._assert_matter_exists(
                document.matter_id,
            )

            self._assert_sources_exist(
                document.source_references,
            )

            self._assert_unique(
                document.id,
                self._documents,
                "Patent document",
                replace,
            )

            self._documents[
                document.id
            ] = _copy_record(document)

    def register_evidence(
        self,
        evidence: EvidenceItem,
        *,
        replace: bool = False,
    ) -> None:
        with self._lock:
            self._assert_matter_exists(
                evidence.matter_id,
            )

            self._assert_sources_exist(
                evidence.source_references,
            )

            self._assert_unique(
                evidence.id,
                self._evidence,
                "Evidence item",
                replace,
            )

            self._evidence[
                evidence.id
            ] = _copy_record(evidence)

    def register_verification(
        self,
        verification: EvidenceVerification,
        *,
        replace: bool = False,
    ) -> None:
        with self._lock:
            self._assert_matter_exists(
                verification.matter_id,
            )

            self._assert_evidence_exists(
                verification.evidence_id,
            )

            evidence = self._evidence[
                verification.evidence_id
            ]

            if evidence.matter_id != verification.matter_id:
                raise MissingPatentReferenceError(
                    "Evidence verification matter does not "
                    "match the referenced evidence item."
                )

            self._assert_sources_exist(
                verification.source_references,
            )

            self._assert_unique(
                verification.id,
                self._verifications,
                "Evidence verification",
                replace,
            )

            self._verifications[
                verification.id
            ] = _copy_record(verification)

    def register_collection(
        self,
        collection: EvidenceCollection,
        *,
        replace: bool = False,
    ) -> None:
        with self._lock:
            self._assert_matter_exists(
                collection.matter_id,
            )

            self._assert_sources_exist(
                collection.source_references,
            )

            for evidence_id in collection.evidence_ids:
                self._assert_evidence_exists(
                    evidence_id
                )

                if (
                    self._evidence[evidence_id].matter_id
                    != collection.matter_id
                ):
                    raise MissingPatentReferenceError(
                        "Evidence collection matter does not "
                        "match one or more evidence items."
                    )

            for document_id in collection.document_ids:
                self._assert_document_exists(
                    document_id
                )

                if (
                    self._documents[document_id].matter_id
                    != collection.matter_id
                ):
                    raise MissingPatentReferenceError(
                        "Evidence collection matter does not "
                        "match one or more patent documents."
                    )

            self._assert_unique(
                collection.id,
                self._collections,
                "Evidence collection",
                replace,
            )

            self._collections[
                collection.id
            ] = _copy_record(collection)

    def get_document(
        self,
        document_id: str,
    ) -> PatentDocument | None:
        with self._lock:
            record = self._documents.get(
                document_id
            )

            if record is None:
                return None

            return _copy_record(record)

    def get_evidence(
        self,
        evidence_id: str,
    ) -> EvidenceItem | None:
        with self._lock:
            record = self._evidence.get(
                evidence_id
            )

            if record is None:
                return None

            return _copy_record(record)

    def get_verification(
        self,
        verification_id: str,
    ) -> EvidenceVerification | None:
        with self._lock:
            record = self._verifications.get(
                verification_id
            )

            if record is None:
                return None

            return _copy_record(record)

    def get_collection(
        self,
        collection_id: str,
    ) -> EvidenceCollection | None:
        with self._lock:
            record = self._collections.get(
                collection_id
            )

            if record is None:
                return None

            return _copy_record(record)

    def list_documents(
        self,
        *,
        matter_id: str | None = None,
    ) -> list[PatentDocument]:
        with self._lock:
            records = [
                record
                for record in self._documents.values()
                if (
                    matter_id is None
                    or record.matter_id == matter_id
                )
            ]

            return [
                _copy_record(record)
                for record in sorted(
                    records,
                    key=lambda item: (
                        item.document_date or date.max,
                        item.id,
                    ),
                )
            ]

    def list_evidence(
        self,
        *,
        matter_id: str | None = None,
    ) -> list[EvidenceItem]:
        with self._lock:
            records = [
                record
                for record in self._evidence.values()
                if (
                    matter_id is None
                    or record.matter_id == matter_id
                )
            ]

            return [
                _copy_record(record)
                for record in sorted(
                    records,
                    key=lambda item: (
                        item.evidence_date or date.max,
                        item.id,
                    ),
                )
            ]

    def list_verifications(
        self,
        *,
        matter_id: str | None = None,
        evidence_id: str | None = None,
    ) -> list[EvidenceVerification]:
        with self._lock:
            records = [
                record
                for record in self._verifications.values()
                if (
                    matter_id is None
                    or record.matter_id == matter_id
                )
                and (
                    evidence_id is None
                    or record.evidence_id == evidence_id
                )
            ]

            return [
                _copy_record(record)
                for record in sorted(
                    records,
                    key=lambda item: (
                        item.verified_date or date.max,
                        item.id,
                    ),
                )
            ]

    def list_collections(
        self,
        *,
        matter_id: str | None = None,
    ) -> list[EvidenceCollection]:
        with self._lock:
            records = [
                record
                for record in self._collections.values()
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

    def build_snapshot(
        self,
        matter_id: str,
    ) -> EvidenceSnapshot:
        with self._lock:
            self._assert_matter_exists(
                matter_id
            )

            documents = self.list_documents(
                matter_id=matter_id,
            )

            evidence = self.list_evidence(
                matter_id=matter_id,
            )

            verifications = self.list_verifications(
                matter_id=matter_id,
            )

            collections = self.list_collections(
                matter_id=matter_id,
            )

            verified_evidence_ids = {
                verification.evidence_id
                for verification in verifications
                if (
                    verification.status
                    == VerificationStatus.VERIFIED
                )
            }

            filing_relationship_counts: dict[
                str,
                int,
            ] = {}

            evidence_type_counts: dict[
                str,
                int,
            ] = {}

            referenced_source_ids: set[str] = set()

            for document in documents:
                referenced_source_ids.update(
                    document.source_references
                )

            for item in evidence:
                relationship_key = (
                    item.filing_relationship.value
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

                evidence_type_key = (
                    item.evidence_type.value
                )

                evidence_type_counts[
                    evidence_type_key
                ] = (
                    evidence_type_counts.get(
                        evidence_type_key,
                        0,
                    )
                    + 1
                )

                referenced_source_ids.update(
                    item.source_references
                )

            for verification in verifications:
                referenced_source_ids.update(
                    verification.source_references
                )

            for collection in collections:
                referenced_source_ids.update(
                    collection.source_references
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

            return EvidenceSnapshot(
                matter_id=matter_id,
                documents=documents,
                evidence=evidence,
                verifications=verifications,
                collections=collections,
                source_references=source_references,
                total_documents=len(documents),
                total_evidence_items=len(evidence),
                verified_evidence_items=len(
                    verified_evidence_ids
                ),
                filing_relationship_counts=dict(
                    sorted(
                        filing_relationship_counts.items()
                    )
                ),
                evidence_type_counts=dict(
                    sorted(
                        evidence_type_counts.items()
                    )
                ),
            )

    def clear(self) -> None:
        with self._lock:
            self._documents.clear()
            self._evidence.clear()
            self._verifications.clear()
            self._collections.clear()


_EVIDENCE_REGISTRY = PatentEvidenceRegistry()


def get_patent_evidence_registry() -> PatentEvidenceRegistry:
    return _EVIDENCE_REGISTRY


def clear_patent_evidence_registry() -> None:
    _EVIDENCE_REGISTRY.clear()