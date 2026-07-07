"""
CGMS Enterprise Event Bus
Event Registry

Release:
    v1.75 - Enterprise Event Bus

Purpose:
    Maintains the mapping between canonical event names and their subscribers.

Design Rule:
    The registry does not publish events.
    The registry does not execute subscribers.
    The registry does not know business logic.
"""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import Final

from app.services.orchestration.domain_event import DomainEvent


EventSubscriber = Callable[[DomainEvent], None | Awaitable[None]]


class EventRegistry:
    """
    Registry of event subscribers.

    This class is intentionally small and infrastructure-independent.
    It maps event names to subscriber callables and provides safe
    registration and lookup operations.
    """

    def __init__(self) -> None:
        self._subscribers: dict[str, list[EventSubscriber]] = {}

    def subscribe(
        self,
        event_name: str,
        subscriber: EventSubscriber,
    ) -> None:
        """
        Register a subscriber for an event name.

        Duplicate subscriber registration for the same event is ignored.
        """

        self._validate_event_name(event_name)

        if event_name not in self._subscribers:
            self._subscribers[event_name] = []

        if subscriber not in self._subscribers[event_name]:
            self._subscribers[event_name].append(subscriber)

    def unsubscribe(
        self,
        event_name: str,
        subscriber: EventSubscriber,
    ) -> None:
        """
        Remove a subscriber from an event name.

        Missing event names or subscribers are ignored to keep the method
        safe for cleanup operations.
        """

        self._validate_event_name(event_name)

        if event_name not in self._subscribers:
            return

        if subscriber in self._subscribers[event_name]:
            self._subscribers[event_name].remove(subscriber)

        if not self._subscribers[event_name]:
            del self._subscribers[event_name]

    def get_subscribers(
        self,
        event_name: str,
    ) -> list[EventSubscriber]:
        """
        Return subscribers registered for an event name.

        A copy is returned to prevent external mutation of registry state.
        """

        self._validate_event_name(event_name)

        return list(self._subscribers.get(event_name, []))

    def clear(self) -> None:
        """
        Remove all registered subscribers.
        """

        self._subscribers.clear()

    def count(
        self,
        event_name: str | None = None,
    ) -> int:
        """
        Count subscribers.

        If event_name is provided, count subscribers for that event only.
        Otherwise, count all registered subscribers.
        """

        if event_name is not None:
            self._validate_event_name(event_name)
            return len(self._subscribers.get(event_name, []))

        return sum(len(subscribers) for subscribers in self._subscribers.values())

    def registered_events(self) -> list[str]:
        """
        Return all event names that currently have subscribers.
        """

        return sorted(self._subscribers.keys())

    @staticmethod
    def _validate_event_name(event_name: str) -> None:
        """
        Validate canonical CGMS event name format.
        """

        if not event_name or not event_name.strip():
            raise ValueError("Event name cannot be empty.")

        if "." not in event_name:
            raise ValueError(
                f"Invalid event name '{event_name}'. "
                "Expected format: '<bounded_context>.<action>'."
            )

    async def publish(
        self,
        event_name: str,
        payload: dict | None = None,
    ):
        """
        Legacy compatibility publisher.

        TODO(v1.76):
        Remove this method after legacy orchestration code migrates to
        EnterpriseEventBus.publish(DomainEvent).
        """

        from app.services.orchestration.domain_event import DomainEvent
        from app.services.orchestration.event_bus import EnterpriseEventBus

        event = DomainEvent(
            event_name=event_name,
            source="legacy.event_registry",
            payload=payload or {},
        )

        bus = EnterpriseEventBus(self)

        return await bus.publish(event)


DEFAULT_EVENT_REGISTRY: Final[EventRegistry] = EventRegistry()

# Backward-compatible alias for legacy orchestration handlers.
# TODO(v1.76): migrate legacy imports to DEFAULT_EVENT_REGISTRY.
event_registry = DEFAULT_EVENT_REGISTRY