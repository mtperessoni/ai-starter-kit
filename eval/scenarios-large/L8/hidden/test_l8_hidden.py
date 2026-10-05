"""Hidden tests for L8: the first paid order earns double points (LOY-07).

Only the public API is used.
"""
from market import api

ADDR = api.Address("BR", "SP", "01000-000")
OK = api.PaymentRequest("card", "ok_1")
DECLINE = api.PaymentRequest("card", "decline_1")


def _setup():
    api.reset()
    api.seed_demo()


def _order(customer, payment=OK, sku="EL-200", coupon=None):
    cart = api.create_cart(customer)
    api.add_to_cart(cart, sku, 1)
    if coupon:
        api.apply_coupon(cart, coupon)
    return api.place_order(cart, payment, ADDR)


def test_first_order_earns_double():
    """LOY-07, LOY-01: 120.00 of merchandise earns 120 normally, 240 on the first order."""
    _setup()
    assert _order("C-REG").status == "paid"
    assert api.points_balance("C-REG") == 240


def test_second_order_earns_normal_points():
    """LOY-07: the second paid order earns 120, so the balance is 360."""
    _setup()
    _order("C-REG")
    _order("C-REG")
    assert api.points_balance("C-REG") == 360


def test_vip_first_order_earns_four_times():
    """LOY-07, LOY-02: VIP doubles 120 to 240, the first order doubles it again to 480."""
    _setup()
    _order("C-VIP")
    assert api.points_balance("C-VIP") == 480


def test_failed_payment_is_not_a_first_order():
    """LOY-07: a declined order earns nothing and the next paid order still gets the bonus."""
    _setup()
    failed = _order("C-REG", DECLINE)
    assert failed.status == "payment_failed"
    assert api.points_balance("C-REG") == 0
    assert _order("C-REG").status == "paid"
    assert api.points_balance("C-REG") == 240


def test_bonus_applies_to_points_after_coupon():
    """LOY-07, LOY-01: SAVE10 leaves 108.00, normal earning 108, first order 216."""
    _setup()
    _order("C-REG", coupon="SAVE10")
    assert api.points_balance("C-REG") == 216


def test_granted_points_do_not_count_as_first_order():
    """LOY-07, LOY-05: a grant is not an order, so the first paid order still earns double."""
    _setup()
    api.grant_points("C-REG", 1000)
    _order("C-REG")
    assert api.points_balance("C-REG") == 1240
