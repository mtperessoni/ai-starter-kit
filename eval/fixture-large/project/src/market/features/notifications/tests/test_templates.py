"""Tests for templates (NTF-01 to NTF-04): subjects."""
import pytest

from market.features.notifications.templates import TEMPLATES, render_subject, required_fields, template_names
from market.infra.errors import ValidationError


def test_there_are_five_templates():
    assert sorted(TEMPLATES) == ["low_stock", "order_cancelled", "order_confirmation",
                                 "payment_failed", "return_completed"]


def test_a_subject_is_filled_from_the_context():
    assert render_subject("order_confirmation", order_id="ORD-0001") == "Order ORD-0001 confirmed"
    assert render_subject("low_stock", sku="EL-200", available=3) == "Low stock: EL-200 has 3 left"


def test_an_unknown_template_is_invalid():
    with pytest.raises(ValidationError):
        render_subject("welcome", order_id="ORD-0001")


def test_a_missing_context_value_is_invalid():
    with pytest.raises(ValidationError, match="return_id"):
        render_subject("return_completed", order_id="ORD-0001")


def test_template_names_are_sorted():
    assert template_names() == tuple(sorted(TEMPLATES))


def test_required_fields_follow_the_subject():
    assert required_fields("low_stock") == ("sku", "available")
    assert required_fields("order_confirmation") == ("order_id",)
    with pytest.raises(ValidationError):
        required_fields("welcome")
