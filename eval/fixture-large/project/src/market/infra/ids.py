"""Per-prefix id counters, ORD-0001 style, reset with the rest of the state."""

_counters: dict[str, int] = {}


def next_id(prefix: str) -> str:
    _counters[prefix] = _counters.get(prefix, 0) + 1
    return f"{prefix}-{_counters[prefix]:04d}"


def reset() -> None:
    _counters.clear()
