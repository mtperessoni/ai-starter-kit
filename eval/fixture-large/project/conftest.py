"""Autouse reset of every in-memory state before and after each test (SPEC 8)."""
import pytest

from market.infra import repositories


@pytest.fixture(autouse=True)
def _reset_state():
    repositories.reset_all()
    yield
    repositories.reset_all()
