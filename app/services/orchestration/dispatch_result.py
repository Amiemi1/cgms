"""
CGMS Enterprise Event Bus
Dispatch Result Model

Release:
    v1.75 - Enterprise Event Bus
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone


@dataclass(frozen=True, slots=True)
class DispatchResult:
    event_id: str
    event_name: str
    subscriber_count: int
    successful_subscribers: list[str] = field(default_factory=list)
    failed_subscribers: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    started_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    completed_at: datetime | None = None
    duration_ms: float | None = None
    correlation_id: str | None = None
    event_version: int = 1

    @property
    def success(self) -> bool:
        return not self.failed_subscribers

    @property
    def success_count(self) -> int:
        return len(self.successful_subscribers)

    @property
    def failure_count(self) -> int:
        return len(self.failed_subscribers)

    def to_dict(self) -> dict:
        return {
            "event_id": self.event_id,
            "event_name": self.event_name,
            "event_version": self.event_version,
            "subscriber_count": self.subscriber_count,
            "successful_subscribers": self.successful_subscribers,
            "failed_subscribers": self.failed_subscribers,
            "success_count": self.success_count,
            "failure_count": self.failure_count,
            "errors": self.errors,
            "success": self.success,
            "started_at": self.started_at.isoformat(),
            "completed_at": self.completed_at.isoformat()
            if self.completed_at
            else None,
            "duration_ms": self.duration_ms,
            "correlation_id": self.correlation_id,
        }