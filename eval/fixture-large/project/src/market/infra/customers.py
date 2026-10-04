"""Customer store used by SHP-03, TAX-01, TAX-02, LOY-02."""
from market.infra.errors import ValidationError
from market.infra.models import Customer
from market.infra.repositories import repo

TIERS = ("standard", "vip")


def add_customer(customer: Customer) -> Customer:
    if not customer.customer_id.strip() or "@" not in customer.email:
        raise ValidationError("customer needs an id and an email")
    if customer.tier not in TIERS:
        raise ValidationError(f"unknown tier {customer.tier}")
    repo("customers").add(customer.customer_id, customer)
    return customer


def get_customer(customer_id: str) -> Customer:
    return repo("customers").get(customer_id)
