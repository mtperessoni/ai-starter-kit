"""Loyalty feature: points ledger, earning, redemption and event handlers (LOY-01 to LOY-06)."""
from market.features.loyalty.loyalty_events import register
from market.features.loyalty.points_ledger import add_points, balance
from market.features.loyalty.points_redemption import LoyaltyRedemptionPort

register()

__all__ = ["LoyaltyRedemptionPort", "add_points", "balance", "register"]
