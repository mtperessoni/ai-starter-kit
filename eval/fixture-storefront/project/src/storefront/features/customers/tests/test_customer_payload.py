"""CUS-01, CUS-02, CUS-03: customer payload."""

import pytest

from storefront.features.customers import CustomerRecord, build_customer_payload


def test_payload_has_only_id_and_vip():
    """CUS-01"""
    assert build_customer_payload(CustomerRecord("c1", "Ana Souza")) == {"id": "c1", "vip": False}


def test_vip_record_gives_a_vip_payload():
    """CUS-02"""
    assert build_customer_payload(CustomerRecord("c1", "Ana Souza", vip=True))["vip"] is True


def test_empty_id_is_refused():
    """CUS-03"""
    with pytest.raises(ValueError):
        build_customer_payload(CustomerRecord("", "Ana Souza"))
