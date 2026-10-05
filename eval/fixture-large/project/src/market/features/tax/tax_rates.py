"""TAX-01: tax rate by delivery region."""
from decimal import Decimal

RATES: dict[str, Decimal] = {
    "SP": Decimal("8"),
    "RJ": Decimal("10"),
    "MG": Decimal("9"),
}
DEFAULT_RATE = Decimal("7")


def rate_for(region: str | None) -> Decimal:
    """Tax rate in percent for a delivery region.

    The caller passes the delivery address region, or the customer's region when the order has no
    address (TAX-01).

        >>> rate_for("SP"), rate_for("RJ"), rate_for("MG"), rate_for("AM"), rate_for(None)
        (Decimal('8'), Decimal('10'), Decimal('9'), Decimal('7'), Decimal('7'))
    """
    if region is None:
        return DEFAULT_RATE
    return RATES.get(region.strip().upper(), DEFAULT_RATE)


def known_regions() -> tuple[str, ...]:
    """Regions with their own rate, sorted; every other region pays the default rate."""
    return tuple(sorted(RATES))


def rate_label(region: str | None) -> str:
    """Readable rate for receipts, such as "8% (SP)" or "7% (default)"."""
    rate = rate_for(region)
    shown = f"{rate.normalize():f}"
    if region is not None and region.strip().upper() in RATES:
        return f"{shown}% ({region.strip().upper()})"
    return f"{shown}% (default)"
