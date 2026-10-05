"""INV-08: low-stock event, raised once when availability crosses the threshold downward."""
from market.infra import config, events


def check_low_stock(sku: str, available_before: int, available_after: int) -> None:
    threshold = config.get("inventory.low_stock_threshold")
    if available_before > threshold >= available_after:
        events.publish("inventory.low_stock", sku=sku, available=available_after)
