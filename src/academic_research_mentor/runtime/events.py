from __future__ import annotations

import queue
import threading
from dataclasses import dataclass
from typing import Any, Dict, Iterable, Optional


@dataclass
class RuntimeEvent:
    """Simple container holding an emitted runtime event."""

    type: str
    payload: Dict[str, Any]


class _EventSubscriber:
    __slots__ = ("queue", "filters", "active")

    def __init__(self, filters: Optional[Iterable[str]] = None) -> None:
        self.queue: "queue.Queue[RuntimeEvent]" = queue.Queue()
        self.filters = set(filters) if filters else None
        self.active = True

    def matches(self, event_type: str) -> bool:
        if not self.filters:
            return True
        return event_type in self.filters


class EventPublisher:
    """Thread-safe pub/sub for runtime UI and tool events."""

    def __init__(self) -> None:
        self._subscribers: list[_EventSubscriber] = []
        self._lock = threading.Lock()

    def subscribe(self, filters: Optional[Iterable[str]] = None) -> "EventSubscription":
        subscriber = _EventSubscriber(filters)
        with self._lock:
            self._subscribers.append(subscriber)
        return EventSubscription(self, subscriber)

    def unsubscribe(self, subscriber: _EventSubscriber) -> None:
        with self._lock:
            subscriber.active = False
            self._subscribers = [s for s in self._subscribers if s is not subscriber]

    def emit(self, event_type: str, payload: Dict[str, Any]) -> None:
        event = RuntimeEvent(event_type, payload)
        with self._lock:
            subscribers_snapshot = list(self._subscribers)
        for subscriber in subscribers_snapshot:
            if not subscriber.active or not subscriber.matches(event_type):
                continue
            try:
                subscriber.queue.put_nowait(event)
            except queue.Full:
                # Drop events silently for slow subscribers; UI is best-effort
                continue


class EventSubscription:
    """Handle for reading events from the publisher."""

    def __init__(self, publisher: EventPublisher, subscriber: _EventSubscriber) -> None:
        self._publisher = publisher
        self._subscriber = subscriber
        self._closed = False

    @property
    def queue(self) -> "queue.Queue[RuntimeEvent]":
        return self._subscriber.queue

    def close(self) -> None:
        if not self._closed:
            self._publisher.unsubscribe(self._subscriber)
            self._closed = True


_EVENT_BUS = EventPublisher()


def emit_event(event_type: str, payload: Dict[str, Any]) -> None:
    """Emit an event on the global runtime event bus."""

    _EVENT_BUS.emit(event_type, payload)


def subscribe_events(filters: Optional[Iterable[str]] = None) -> EventSubscription:
    """Subscribe to runtime events.

    Returns an EventSubscription with a thread-safe queue for polling.
    """

    return _EVENT_BUS.subscribe(filters)


__all__ = ["RuntimeEvent", "EventPublisher", "EventSubscription", "emit_event", "subscribe_events"]
