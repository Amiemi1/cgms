from __future__ import annotations

from datetime import date
from decimal import Decimal
from typing import Any

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
from app.services.patent_governance.innovation_bootstrap import (
    bootstrap_confirmed_innovation_map,
)
from app.services.patent_governance.innovation_registry import (
    PatentInnovationRegistry,
    get_patent_innovation_registry,
)
from app.services.patent_governance.models import (
    CoveragePosition,
    LegalReviewStatus,
    RecordStatus,
    VerificationStatus,
)
from app.services.patent_governance.registry import (
    PatentGovernanceRegistry,
    get_patent_governance_registry,
)


def _display_status(value: str) -> str:
    return value.replace("_", " ").title()


def _format_date(value: date | None) -> str:
    if value is None:
        return "Date not recorded"

    return value.strftime("%d %B %Y")


def _format_currency(
    value: Decimal | None,
    currency: str = "USD",
) -> str:
    if value is None:
        return "Not recorded"

    return f"{currency} {value:,.2f}"


def _mask_identifier(
    value: str | None,
    *,
    include_sensitive: bool,
) -> str:
    if not value:
        return "Not recorded"

    if include_sensitive:
        return value

    normalized = "".join(
        character
        for character in value
        if character.isalnum()
    )

    if len(normalized) <= 4:
        return "••••"

    return f"••••{normalized[-4:]}"


def _percentage(
    numerator: int,
    denominator: int,
) -> int:
    if denominator <= 0:
        return 0

    return round(
        (numerator / denominator) * 100
    )


