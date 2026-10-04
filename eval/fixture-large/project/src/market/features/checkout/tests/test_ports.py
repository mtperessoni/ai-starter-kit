"""Tests for ports (CHK-03, CHK-04): the null port and wiring a real one."""
from decimal import Decimal

import pytest

from market.features.checkout.ports import get_loyalty_port, set_loyalty_port
from market.infra.errors import PolicyError


class FixedPort:
    def redemption_value(self, customer_id, points, merchandise_total):
        return Decimal("7.00")


def test_null_port_allows_zero_points():
    assert get_loyalty_port().redemption_value("C-REG", 0, Decimal("100.00")) == Decimal("0.00")


def test_null_port_refuses_any_points():
    with pytest.raises(PolicyError) as error:
        get_loyalty_port().redemption_value("C-REG", 500, Decimal("100.00"))
    assert error.value.reason == "loyalty_unavailable"


def test_a_wired_port_is_used():
    port = FixedPort()
    set_loyalty_port(port)
    assert get_loyalty_port() is port


def test_none_restores_the_null_port():
    set_loyalty_port(FixedPort())
    set_loyalty_port(None)
    with pytest.raises(PolicyError):
        get_loyalty_port().redemption_value("C-REG", 100, Decimal("100.00"))
