"""CUS-01, CUS-02, CUS-03: the payload the orders service receives for a customer."""

from dataclasses import dataclass


@dataclass(frozen=True)
class CustomerRecord:
    id: str
    full_name: str
    vip: bool = False


def build_customer_payload(record: CustomerRecord) -> dict:
    if not record.id:
        raise ValueError("customer id is required")
    return {"id": record.id, "vip": bool(record.vip)}
