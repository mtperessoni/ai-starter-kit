"""SHP-01, SHP-06: delivery zones, base fees and delivery days by region."""
from decimal import Decimal

ZONE_BY_REGION: dict[str, int] = {"SP": 1, "RJ": 2, "MG": 2, "ES": 2}
DEFAULT_ZONE = 3

BASE_FEE: dict[int, Decimal] = {
    1: Decimal("10.00"),
    2: Decimal("18.00"),
    3: Decimal("30.00"),
}

STANDARD_DAYS: dict[int, int] = {1: 3, 2: 5, 3: 8}
EXPRESS_DAYS: dict[int, int] = {1: 1, 2: 2, 3: 4}


def zone_for(region: str | None) -> int:
    """Zone of a delivery region: 1 for SP, 2 for RJ, MG and ES, 3 for every other region.

    A missing region (no address and no customer region) falls in the farthest zone.

        >>> zone_for("SP"), zone_for("MG"), zone_for("AM"), zone_for(None)
        (1, 2, 3, 3)

    Region codes are matched after trimming and upper-casing, so " sp " is SP.
    """
    if region is None:
        return DEFAULT_ZONE
    return ZONE_BY_REGION.get(region.strip().upper(), DEFAULT_ZONE)


def base_fee(zone: int) -> Decimal:
    """Standard fee of a zone before the weight surcharge (SHP-01)."""
    if zone not in BASE_FEE:
        raise KeyError(f"unknown shipping zone {zone}")
    return BASE_FEE[zone]


def delivery_days(zone: int, method: str) -> int:
    """Delivery days by zone: 3, 5, 8 for standard and 1, 2, 4 for express (SHP-06)."""
    table = EXPRESS_DAYS if method == "express" else STANDARD_DAYS
    if zone not in table:
        raise KeyError(f"unknown shipping zone {zone}")
    return table[zone]


def regions_in_zone(zone: int) -> tuple[str, ...]:
    """Listed regions of a zone, sorted. Zone 3 has no list: it is every other region."""
    return tuple(sorted(region for region, z in ZONE_BY_REGION.items() if z == zone))


def zone_summary() -> list[str]:
    """One line per zone for documentation and support screens.

        zone 1: SP, 10.00, standard 3 days, express 1 day
    """
    rows = []
    for zone in sorted(BASE_FEE):
        regions = ", ".join(regions_in_zone(zone)) or "other regions"
        express = EXPRESS_DAYS[zone]
        rows.append(f"zone {zone}: {regions}, {BASE_FEE[zone]}, standard {STANDARD_DAYS[zone]} days, "
                    f"express {express} day{'s' if express != 1 else ''}")
    return rows
