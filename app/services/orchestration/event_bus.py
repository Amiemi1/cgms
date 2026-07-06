"""
CGMS Enterprise Event Bus

Release:
    v1.75 - Enterprise Event Bus
"""

from __future__ import annotations

import inspect
import time
from datetime import datetime, timezone

from app.services.orchestration.dispatch_result import DispatchResult
from app.services.orchestration.domain_event import DomainEvent
from app.services.orchestration.event_registry import (
    DEFAULT_EVENT_REGISTRY,
    EventRegistry,
)


class EnterpriseEventBus:
    """
    In-process Enterprise Event Bus.

    Responsible for publishing DomainEvent instances to registered subscribers.
    """

    def __init__(self, registry: EventRegistry | None = None) -> None:
        self.registry = registry or DEFAULT_EVENT_REGISTRY

    async def publish(self, event: DomainEvent) -> DispatchResult:
        started_at = datetime.now(timezone.utc)
        started_perf = time.perf_counter()

        subscribers = self.registry.get_subscribers(event.event_name)

        successful: list[str] = []
        failed: list[str] = []
        errors: list[str] = []

        for subscriber in subscribers:
            name = getattr(subscriber, "__name__", subscriber.__class__.__name__)

            try:
                result = subscriber(event)

                if inspect.isawaitable(result):
                    await result

                successful.append(name)

            except Exception as exc:
                failed.append(name)
                errors.append(f"{name}: {exc}")

        completed_at = datetime.now(timezone.utc)
        duration_ms = round((time.perf_counter() - started_perf) * 1000, 3)

        return DispatchResult(
            event_id=event.event_id,
            event_name=event.event_name,
            event_version=event.event_version,
            subscriber_count=len(subscribers),
            successful_subscribers=successful,
            failed_subscribers=failed,
            errors=errors,
            started_at=started_at,
            completed_at=completed_at,
            duration_ms=duration_ms,
            correlation_id=event.correlation_id,
        )


DEFAULT_EVENT_BUS = EnterpriseEventBus()