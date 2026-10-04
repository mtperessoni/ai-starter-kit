"""Hidden tests for L3: stock alerts (ALR-01 to ALR-05).

Only the public API is used.
"""
import pytest

from market import api


def _setup():
    api.reset()
    api.seed_demo()
    api.set_stock("EL-200", 0)


def _sold_out_skus(count):
    skus = []
    for i in range(count):
        sku = f"SO-{i + 1:02d}"
        api.add_product(sku, f"Sold out {i + 1}", "toys", "10.00", 100)
        api.set_stock(sku, 0)
        skus.append(sku)
    return skus


def test_subscribe_on_sold_out_sku_returns_waiting_alert():
    """ALR-01: a sold-out SKU accepts an alert that is not notified."""
    _setup()
    a = api.subscribe_stock_alert("C-REG", "EL-200")
    assert a.customer_id == "C-REG"
    assert a.sku == "EL-200"
    assert a.notified is False
    assert api.list_stock_alerts("C-REG") == [a]


def test_subscribe_on_in_stock_sku_is_refused():
    """ALR-01: a SKU with stock raises PolicyError."""
    _setup()
    with pytest.raises(api.PolicyError):
        api.subscribe_stock_alert("C-REG", "BK-100")


def test_asking_twice_returns_the_same_alert():
    """ALR-02: the second request returns the first alert."""
    _setup()
    first = api.subscribe_stock_alert("C-REG", "EL-200")
    second = api.subscribe_stock_alert("C-REG", "EL-200")
    assert second.alert_id == first.alert_id
    assert len(api.list_stock_alerts("C-REG")) == 1


def test_eleventh_waiting_alert_is_refused():
    """ALR-03: 10 waiting alerts are allowed, the 11th raises PolicyError."""
    _setup()
    skus = _sold_out_skus(11)
    for sku in skus[:10]:
        api.subscribe_stock_alert("C-REG", sku)
    with pytest.raises(api.PolicyError):
        api.subscribe_stock_alert("C-REG", skus[10])


def test_notified_alerts_do_not_count_toward_the_limit():
    """ALR-03, ALR-04: after one alert is notified the customer may add another."""
    _setup()
    skus = _sold_out_skus(11)
    for sku in skus[:10]:
        api.subscribe_stock_alert("C-REG", sku)
    api.restock(skus[0], 3)
    assert api.subscribe_stock_alert("C-REG", skus[10]).notified is False


def test_restock_notifies_waiting_alert_and_sends_email():
    """ALR-04: restocking a sold-out SKU marks the alert and sends back_in_stock once."""
    _setup()
    api.subscribe_stock_alert("C-REG", "EL-200")
    api.restock("EL-200", 3)
    sent = api.sent_notifications(template="back_in_stock")
    assert len(sent) == 1
    assert sent[0].recipient == "reg@example.com"
    assert api.list_stock_alerts("C-REG")[0].notified is True


def test_every_waiting_customer_is_notified():
    """ALR-04: two customers waiting on the same SKU both get the email."""
    _setup()
    api.subscribe_stock_alert("C-REG", "EL-200")
    api.subscribe_stock_alert("C-VIP", "EL-200")
    api.restock("EL-200", 3)
    recipients = sorted(n.recipient for n in api.sent_notifications(template="back_in_stock"))
    assert recipients == ["reg@example.com", "vip@example.com"]


def test_second_restock_sends_nothing_new():
    """ALR-05: a notified alert is not sent again when stock is added again."""
    _setup()
    api.subscribe_stock_alert("C-REG", "EL-200")
    api.restock("EL-200", 3)
    api.restock("EL-200", 3)
    assert len(api.sent_notifications(template="back_in_stock")) == 1


def test_new_request_after_notification_creates_new_alert():
    """ALR-05: after being notified and sold out again, asking creates a new waiting alert."""
    _setup()
    first = api.subscribe_stock_alert("C-REG", "EL-200")
    api.restock("EL-200", 3)
    api.set_stock("EL-200", 0)
    second = api.subscribe_stock_alert("C-REG", "EL-200")
    assert second.alert_id != first.alert_id
    assert second.notified is False


def test_subscribing_after_restock_is_refused():
    """ALR-01: once the SKU has stock again the request raises PolicyError."""
    _setup()
    api.restock("EL-200", 3)
    with pytest.raises(api.PolicyError):
        api.subscribe_stock_alert("C-REG", "EL-200")
