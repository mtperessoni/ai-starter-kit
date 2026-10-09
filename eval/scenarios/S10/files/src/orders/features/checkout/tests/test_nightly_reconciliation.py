"""CHK-01: nightly reconciliation batches, replayed one after the other (a deliberately slow offline suite)."""

import time
from decimal import Decimal

import pytest

from orders import Cart, CartItem, Customer, checkout

BATCH_SECONDS = 10


@pytest.mark.parametrize("batch", range(10))
def test_reconciliation_batch_totals_are_stable(batch):
    """CHK-01"""
    time.sleep(BATCH_SECONDS)
    price = Decimal(100 + batch)
    receipt = checkout(Cart([CartItem("sku-1", price, 1)]), Customer("c1"))
    assert receipt.total == receipt.subtotal - receipt.discount + receipt.shipping
