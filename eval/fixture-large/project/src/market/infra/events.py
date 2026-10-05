"""Synchronous event bus (SPEC 2.9; INV-08, NTF-01 to NTF-04)."""
from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime

from market.infra import clock


@dataclass(frozen=True)
class Event:
    name: str
    payload: dict
    at: datetime


_handlers: dict[str, list[Callable[[Event], None]]] = {}
_history: list[Event] = []


def subscribe(name: str, handler: Callable[[Event], None]) -> None:
    registered = _handlers.setdefault(name, [])
    if handler not in registered:
        registered.append(handler)


def publish(name: str, **payload) -> Event:
    event = Event(name, dict(payload), clock.now())
    _history.append(event)
    for handler in list(_handlers.get(name, [])):
        handler(event)
    return event


def history(name: str | None = None) -> list[Event]:
    return [e for e in _history if name is None or e.name == name]


def reset_history() -> None:
    _history.clear()
