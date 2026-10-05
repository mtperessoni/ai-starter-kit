"""NTF-01 to NTF-04: subject templates of every email the market sends."""
from string import Formatter

from market.infra.errors import ValidationError

TEMPLATES: dict[str, str] = {
    "order_confirmation": "Order {order_id} confirmed",
    "payment_failed": "Payment failed for order {order_id}",
    "order_cancelled": "Order {order_id} cancelled",
    "return_completed": "Return {return_id} completed",
    "low_stock": "Low stock: {sku} has {available} left",
}


def render_subject(template: str, **context) -> str:
    """Fill a template with its context values.

        render_subject("order_confirmation", order_id="ORD-0001") -> "Order ORD-0001 confirmed"

    An unknown template or a missing context key is a ValidationError.
    """
    if template not in TEMPLATES:
        raise ValidationError(f"unknown notification template {template}")
    try:
        return TEMPLATES[template].format(**context)
    except KeyError as missing:
        raise ValidationError(f"template {template} needs {missing.args[0]}") from missing


def template_names() -> tuple[str, ...]:
    """Template names in alphabetical order."""
    return tuple(sorted(TEMPLATES))


def required_fields(template: str) -> tuple[str, ...]:
    """Context keys a template needs, in the order they appear in its subject."""
    if template not in TEMPLATES:
        raise ValidationError(f"unknown notification template {template}")
    fields = [name for _, name, _, _ in Formatter().parse(TEMPLATES[template]) if name]
    return tuple(dict.fromkeys(fields))
