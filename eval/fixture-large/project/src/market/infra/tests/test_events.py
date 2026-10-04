"""Tests for infra.events (SPEC 2.9: INV-08 and the peripheral listeners)."""
from market.infra import events


def test_publish_calls_handlers_in_subscribe_order():
    seen = []
    events.subscribe("t.one", lambda e: seen.append(("a", e.payload["x"])))
    events.subscribe("t.one", lambda e: seen.append(("b", e.payload["x"])))
    events.publish("t.one", x=1)
    assert seen == [("a", 1), ("b", 1)]


def test_same_handler_twice_is_ignored():
    seen = []

    def handler(event):
        seen.append(event.name)

    events.subscribe("t.two", handler)
    events.subscribe("t.two", handler)
    events.publish("t.two")
    assert seen == ["t.two"]


def test_history_filters_by_name_and_stores_time():
    events.publish("t.a", n=1)
    events.publish("t.b", n=2)
    assert [e.name for e in events.history()] == ["t.a", "t.b"]
    assert events.history("t.b")[0].payload == {"n": 2}
    assert events.history("t.a")[0].at.year == 2026
