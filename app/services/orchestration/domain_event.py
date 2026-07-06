"""
CGMS Enterprise Event Bus
Canonical Domain Event Model

Release:
    v1.75 - Enterprise Event Bus

Purpose:
    Defines the immutable event contract used throughout CGMS.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4


@dataclass(frozen=True, slots=True)
class DomainEvent:
    """
    Canonical CGMS domain event.

    Every event published within CGMS must conform to this model.

    The model is intentionally infrastructure-agnostic so it can
    later be transported through Kafka, RabbitMQ, Redis Streams,
    Azure Service Bus, or other messaging technologies.
    """

    event_name: str

    payload: dict[str, Any]

    source: str

    event_version: int = 1

    event_id: str = field(default_factory=lambda: str(uuid4()))

    occurred_at: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc)
    )

    workspace_id: str | None = None

    actor_id: str | None = None

    correlation_id: str | None = None

    causation_id: str | None = None

    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """
        Serialize the event into a transport-safe dictionary.
        """

        return {
            "event_id": self.event_id,
            "event_name": self.event_name,
            "event_version": self.event_version,
            "occurred_at": self.occurred_at.isoformat(),
            "source": self.source,
            "workspace_id": self.workspace_id,
            "actor_id": self.actor_id,
            "correlation_id": self.correlation_id,
            "causation_id": self.causation_id,
            "payload": self.payload,
            "metadata": self.metadata,
        }

    @property
    def bounded_context(self) -> str:
        """
        Returns the bounded context.

        Example:
            memory.created -> memory
        """

        return self.event_name.split(".", maxsplit=1)[0]

    @property
    def action(self) -> str:
        """
        Returns the event action.

        Example:
            memory.created -> created
        """

        return self.event_name.split(".", maxsplit=1)[1]