class PatentDashboardService:
    """
    Builds the internal Patent and IP Progress Dashboard view.

    The service presents governed operational information only.
    It does not provide legal advice or represent an official
    USPTO status system.
    """

    def __init__(
        self,
        governance_registry: PatentGovernanceRegistry | None = None,
        evidence_registry: PatentEvidenceRegistry | None = None,
        innovation_registry: PatentInnovationRegistry | None = None,
    ) -> None:
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

        self._innovation_registry = (
            innovation_registry
            if innovation_registry is not None
            else get_patent_innovation_registry()
        )

    def ensure_bootstrapped(self) -> None:
        bootstrap_confirmed_patent_records(
            self._governance_registry
        )

        bootstrap_confirmed_patent_evidence(
            self._governance_registry,
            self._evidence_registry,
        )

        bootstrap_confirmed_innovation_map(
            self._governance_registry,
            self._evidence_registry,
            self._innovation_registry,
        )

    def build_view(
        self,
        *,
        matter_id: str = CGMS_PATENT_MATTER_ID,
        include_sensitive: bool = False,
    ) -> dict[str, Any]:
        self.ensure_bootstrapped()

        governance_snapshot = (
            self._governance_registry.build_snapshot(
                matter_id
            )
        )

        evidence_snapshot = (
            self._evidence_registry.build_snapshot(
                matter_id
            )
        )

        innovation_snapshot = (
            self._innovation_registry.build_snapshot(
                matter_id
            )
        )

        matter = governance_snapshot.matter

        filing = (
            governance_snapshot.filings[0]
            if governance_snapshot.filings
            else None
        )

        milestones = governance_snapshot.milestones

        completed_milestone_statuses = {
            RecordStatus.COMPLETE,
            RecordStatus.VERIFIED,
        }

        completed_milestones = sum(
            1
            for milestone in milestones
            if milestone.status
            in completed_milestone_statuses
        )

        verified_evidence = (
            evidence_snapshot.verified_evidence_items
        )

        partially_verified_evidence = sum(
            1
            for verification
            in evidence_snapshot.verifications
            if (
                verification.status
                == VerificationStatus.PARTIALLY_VERIFIED
            )
        )

        reviewed_claim_candidates = sum(
            1
            for candidate
            in innovation_snapshot.claim_candidates
            if (
                candidate.legal_review_status
                == LegalReviewStatus.REVIEWED
            )
        )

        assessed_coverage_records = sum(
            1
            for assessment
            in innovation_snapshot.coverage_assessments
            if (
                assessment.position
                != CoveragePosition.NOT_ASSESSED
            )
        )

        filing_overview = {
            "matter_id": matter.id,
            "title": matter.title,
            "jurisdiction": matter.jurisdiction,
            "matter_type": _display_status(
                matter.matter_type.value
            ),
            "matter_status": _display_status(
                matter.status.value
            ),
            "opened_date": _format_date(
                matter.opened_date
            ),
            "application_number": (
                _mask_identifier(
                    (
                        filing.application_number
                        if filing is not None
                        else None
                    ),
                    include_sensitive=include_sensitive,
                )
            ),
            "confirmation_number": (
                _mask_identifier(
                    (
                        filing.confirmation_number
                        if filing is not None
                        else None
                    ),
                    include_sensitive=include_sensitive,
                )
            ),
            "customer_number": (
                _mask_identifier(
                    (
                        filing.customer_number
                        if filing is not None
                        else None
                    ),
                    include_sensitive=include_sensitive,
                )
            ),
            "patent_center_number": (
                _mask_identifier(
                    (
                        filing.patent_center_number
                        if filing is not None
                        else None
                    ),
                    include_sensitive=include_sensitive,
                )
            ),
            "filing_date": _format_date(
                (
                    filing.filing_date
                    if filing is not None
                    else None
                )
            ),
            "filing_fee": _format_currency(
                (
                    filing.filing_fee
                    if filing is not None
                    else None
                )
            ),
            "identifiers_masked": (
                not include_sensitive
            ),
        }

        timeline = [
            {
                "id": milestone.id,
                "title": milestone.title,
                "type": _display_status(
                    milestone.milestone_type
                ),
                "date": _format_date(
                    milestone.milestone_date
                ),
                "date_value": (
                    milestone.milestone_date.isoformat()
                    if milestone.milestone_date
                    is not None
                    else None
                ),
                "status": _display_status(
                    milestone.status.value
                ),
                "status_value": milestone.status.value,
                "responsible_party": (
                    milestone.responsible_party
                    or "Not assigned"
                ),
                "next_action": milestone.next_action,
                "notes": milestone.notes,
            }
            for milestone in milestones
        ]

        evidence_items = [
            {
                "id": item.id,
                "title": item.title,
                "type": _display_status(
                    item.evidence_type.value
                ),
                "status": _display_status(
                    item.status.value
                ),
                "status_value": item.status.value,
                "filing_relationship": (
                    _display_status(
                        item.filing_relationship.value
                    )
                ),
                "repository_path": item.repository_path,
                "git_commit": item.git_commit,
                "release_tag": item.release_tag,
                "verified": item.verified,
                "notes": item.notes,
            }
            for item in evidence_snapshot.evidence
        ]

        innovations = [
            {
                "id": innovation.id,
                "title": innovation.title,
                "technical_area": (
                    innovation.technical_area
                ),
                "summary": innovation.summary,
                "status": _display_status(
                    innovation.status.value
                ),
                "status_value": innovation.status.value,
                "filing_relationship": (
                    _display_status(
                        innovation.filing_relationship.value
                    )
                ),
                "commercial_significance": (
                    innovation.commercial_significance
                ),
                "evidence_count": len(
                    innovation.evidence_ids
                ),
            }
            for innovation
            in innovation_snapshot.innovations
        ]

        claim_candidates = [
            {
                "id": candidate.id,
                "title": candidate.title,
                "technical_summary": (
                    candidate.technical_summary
                ),
                "candidate_type": _display_status(
                    candidate.candidate_type.value
                ),
                "status": _display_status(
                    candidate.status.value
                ),
                "status_value": candidate.status.value,
                "legal_review_status": (
                    _display_status(
                        candidate.legal_review_status.value
                    )
                ),
                "legal_review_required": (
                    candidate.legal_review_required
                ),
                "innovation_count": len(
                    candidate.innovation_ids
                ),
                "evidence_count": len(
                    candidate.evidence_ids
                ),
                "notes": candidate.notes,
            }
            for candidate
            in innovation_snapshot.claim_candidates
        ]

        actions = self._build_actions(
            milestones=milestones,
            partially_verified_evidence=(
                partially_verified_evidence
            ),
            reviewed_claim_candidates=(
                reviewed_claim_candidates
            ),
            total_claim_candidates=(
                innovation_snapshot
                .total_claim_candidates
            ),
            assessed_coverage_records=(
                assessed_coverage_records
            ),
            total_coverage_records=len(
                innovation_snapshot
                .coverage_assessments
            ),
        )

        return {
            "page": {
                "title": (
                    "CGMS Patent & IP Progress Dashboard"
                ),
                "subtitle": (
                    "Operational filing, evidence and "
                    "innovation governance"
                ),
                "confidential": True,
                "production_access_enabled": False,
            },
            "filing": filing_overview,
            "metrics": {
                "administrative": {
                    "completed": completed_milestones,
                    "total": len(milestones),
                    "percent": _percentage(
                        completed_milestones,
                        len(milestones),
                    ),
                },
                "evidence": {
                    "verified": verified_evidence,
                    "partially_verified": (
                        partially_verified_evidence
                    ),
                    "total": (
                        evidence_snapshot
                        .total_evidence_items
                    ),
                    "percent": _percentage(
                        verified_evidence,
                        evidence_snapshot
                        .total_evidence_items,
                    ),
                },
                "innovations": {
                    "total": (
                        innovation_snapshot
                        .total_innovations
                    ),
                    "deployed": (
                        innovation_snapshot
                        .innovation_status_counts.get(
                            "deployed",
                            0,
                        )
                    ),
                    "implemented": (
                        innovation_snapshot
                        .innovation_status_counts.get(
                            "implemented",
                            0,
                        )
                    ),
                    "in_progress": (
                        innovation_snapshot
                        .innovation_status_counts.get(
                            "in_progress",
                            0,
                        )
                    ),
                },
                "legal_review": {
                    "reviewed": (
                        reviewed_claim_candidates
                    ),
                    "total": (
                        innovation_snapshot
                        .total_claim_candidates
                    ),
                    "percent": _percentage(
                        reviewed_claim_candidates,
                        innovation_snapshot
                        .total_claim_candidates,
                    ),
                },
                "coverage": {
                    "assessed": (
                        assessed_coverage_records
                    ),
                    "total": len(
                        innovation_snapshot
                        .coverage_assessments
                    ),
                    "percent": _percentage(
                        assessed_coverage_records,
                        len(
                            innovation_snapshot
                            .coverage_assessments
                        ),
                    ),
                },
            },
            "timeline": timeline,
            "documents": [
                {
                    "id": document.id,
                    "title": document.title,
                    "document_type": (
                        _display_status(
                            document.document_type
                        )
                    ),
                    "status": _display_status(
                        document.status.value
                    ),
                    "filed": document.filed,
                    "repository_path": (
                        document.repository_path
                    ),
                    "notes": document.notes,
                }
                for document
                in evidence_snapshot.documents
            ],
            "evidence": evidence_items,
            "evidence_collections": [
                {
                    "id": collection.id,
                    "title": collection.title,
                    "description": (
                        collection.description
                    ),
                    "status": _display_status(
                        collection.status.value
                    ),
                    "evidence_count": len(
                        collection.evidence_ids
                    ),
                    "document_count": len(
                        collection.document_ids
                    ),
                    "notes": collection.notes,
                }
                for collection
                in evidence_snapshot.collections
            ],
            "innovations": innovations,
            "claim_candidates": claim_candidates,
            "actions": actions,
            "governance": {
                "legal_disclaimer": (
                    "This dashboard is an internal operational "
                    "record. It is not legal advice, does not "
                    "determine patentability or claim scope, "
                    "and is not an official USPTO status system."
                ),
                "confidentiality_notice": (
                    "Patent filing identifiers and unpublished "
                    "technical information are confidential. "
                    "Production access remains disabled until "
                    "PIP-006 security controls are complete."
                ),
                "coverage_notice": (
                    "Coverage remains unassessed because the "
                    "filed provisional specification has not "
                    "been stored and compared with the mapped "
                    "post-filing innovations."
                ),
            },
        }

    def _build_actions(
        self,
        *,
        milestones: list[Any],
        partially_verified_evidence: int,
        reviewed_claim_candidates: int,
        total_claim_candidates: int,
        assessed_coverage_records: int,
        total_coverage_records: int,
    ) -> list[dict[str, str]]:
        actions: list[dict[str, str]] = []

        for milestone in milestones:
            if milestone.next_action:
                actions.append(
                    {
                        "id": (
                            f"ACT-{milestone.id}"
                        ),
                        "priority": (
                            "High"
                            if milestone.status
                            == RecordStatus.IN_PROGRESS
                            else "Medium"
                        ),
                        "title": milestone.title,
                        "description": (
                            milestone.next_action
                        ),
                        "source": (
                            "Administrative milestone"
                        ),
                    }
                )

        if partially_verified_evidence > 0:
            actions.append(
                {
                    "id": "ACT-EVIDENCE-REVIEW",
                    "priority": "Medium",
                    "title": (
                        "Complete evidence-content review"
                    ),
                    "description": (
                        f"Complete the recorded content review "
                        f"for {partially_verified_evidence} "
                        f"partially verified evidence items."
                    ),
                    "source": "Evidence governance",
                }
            )

        if (
            reviewed_claim_candidates
            < total_claim_candidates
        ):
            actions.append(
                {
                    "id": "ACT-LEGAL-REVIEW",
                    "priority": "High",
                    "title": (
                        "Obtain professional claim review"
                    ),
                    "description": (
                        f"{total_claim_candidates - reviewed_claim_candidates} "
                        f"technical claim candidates remain "
                        f"without professional legal review."
                    ),
                    "source": "Claim governance",
                }
            )

        if (
            assessed_coverage_records
            < total_coverage_records
        ):
            actions.append(
                {
                    "id": "ACT-COVERAGE-ASSESSMENT",
                    "priority": "High",
                    "title": (
                        "Assess provisional filing coverage"
                    ),
                    "description": (
                        "Store the filed provisional "
                        "specification in the governed evidence "
                        "repository and compare it against all "
                        "mapped innovations."
                    ),
                    "source": "Coverage governance",
                }
            )

        priority_order = {
            "High": 0,
            "Medium": 1,
            "Low": 2,
        }

        return sorted(
            actions,
            key=lambda action: (
                priority_order.get(
                    action["priority"],
                    99,
                ),
                action["id"],
            ),
        )


def build_patent_dashboard_view(
    *,
    include_sensitive: bool = False,
) -> dict[str, Any]:
    return PatentDashboardService().build_view(
        include_sensitive=include_sensitive
    )