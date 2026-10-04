"""CRT-07: a cart untouched for the configured days is expired."""
from datetime import timedelta

from market.infra import clock, config
from market.infra.models import Cart
from market.infra.repositories import repo


def is_expired(cart: Cart) -> bool:
    return clock.now() - cart.updated_at >= timedelta(days=config.get("cart.ttl_days"))


def purge_expired() -> int:
    stale = [c for c in repo("carts").all() if c.status == "open" and is_expired(c)]
    for cart in stale:
        repo("carts").delete(cart.cart_id)
    return len(stale)
