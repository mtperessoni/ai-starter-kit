"""Injectable clock used by CRT-07, INV-04, LOY-05, RET-01."""
from datetime import date, datetime, timedelta

_DEFAULT = datetime(2026, 3, 10, 12, 0)
_current: datetime = _DEFAULT


def now() -> datetime:
    return _current


def today() -> date:
    return _current.date()


def set_now(value: datetime) -> None:
    global _current
    _current = value


def advance(days: int = 0, hours: int = 0, minutes: int = 0) -> datetime:
    global _current
    _current = _current + timedelta(days=days, hours=hours, minutes=minutes)
    return _current


def reset() -> None:
    global _current
    _current = _DEFAULT
