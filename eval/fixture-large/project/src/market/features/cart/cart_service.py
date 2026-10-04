"""CRT-01, CRT-02, CRT-03, CRT-04, CRT-05, CRT-07, CAT-05: cart lines."""
from market.features.cart.cart_expiry import is_expired
from market.features.catalog.product_store import require_sellable
from market.features.inventory.stock_store import available
from market.infra import clock, config, ids
from market.infra.customers import get_customer
from market.infra.errors import NotFoundError, OutOfStockError, PolicyError, ValidationError
from market.infra.models import Cart, CartLine
from market.infra.repositories import repo

_CARTS = "carts"


def create_cart(customer_id: str) -> Cart:
    get_customer(customer_id)
    cart = Cart(ids.next_id("CRT"), customer_id, [], [], clock.now())
    repo(_CARTS).add(cart.cart_id, cart)
    return cart


def get_cart(cart_id: str) -> Cart:
    return repo(_CARTS).get(cart_id)


def editable_cart(cart_id: str) -> Cart:
    """The cart, only if it is open and not expired (CRT-07)."""
    cart = get_cart(cart_id)
    if cart.status != "open":
        raise PolicyError("cart_not_open")
    if is_expired(cart):
        raise PolicyError("cart_expired")
    return cart


def _find_line(cart: Cart, sku: str) -> CartLine | None:
    return next((line for line in cart.lines if line.sku == sku), None)


def _check_quantity(cart: Cart, sku: str, new_qty: int, is_new_line: bool) -> None:
    if new_qty < 1 or new_qty > config.get("cart.max_qty"):
        raise ValidationError(f"quantity must be 1 to {config.get('cart.max_qty')}")
    if is_new_line and len(cart.lines) >= config.get("cart.max_lines"):
        raise ValidationError(f"a cart has at most {config.get('cart.max_lines')} different SKUs")
    if new_qty > available(sku):
        raise OutOfStockError(f"not enough stock for {sku}", (sku,))


def _touch(cart: Cart) -> Cart:
    cart.updated_at = clock.now()
    return cart


def add_item(cart_id: str, sku: str, qty: int = 1) -> Cart:
    cart = editable_cart(cart_id)
    if qty < 1:
        raise ValidationError("quantity must be at least 1")
    require_sellable(sku)
    line = _find_line(cart, sku)
    _check_quantity(cart, sku, (line.qty if line else 0) + qty, line is None)
    if line is None:
        cart.lines.append(CartLine(sku, qty))
    else:
        line.qty += qty
    return _touch(cart)


def set_quantity(cart_id: str, sku: str, qty: int) -> Cart:
    cart = editable_cart(cart_id)
    line = _find_line(cart, sku)
    if qty == 0:
        if line is not None:
            cart.lines.remove(line)
        return _touch(cart)
    require_sellable(sku)
    _check_quantity(cart, sku, qty, line is None)
    if line is None:
        cart.lines.append(CartLine(sku, qty))
    else:
        line.qty = qty
    return _touch(cart)


def remove_item(cart_id: str, sku: str) -> Cart:
    cart = editable_cart(cart_id)
    line = _find_line(cart, sku)
    if line is None:
        raise NotFoundError(f"{sku} is not in the cart")
    cart.lines.remove(line)
    return _touch(cart)


def clear_cart(cart_id: str) -> Cart:
    cart = editable_cart(cart_id)
    cart.lines.clear()
    cart.coupon_codes.clear()
    return _touch(cart)


def mark_converted(cart_id: str) -> Cart:
    cart = get_cart(cart_id)
    cart.status = "converted"
    return cart
