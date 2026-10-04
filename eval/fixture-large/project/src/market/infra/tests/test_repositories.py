"""Tests for infra.repositories (state reset and CRUD used by every feature)."""
import pytest

from market.infra import clock, config, events, ids
from market.infra.errors import NotFoundError, ValidationError
from market.infra.repositories import repo, reset_all


def test_add_get_find_all():
    items = repo("t_items")
    items.add("a", 1)
    assert items.get("a") == 1
    assert items.find("zz") is None
    assert items.all() == [1]


def test_duplicate_add_raises_validation_error():
    items = repo("t_dup")
    items.add("a", 1)
    with pytest.raises(ValidationError):
        items.add("a", 2)


def test_get_missing_raises_not_found():
    with pytest.raises(NotFoundError):
        repo("t_missing").get("nope")


def test_save_overwrites_and_delete_removes():
    items = repo("t_save")
    items.save("a", 1)
    items.save("a", 2)
    assert items.get("a") == 2
    items.delete("a")
    assert items.find("a") is None


def test_reset_all_clears_repos_ids_config_clock_and_history():
    repo("t_reset").save("a", 1)
    ids.next_id("ORD")
    config.set("cart.max_qty", 3)
    clock.advance(days=3)
    events.publish("t.reset")
    reset_all()
    assert repo("t_reset").all() == []
    assert ids.next_id("ORD") == "ORD-0001"
    assert config.get("cart.max_qty") == 99
    assert clock.now().day == 10
    assert events.history() == []
