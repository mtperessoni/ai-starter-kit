"""Autouse world for the returns tests: no loyalty port inside a test, the wired one restored after."""
import pytest

from market.features.checkout import ports
from market.features.returns.tests.helpers import setup_world


@pytest.fixture(autouse=True)
def world():
    wired = ports.get_loyalty_port()
    ports.set_loyalty_port(None)
    setup_world()
    yield
    ports.set_loyalty_port(wired)
