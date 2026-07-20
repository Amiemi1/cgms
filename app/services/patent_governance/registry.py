from __future__ import annotations

from datetime import date
from threading import RLock
from typing import TypeVar

from pydantic import BaseModel

from app.services.patent_governance.models import (
    AdministrativeMilestone,
    FilingRecord,
    PatentGovernanceSnapshot,
    PatentMatter,
    SourceReference,
)


RecordType = TypeVar(
    "RecordType",
    bound=BaseModel,
)


class DuplicatePatentRecordError(ValueError):
    """
    Raised when a record is registered with an ID that
    already exists and replacement was not authorized.
    """


class MissingPatentReferenceError(ValueError):
    """
    Raised when a record refers to a matter or source
    reference that does not exist in the registry.
    """


def _copy_record(
    record: RecordType,
) -> RecordType:
    return record.model_copy(deep=True)


class PatentGovernanceRegistry:
    """
    Thread-safe, in-memory registry for governed patent records.

    Stored and returned records are deep copies so callers cannot
    mutate the authoritative registry accidentally.
    """

    def __init__(self) -> None:
        self._lock = RLock()

        self._matters: dict[str, PatentMatter] = {}
        self._filings: dict[str, FilingRecord] = {}
        self._milestones: dict[
            str,
            AdministrativeMilestone,
        ] = {}
        self._source_references: dict[
            str,
            SourceReference,
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
        if matter_id not in self._matters:
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
            if source_id not in self._source_references
        )

        if missing:
            raise MissingPatentReferenceError(
                "Unknown source references: "
                + ", ".join(missing)
                + "."
            )

    def register_source_reference(
        self,
        source_reference: SourceReference,
        *,
        replace: bool = False,
    ) -> None:
        with self._lock:
            self._assert_unique(
                source_reference.id,
                self._source_references,
                "Source reference",
                replace,
            )

            self._source_references[
                source_reference.id
            ] = _copy_record(source_reference)

    def register_matter(
        self,
        matter: PatentMatter,
        *,
        replace: bool = False,
    ) -> None:
        with self._lock:
            self._assert_sources_exist(
                matter.source_references,
            )

            self._assert_unique(
                matter.id,
                self._matters,
                "Patent matter",
                replace,
            )

            self._matters[matter.id] = _copy_record(matter)

    def register_filing(
        self,
        filing: FilingRecord,
        *,
        replace: bool = False,
    ) -> None:
        with self._lock:
            self._assert_matter_exists(
                filing.matter_id,
            )

            self._assert_sources_exist(
                filing.source_references,
            )

            self._assert_unique(
                filing.id,
                self._filings,
                "Filing record",
                replace,
            )

            self._filings[filing.id] = _copy_record(filing)

    def register_milestone(
        self,
        milestone: AdministrativeMilestone,
        *,
        replace: bool = False,
    ) -> None:
        with self._lock:
            self._assert_matter_exists(
                milestone.matter_id,
            )

            self._assert_sources_exist(
                milestone.source_references,
            )

            self._assert_unique(
                milestone.id,
                self._milestones,
                "Administrative milestone",
                replace,
            )

            self._milestones[
                milestone.id
            ] = _copy_record(milestone)

    def get_source_reference(
        self,
        source_reference_id: str,
    ) -> SourceReference | None:
        with self._lock:
            record = self._source_references.get(
                source_reference_id,
            )

            if record is None:
                return None

            return _copy_record(record)

    def get_matter(
        self,
        matter_id: str,
    ) -> PatentMatter | None:
        with self._lock:
            record = self._matters.get(matter_id)

            if record is None:
                return None

            return _copy_record(record)

    def get_filing(
        self,
        filing_id: str,
    ) -> FilingRecord | None:
        with self._lock:
            record = self._filings.get(filing_id)

            if record is None:
                return None

            return _copy_record(record)

    def get_milestone(
        self,
        milestone_id: str,
    ) -> AdministrativeMilestone | None:
        with self._lock:
            record = self._milestones.get(
                milestone_id,
            )

            if record is None:
                return None

            return _copy_record(record)

    def list_source_references(
        self,
    ) -> list[SourceReference]:
        with self._lock:
            return [
                _copy_record(record)
                for record in sorted(
                    self._source_references.values(),
                    key=lambda item: item.id,
                )
            ]

    def list_matters(
        self,
    ) -> list[PatentMatter]:
        with self._lock:
            return [
                _copy_record(record)
                for record in sorted(
                    self._matters.values(),
                    key=lambda item: item.id,
                )
            ]

    def list_filings(
        self,
        *,
        matter_id: str | None = None,
    ) -> list[FilingRecord]:
        with self._lock:
            records = [
                record
                for record in self._filings.values()
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
                        item.filing_date or date.max,
                        item.id,
                    ),
                )
            ]

    def list_milestones(
        self,
        *,
        matter_id: str | None = None,
    ) -> list[AdministrativeMilestone]:
        with self._lock:
            records = [
                record
                for record in self._milestones.values()
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
                        item.milestone_date or date.max,
                        item.id,
                    ),
                )
            ]

    def build_snapshot(
        self,
        matter_id: str,
    ) -> PatentGovernanceSnapshot:
        with self._lock:
            matter = self._matters.get(matter_id)

            if matter is None:
                raise MissingPatentReferenceError(
                    f"Patent matter '{matter_id}' does not exist."
                )

            filings = self.list_filings(
                matter_id=matter_id,
            )

            milestones = self.list_milestones(
                matter_id=matter_id,
            )

            referenced_source_ids = set(
                matter.source_references
            )

            for filing in filings:
                referenced_source_ids.update(
                    filing.source_references
                )

            for milestone in milestones:
                referenced_source_ids.update(
                    milestone.source_references
                )

            sources = [
                _copy_record(
                    self._source_references[source_id]
                )
                for source_id in sorted(
                    referenced_source_ids
                )
            ]

            return PatentGovernanceSnapshot(
                matter=_copy_record(matter),
                filings=filings,
                milestones=milestones,
                source_references=sources,
            )

    def clear(self) -> None:
        with self._lock:
            self._matters.clear()
            self._filings.clear()
            self._milestones.clear()
            self._source_references.clear()


_REGISTRY = PatentGovernanceRegistry()


def get_patent_governance_registry() -> PatentGovernanceRegistry:
    return _REGISTRY


def clear_patent_governance_registry() -> None:
    _REGISTRY.clear()