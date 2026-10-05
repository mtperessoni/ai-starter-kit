# Large fixture: the single design (LG01)

Everything for `eval/fixture-large/project/`, `eval/scenarios-large/L1..L8` and `eval/arms-large.json` is written from this file. If code, docs or scenarios disagree with it, SPEC.md wins. Stdlib only, Python 3.11+, pytest. English everywhere, no em dash.

Conventions used below: paths are relative to `project/src/market/` unless they start with `project/`. "Group A" = catalog, pricing, promotions, inventory, cart, infra. "Group B" = checkout, payments, shipping, tax, loyalty, returns, notifications, `api.py`, `market/__init__.py`. Every `features/<f>/` and `infra/` has an `__init__.py` of at most 10 lines (re-export of the entry symbols only, no logic, except `loyalty/__init__.py` and `notifications/__init__.py`, which call `register()` once at import).

## 1. Domain overview

A marketplace order service. Customers (standard or vip) browse a catalog, fill a cart, apply coupons, check out (shipping, tax, optional loyalty redemption), pay by card, pix or gift card, and may cancel or return. Everything is in memory, synchronous and deterministic (clock and ids are injectable).

| Topic | Decision |
|---|---|
| Money | `decimal.Decimal` always, never float. Build from strings (`Decimal("12.50")`). Output money has exactly 2 decimals |
| Rounding | `infra.money.q2(x)`: ROUND_HALF_UP to cents. Applied ONLY where a rule below says so: volume break (PRC-03), each promotion stage total (PRM-02, 07, 08, 09, 10), allocation (PRC-04), tax per line and on shipping (TAX-03, TAX-04), express fee (SHP-05), installment interest and installment amount (PAY-02), refund proration (RET-03), average rating to 1 decimal (REV-04, scenario L2). Never elsewhere |
| Time | `infra.clock.now()`; tests move it with `set_now`/`advance`. Demo clock is `2026-03-10 12:00:00` |
| Ids | `infra.ids.next_id(prefix)` gives `ORD-0001`, `PAY-0001`, `RSV-0001`, `RET-0001`, `NTF-0001`, `CRT-0001`, `REV-0001`, `ALR-0001` (4 digits, per-prefix counter, reset by `reset_all`) |
| Errors | `MarketError` (code str) with `NotFoundError` "not_found", `ValidationError` "invalid", `OutOfStockError` "out_of_stock" (attr `skus: tuple[str, ...]`), `PolicyError` "policy" (attr `reason: str`) |
| State | `infra.repositories.repo(name)` in-memory repositories; `reset_all()` clears repos, ids, config overrides, clock and event history (subscribers stay) |
| Regions | Brazilian state codes as plain strings (`SP`, `RJ`, `MG`, `ES`, `AM`, ...) |

Seed data (`api.seed_demo()`), the only data hidden tests may assume:

| Kind | Content |
|---|---|
| Clock | `2026-03-10 12:00:00` |
| Products (sku, name, category, price, weight g) | BK-100 Python Basics books 40.00 400; BK-200 Data Patterns books 60.00 600; EL-100 USB Cable electronics 15.00 100; EL-200 Headphones electronics 120.00 300; FS-100 T-Shirt fashion 25.00 200; GR-100 Coffee 500g grocery 12.50 500; HM-100 Desk Lamp home 80.00 1500; TY-100 Puzzle toys 30.00 700; GC-050 Gift Card 50 gift_card 50.00 0 |
| Stock on hand | 100 each except EL-200 = 5; GC-050 untracked (INV-07) |
| Customers (id, email, tier, region) | C-REG reg@example.com standard SP; C-VIP vip@example.com vip SP; C-RJ rj@example.com standard RJ; C-AM am@example.com standard AM |
| Coupons | SAVE10 percent 10, min 50.00; SAVE20 percent 20, min 100.00, per customer limit 1, expires 2026-12-31; FIX15 fixed 15.00, min 80.00; FREESHIP free_shipping, min 30.00 |
| Category sale | SALE-TOYS toys 20 percent, 2026-03-01 to 2026-03-31 |
| BOGO | BOGO-TSHIRT sku FS-100, buy 2 get 1 free |
| Bundle | BUNDLE-READER skus BK-100 + BK-200, amount off 15.00 per set |
| Gift card | GIFT-100 balance 100.00 |

## 2. Module map

### 2.1 Tiers and allowed imports

Core = catalog, pricing, promotions, inventory, cart, checkout, payments, shipping, tax. Peripheral = loyalty, returns, notifications. Core never imports peripheral; peripheral listens to core through events (2.9). Checkout reaches loyalty only through the port in `checkout/ports.py` that `api.py` wires at import. A feature imports another only through that feature's package modules named in the table (never its tests). No cycles.

| Feature | May import (besides `infra`) |
|---|---|
| catalog | none |
| promotions | none |
| pricing | catalog, promotions |
| inventory | catalog |
| cart | catalog, inventory, pricing, promotions |
| shipping | pricing (models only), catalog (`category_rules`) |
| tax | pricing (models only), catalog (`category_rules`) |
| payments | none |
| checkout | cart, catalog, pricing, promotions, inventory, payments, shipping, tax |
| loyalty | none (events only) |
| returns | checkout (`order_models`, `order_lifecycle`), payments, inventory, catalog (`category_rules`) |
| notifications | none (events and `infra.customers` only) |
| api.py | everything |

### 2.2 infra (group A) `infra/`

| File | Responsibility | Entry symbols | Lines |
|---|---|---|---|
| errors.py | Exceptions | `class MarketError(Exception)` with `code: str`; `NotFoundError`, `ValidationError`, `OutOfStockError(message, skus: tuple[str, ...] = ())`, `PolicyError(reason: str)` (message = reason) | 30 |
| money.py | Decimal helpers | `D(value: str \| int \| Decimal) -> Decimal` (via `str`); `q2(value: Decimal) -> Decimal`; `pct(amount: Decimal, percent: Decimal) -> Decimal` (amount*percent/100, unrounded); `allocate(amount: Decimal, weights: Sequence[Decimal]) -> list[Decimal]` (proportional, each q2, remainder to the last weight greater than 0, sums exactly to `amount`; all weights zero gives zeros) | 30 |
| clock.py | Injectable clock | `now() -> datetime`, `today() -> date`, `set_now(value: datetime) -> None`, `advance(days: int = 0, hours: int = 0, minutes: int = 0) -> datetime`, `reset() -> None` (default `datetime(2026, 3, 10, 12, 0)`) | 50 |
| config.py | Tunable numbers | `DEFAULTS: dict[str, object]` (2.10), `get(key: str)`, `set(key: str, value: object) -> None`, `reset() -> None`; unknown key raises `KeyError` | 70 |
| events.py | Event bus | `@dataclass(frozen=True) Event(name: str, payload: dict, at: datetime)`; `subscribe(name: str, handler: Callable[[Event], None]) -> None` (same handler twice ignored); `publish(name: str, **payload) -> Event` (stores in history, calls handlers in subscribe order); `history(name: str \| None = None) -> list[Event]`; `reset_history() -> None` | 60 |
| repositories.py | In-memory repos | `class InMemoryRepository`: `add(key, obj)` (duplicate raises `ValidationError`), `get(key)` (raises `NotFoundError`), `find(key) -> obj \| None`, `save(key, obj)`, `delete(key)`, `all() -> list`, `clear()`; `repo(name: str) -> InMemoryRepository` (created on demand); `reset_all() -> None` | 90 |
| ids.py | Id counters | `next_id(prefix: str) -> str`; `reset() -> None` | 20 |
| models.py | Shared dataclasses | see 2.2.1 | 70 |
| customers.py | Customer store | `add_customer(customer: Customer) -> Customer`; `get_customer(customer_id: str) -> Customer` | 30 |

#### 2.2.1 `infra/models.py` (all frozen=False dataclasses)

| Class | Fields |
|---|---|
| `Product` | `sku: str`, `name: str`, `category: str`, `price: Decimal`, `weight_grams: int`, `active: bool = True`, `taxable_class: str = "standard"` ("standard" or "exempt") |
| `Customer` | `customer_id: str`, `email: str`, `tier: str = "standard"` ("standard" or "vip"), `region: str = "SP"`, `tax_exempt: bool = False` |
| `CartLine` | `sku: str`, `qty: int` |
| `Cart` | `cart_id: str`, `customer_id: str`, `lines: list[CartLine]`, `coupon_codes: list[str]`, `updated_at: datetime`, `status: str = "open"` ("open" or "converted") |
| `Address` | `country: str = "BR"`, `region: str = "SP"`, `postal_code: str = ""` |

### 2.3 catalog (group A) `features/catalog/`

| File | Responsibility | Entry symbols | Lines |
|---|---|---|---|
| category_rules.py | Category facts | `CATEGORIES: tuple[str, ...] = ("books","electronics","fashion","grocery","home","toys","gift_card")`; `EXEMPT_CATEGORIES = ("books","grocery","gift_card")`; `is_digital(category: str) -> bool` (gift_card); `is_returnable(category: str) -> bool` (not gift_card, not grocery); `is_stock_tracked(category: str) -> bool` (not gift_card) | 40 |
| product_validation.py | Validation | `validate_product(product: Product) -> None`; `validate_price_change(old: Decimal, new: Decimal) -> None`; `taxable_class_for(category: str) -> str` | 80 |
| product_store.py | Persistence and lookup | `add_product(product: Product) -> Product` (validates, sets `taxable_class`); `get_product(sku: str) -> Product`; `find_product(sku: str) -> Product \| None`; `list_products() -> list[Product]`; `require_sellable(sku: str) -> Product`; `deactivate_product(sku: str) -> Product`; `update_price(sku: str, new_price: Decimal) -> Product` | 110 |
| catalog_search.py | Search | `search_products(query: str = "", category: str \| None = None, max_price: Decimal \| None = None, sort: str = "name") -> list[Product]` (`sort` in name, price_asc, price_desc) | 70 |

### 2.4 pricing (group A) `features/pricing/`

| File | Responsibility | Entry symbols | Lines |
|---|---|---|---|
| quote_models.py | Quote dataclasses | `LineQuote(sku: str, category: str, qty: int, unit_price: Decimal, line_subtotal: Decimal, line_discount: Decimal, line_total: Decimal, taxable_class: str, weight_grams: int)`; `PriceQuote(lines: tuple[LineQuote, ...], subtotal: Decimal, discounts: tuple[AppliedDiscount, ...], discount_total: Decimal, total: Decimal, free_shipping: bool, rejected_coupons: tuple[tuple[str, str], ...])` (`AppliedDiscount` from `promotions.promotion_models`) | 50 |
| volume_breaks.py | Quantity breaks | `volume_percent(qty: int) -> Decimal`; `volume_discount(unit_price: Decimal, qty: int) -> Decimal` (q2 of line subtotal times percent) | 50 |
| discount_allocation.py | Aggregation | `line_discount_map(discounts: Sequence[AppliedDiscount]) -> dict[str, Decimal]` (sum of `line_amounts` per sku) | 50 |
| price_calculator.py | The quote | `line_subtotal(unit_price: Decimal, qty: int) -> Decimal`; `quote_lines(lines: Sequence[CartLine], customer: Customer, coupon_codes: Sequence[str], today: date \| None = None) -> PriceQuote` | 150 |

### 2.5 promotions (group A) `features/promotions/`

| File | Responsibility | Entry symbols | Lines |
|---|---|---|---|
| promotion_models.py | Dataclasses | `Coupon(code: str, kind: str, value: Decimal, min_subtotal: Decimal = Decimal("0"), starts_on: date \| None = None, expires_on: date \| None = None, per_customer_limit: int \| None = None, global_limit: int \| None = None, categories: tuple[str, ...] = ())` (`kind` in percent, fixed, free_shipping; `value` is percent, amount, or 0); `CategorySale(sale_id: str, category: str, percent: Decimal, starts_on: date, ends_on: date)`; `BogoRule(rule_id: str, sku: str, buy: int = 2, free: int = 1)`; `Bundle(bundle_id: str, skus: tuple[str, ...], amount_off: Decimal)`; `PromoLine(sku: str, category: str, qty: int, unit_price: Decimal, value: Decimal)` (`value` = running value after volume break); `AppliedDiscount(code: str, kind: str, amount: Decimal, line_amounts: tuple[tuple[str, Decimal], ...])` (kinds: volume, category_sale, bogo, percent_coupon, bundle, fixed_coupon); `PromoResult(discounts: tuple[AppliedDiscount, ...], total: Decimal, free_shipping: bool, rejected: tuple[tuple[str, str], ...], applied_codes: tuple[str, ...])` | 90 |
| coupon_store.py | Definitions | `add_coupon(coupon: Coupon) -> Coupon` (code normalized, duplicates rejected, percent in 0 to 100 exclusive of 0); `get_coupon(code: str) -> Coupon` (NotFoundError); `find_coupon(code: str) -> Coupon \| None`; `add_category_sale(sale: CategorySale) -> CategorySale`; `add_bogo(rule: BogoRule) -> BogoRule`; `add_bundle(bundle: Bundle) -> Bundle`; `active_sales(today: date) -> list[CategorySale]`; `bogo_rules() -> list[BogoRule]`; `bundles() -> list[Bundle]`; `normalize_code(code: str) -> str` (strip, upper) | 120 |
| promotion_usage.py | Use accounting | `hold_uses(order_id: str, customer_id: str, codes: Sequence[str]) -> None`; `commit_uses(order_id: str) -> None`; `release_uses(order_id: str) -> None` (idempotent); `usage_count(code: str, customer_id: str \| None = None) -> int` (held + committed uses, for that customer if given) | 80 |
| coupon_validation.py | Checks | `check_coupon(code: str, eligible_subtotal: Decimal, customer_id: str, today: date) -> str \| None`; reasons `unknown`, `not_started`, `expired`, `below_minimum`, `limit_reached`, `customer_limit_reached` (checked in this order) | 80 |
| promotion_engine.py | The big file | section 3; entry `evaluate(lines: Sequence[PromoLine], customer: Customer, codes: Sequence[str], today: date) -> PromoResult`; `explain(result: PromoResult) -> list[str]` | 700 |

### 2.6 inventory (group A) `features/inventory/`

| File | Responsibility | Entry symbols | Lines |
|---|---|---|---|
| stock_store.py | Stock levels | `set_on_hand(sku: str, qty: int) -> None`; `add_stock(sku: str, qty: int) -> int` (returns new on hand; publishes `inventory.restocked` when available goes from 0 to above 0); `on_hand(sku: str) -> int`; `reserved(sku: str) -> int` (sum of active reservations); `available(sku: str) -> int` (untracked categories return `10**9`) | 110 |
| reservations.py | Holds | `Reservation(reservation_id: str, order_id: str, lines: tuple[tuple[str, int], ...], status: str, expires_at: datetime)` (status active, released, committed, expired); `reserve(order_id: str, lines: Sequence[tuple[str, int]]) -> Reservation`; `release(reservation_id: str) -> Reservation`; `commit(reservation_id: str) -> Reservation`; `expire_due() -> int` (count expired); `get_reservation(reservation_id: str) -> Reservation` | 170 |
| low_stock.py | Threshold events | `check_low_stock(sku: str, available_before: int, available_after: int) -> None` (publishes `inventory.low_stock`) | 50 |

### 2.7 cart (group A) `features/cart/`

| File | Responsibility | Entry symbols | Lines |
|---|---|---|---|
| cart_service.py | Lines | `create_cart(customer_id: str) -> Cart`; `get_cart(cart_id: str) -> Cart`; `add_item(cart_id: str, sku: str, qty: int = 1) -> Cart`; `set_quantity(cart_id: str, sku: str, qty: int) -> Cart`; `remove_item(cart_id: str, sku: str) -> Cart`; `clear_cart(cart_id: str) -> Cart`; `mark_converted(cart_id: str) -> Cart` | 140 |
| cart_coupons.py | Coupons on cart | `apply_coupon(cart_id: str, code: str) -> Cart`; `remove_coupon(cart_id: str, code: str) -> Cart` | 60 |
| cart_pricing.py | Quote | `price_cart(cart_id: str) -> PriceQuote` (customer lookup, `pricing.quote_lines`) | 50 |
| cart_expiry.py | Expiry | `is_expired(cart: Cart) -> bool`; `purge_expired() -> int` | 50 |

### 2.8 Group B features

| Feature / file | Responsibility | Entry symbols | Lines |
|---|---|---|---|
| shipping/shipping_zones.py | Zone tables | `ZONE_BY_REGION: dict[str, int]` (SP 1; RJ, MG, ES 2); `zone_for(region: str \| None) -> int` (others 3); `BASE_FEE = {1: Decimal("10.00"), 2: Decimal("18.00"), 3: Decimal("30.00")}`; `STANDARD_DAYS = {1: 3, 2: 5, 3: 8}`; `EXPRESS_DAYS = {1: 1, 2: 2, 3: 4}` | 50 |
| shipping/shipping_rules.py | Rules | `is_digital_only(lines: Sequence[LineQuote]) -> bool`; `total_weight(lines: Sequence[LineQuote]) -> int` (physical lines only); `weight_surcharge(grams: int) -> Decimal`; `free_threshold(tier: str) -> Decimal` | 60 |
| shipping/shipping_fee.py | Quote | `ShippingRequest(region: str \| None, lines: Sequence[LineQuote], merchandise_total: Decimal, customer_tier: str, method: str = "standard", free_shipping_coupon: bool = False)`; `ShippingQuote(fee: Decimal, zone: int, method: str, estimated_days: int, free_reason: str \| None, total_weight_grams: int)` (`free_reason` in digital, threshold, coupon, None); `quote_shipping(request: ShippingRequest) -> ShippingQuote` | 110 |
| tax/tax_rates.py | Rates | `RATES: dict[str, Decimal]` (SP 8, RJ 10, MG 9); `DEFAULT_RATE = Decimal("7")`; `rate_for(region: str \| None) -> Decimal` (percent) | 40 |
| tax/tax_calculator.py | Tax | `TaxResult(total: Decimal, per_line: dict[str, Decimal], shipping_tax: Decimal, rate: Decimal)`; `compute_tax(lines: Sequence[LineQuote], shipping_fee: Decimal, region: str \| None, tax_exempt: bool = False) -> TaxResult` | 90 |
| payments/payment_models.py | Dataclasses | `PaymentRequest(method: str, token: str = "", installments: int = 1, gift_card_code: str \| None = None, idempotency_key: str \| None = None)`; `Payment(payment_id: str, order_id: str, customer_id: str, method: str, amount: Decimal, captured: Decimal, refunded: Decimal, status: str, installments: int, installment_amount: Decimal, gateway_ref: str \| None, decline_code: str \| None, idempotency_key: str \| None, gift_card_code: str \| None)` (status captured, failed, partially_refunded, refunded); `GatewayResult(approved: bool, code: str, reference: str \| None)` | 60 |
| payments/gateway.py | Fake gateway | `authorize(method: str, token: str, amount: Decimal, attempt: int) -> GatewayResult`; token `ok_*` approves ref `GW-<token>`; `decline_*` declines `card_declined`; `fraud_*` declines `suspected_fraud`; `flaky_N` times out (`gateway_timeout`, approved False) for attempts 1..N then approves; `timeout_always` always times out; anything else declines `invalid_token` | 60 |
| payments/installments.py | Card plans | `installment_plan(amount: Decimal, installments: int) -> tuple[Decimal, Decimal]` (total with interest, each) | 50 |
| payments/gift_cards.py | Gift card balances | `issue_gift_card(code: str, balance: Decimal) -> None`; `gift_card_balance(code: str) -> Decimal`; `debit_gift_card(code: str, amount: Decimal) -> None`; `credit_gift_card(code: str, amount: Decimal) -> None` | 70 |
| payments/payment_service.py | Charge and refund | `charge(order_id: str, customer_id: str, amount: Decimal, request: PaymentRequest) -> Payment` (never raises on a decline; raises `ValidationError` for bad method or installments); `refund(payment_id: str, amount: Decimal) -> Payment`; `get_payment(payment_id: str) -> Payment` | 160 |
| checkout/ports.py | Core to peripheral port | `class LoyaltyPort(Protocol)`: `redemption_value(customer_id: str, points: int, merchandise_total: Decimal) -> Decimal`; `set_loyalty_port(port: LoyaltyPort \| None) -> None`; `get_loyalty_port() -> LoyaltyPort` (default null port: 0 points gives `Decimal("0.00")`, more raises `PolicyError("loyalty_unavailable")`) | 40 |
| checkout/order_models.py | Dataclasses | `OrderLine(sku: str, category: str, qty: int, unit_price: Decimal, line_subtotal: Decimal, line_discount: Decimal, line_total: Decimal, tax: Decimal, weight_grams: int)`; `OrderQuote(price: PriceQuote, shipping: ShippingQuote, tax: TaxResult, loyalty_discount: Decimal, points_to_redeem: int, total: Decimal)`; `Order(order_id: str, customer_id: str, lines: tuple[OrderLine, ...], subtotal: Decimal, discount_total: Decimal, shipping: Decimal, tax: Decimal, loyalty_discount: Decimal, total: Decimal, status: str, address: Address \| None, shipping_method: str, coupon_codes: tuple[str, ...], points_redeemed: int, payment_id: str \| None, reservation_id: str \| None, decline_code: str \| None, created_at: datetime, paid_at: datetime \| None, shipped_at: datetime \| None, delivered_at: datetime \| None, returned_units: dict[str, int])`. Status values: pending, paid, payment_failed, cancelled, shipped, delivered, partially_refunded, refunded | 90 |
| checkout/order_validation.py | Pre-checks | `validate_checkout(cart: Cart, address: Address \| None, price: PriceQuote) -> None` | 70 |
| checkout/order_quote.py | Quote | `build_quote(cart: Cart, customer: Customer, address: Address \| None, shipping_method: str, points_to_redeem: int) -> OrderQuote` | 130 |
| checkout/order_placement.py | Place | `place_order(cart_id: str, payment: PaymentRequest, address: Address \| None = None, shipping_method: str = "standard", points_to_redeem: int = 0) -> Order`; private `_rollback(order: Order, reservation_id: str) -> None` | 190 |
| checkout/order_lifecycle.py | Status | `get_order(order_id: str) -> Order`; `cancel_order(order_id: str) -> Order`; `mark_shipped(order_id: str) -> Order`; `mark_delivered(order_id: str) -> Order`; `apply_return(order_id: str, items: Sequence[tuple[str, int]]) -> Order` (updates `returned_units` and status partially_refunded or refunded) | 130 |
| loyalty/points_ledger.py | Lots | `PointsLot(lot_id: str, customer_id: str, points: int, remaining: int, earned_at: datetime)` ; `add_points(customer_id: str, points: int, reason: str) -> None`; `balance(customer_id: str) -> int` (excludes expired); `spend(customer_id: str, points: int) -> None` (FIFO); `claw_back(customer_id: str, points: int) -> int` (returns actually removed, floors at 0); `expire_lots(customer_id: str) -> int` | 120 |
| loyalty/points_earning.py | Earning | `tier_multiplier(tier: str) -> int`; `points_for_order(points_base: Decimal, tier: str) -> int` | 50 |
| loyalty/points_redemption.py | Redemption | `redemption_value(customer_id: str, points: int, merchandise_total: Decimal) -> Decimal`; `class LoyaltyRedemptionPort` implementing the port | 80 |
| loyalty/loyalty_events.py | Handlers | `on_order_paid`, `on_order_cancelled`, `on_return_completed`, `register() -> None` | 70 |
| returns/return_models.py | Dataclasses | `RefundBreakdown(merchandise: Decimal, tax: Decimal, shipping: Decimal, total: Decimal)`; `ReturnRequest(return_id: str, order_id: str, customer_id: str, items: tuple[tuple[str, int], ...], reason: str, status: str, refund: RefundBreakdown, created_at: datetime)` (status completed) | 50 |
| returns/return_policy.py | Eligibility | `REASONS = ("defective","wrong_item","changed_mind","other")`; `check_eligibility(order: Order, items: Sequence[tuple[str, int]], reason: str, today: date) -> None` (raises `ValidationError` or `PolicyError`) | 80 |
| returns/refund_calculator.py | Amounts | `compute_refund(order: Order, items: Sequence[tuple[str, int]], reason: str) -> RefundBreakdown` | 80 |
| returns/return_service.py | Flow | `request_return(order_id: str, items: Sequence[tuple[str, int]], reason: str) -> ReturnRequest`; `get_return(return_id: str) -> ReturnRequest` | 90 |
| notifications/notification_models.py | Dataclass | `Notification(notification_id: str, template: str, recipient: str, order_id: str \| None, subject: str, sent_at: datetime)` | 30 |
| notifications/templates.py | Subjects | `TEMPLATES: dict[str, str]` (order_confirmation, payment_failed, order_cancelled, return_completed, low_stock); `render_subject(template: str, **context) -> str` | 50 |
| notifications/dispatcher.py | Send | `send(template: str, recipient: str, order_id: str \| None = None, **context) -> Notification \| None` (None when suppressed by NTF-05); `list_sent(recipient: str \| None = None, template: str \| None = None) -> list[Notification]` | 70 |
| notifications/notification_events.py | Handlers | `register() -> None` and one handler per event in 2.9 | 50 |
| `api.py` | Facade | section 5 | 300 |
| `__init__.py` (package) | `from market import api` works; exports `__version__ = "0.1.0"` | 15 |

### 2.9 Events (infra.events)

| Event | Publisher | Payload keys | Subscribers |
|---|---|---|---|
| `inventory.low_stock` | inventory | sku, available | notifications |
| `inventory.restocked` | inventory | sku, available | none in the seed (L3 adds one) |
| `payment.captured` | payments | payment_id, order_id, amount | none |
| `payment.failed` | payments | payment_id, order_id, customer_id, code | notifications |
| `payment.refunded` | payments | payment_id, order_id, amount | none |
| `order.paid` | checkout | order_id, customer_id, points_base (Decimal, sum of `line_total` of non-gift-card lines), points_redeemed (int), total | loyalty, notifications |
| `order.cancelled` | checkout | order_id, customer_id, points_base, points_redeemed | loyalty, notifications |
| `return.completed` | returns | return_id, order_id, customer_id, points_base_returned (Decimal, merchandise refunded of non-gift-card lines), refund_total | loyalty, notifications |

### 2.10 Config keys (`infra/config.py::DEFAULTS`)

| Key | Default | Used by |
|---|---|---|
| `catalog.max_price` | `Decimal("100000.00")` | CAT-02 |
| `catalog.max_price_change_percent` | `Decimal("50")` | CAT-06 |
| `pricing.volume_tier1_qty` / `_percent` | `10` / `Decimal("5")` | PRC-03 |
| `pricing.volume_tier2_qty` / `_percent` | `50` / `Decimal("10")` | PRC-03 |
| `promo.max_total_discount_percent` | `Decimal("40")` | PRM-11 |
| `inventory.reservation_minutes` | `30` | INV-04 |
| `inventory.low_stock_threshold` | `5` | INV-08 |
| `cart.max_lines` / `cart.max_qty` / `cart.ttl_days` | `20` / `99` / `7` | CRT-01, 03, 07 |
| `checkout.min_order_total` | `Decimal("10.00")` | CHK-07 |
| `shipping.free_threshold` / `shipping.free_threshold_vip` | `Decimal("200.00")` / `Decimal("100.00")` | SHP-03 |
| `shipping.max_weight_grams` | `30000` | SHP-06 |
| `shipping.express_multiplier` | `Decimal("1.5")` | SHP-05 |
| `shipping.surcharge_per_500g` | `Decimal("3.00")` | SHP-02 |
| `payments.max_attempts` | `3` | PAY-05 |
| `payments.max_installments` / `payments.min_installment` | `6` / `Decimal("10.00")` | PAY-02 |
| `payments.interest_percent_per_extra_installment` | `Decimal("1.99")` | PAY-02 |
| `loyalty.redeem_min_points` / `loyalty.redeem_step` | `500` / `100` | LOY-04 |
| `loyalty.max_redeem_percent` | `Decimal("50")` | LOY-04 |
| `loyalty.expiry_days` | `365` | LOY-05 |
| `loyalty.vip_multiplier` | `2` | LOY-02 |
| `returns.window_days` | `30` | RET-01 |

Rules whose "Change via" is `config` read the key above; the PRD row names the key.

### 2.11 Placement sequence of `place_order` (the contract of CHK-02, CHK-06)

1. Load cart (open, not expired, non-empty) and customer. 2. `build_quote`: price (`cart_pricing`) then loyalty redemption (port) then shipping then tax, in the order of CHK-04 (see L1 for the changed order). 3. `validate_checkout` (address, minimum, rejected coupons). 4. `inventory.reserve(order_id, lines)`. 5. `promotion_usage.hold_uses`. 6. Create the `Order` with status `pending` and snapshot prices. 7. `payments.charge`. 8a. Captured: `inventory.commit`, `promotion_usage.commit_uses`, status `paid`, `paid_at`, cart `converted`, publish `order.paid`. 8b. Failed: `_rollback`, status `payment_failed`, `decline_code` set. Each placement gets a new order id; the cart stays open after a decline.

Correct `_rollback` body: `inventory.release(reservation_id)` then `promotion_usage.release_uses(order.order_id)`. `cancel_order` does the same releases plus refund, restock and `order.cancelled`.

## 3. The big file: `promotions/promotion_engine.py` (about 700 lines)

Pure functions over a `_Context`; no repository writes. Listed in `eval/fixture-large/project/repo.md` and the ratchet allowlist as a big file. Flows must read it by symbol.

| Lines | Section | Symbols |
|---|---|---|
| 1-35 | Module docstring (cites PRM-02 to PRM-13), imports | none |
| 36-80 | Constants | `ELIGIBLE_EXCLUDED_CATEGORIES = ("gift_card",)`, `KIND_PERCENT`, `KIND_FIXED`, `KIND_FREE_SHIPPING`, reason constants |
| 81-150 | Context | `@dataclass class _Context`: `lines: list[PromoLine]`, `values: dict[str, Decimal]` (running value per sku), `customer`, `codes`, `today`, `discounts: list[AppliedDiscount]`, `rejected: list[tuple[str, str]]`, `applied_codes: list[str]`, `coupons: dict[str, Coupon]` (by kind), `free_shipping: bool`, `eligible_list_subtotal: Decimal`, `spent: Decimal` (engine discount so far) ; `_new_context(...)` |
| 151-250 | Helpers | `_eligible(ctx) -> list[PromoLine]` (PRM-12), `_list_subtotal(lines) -> Decimal`, `_headroom(ctx) -> Decimal` (PRM-11: `q2(eligible_list_subtotal * cap_percent / 100) - spent`, never below 0), `_trim(ctx, amount) -> Decimal`, `_take(ctx, code, kind, amount, weights: list[tuple[str, Decimal]]) -> None` (allocates with `money.allocate`, lowers `values`, adds `spent`, appends `AppliedDiscount`) |
| 251-340 | Coupon intake | `_resolve_coupons(ctx) -> None` (PRM-01, 03, 04, 06, 13: normalizes, `check_coupon`, first valid per kind wins, others rejected `kind_already_applied`, unknown rejected `unknown`) |
| 341-400 | `stage_category_sales(ctx)` | PRM-07 |
| 401-460 | `stage_bogo(ctx)` | PRM-08 |
| 461-530 | `stage_percent_coupons(ctx)` | PRM-02 |
| 531-590 | `stage_bundles(ctx)` | PRM-09 |
| 591-630 | `stage_fixed_coupons(ctx)` | PRM-10 |
| 631-650 | `stage_free_shipping(ctx)` | PRM-13 |
| 651-680 | Pipeline | `PIPELINE: tuple[Callable[[_Context], None], ...]` and `evaluate(...)` (PRM-05) |
| 681-700 | `explain(result) -> list[str]` | one line per discount: `"<code> <kind> -<amount>"` |

Correct `PIPELINE` order (PRM-05): `stage_category_sales, stage_bogo, stage_percent_coupons, stage_bundles, stage_fixed_coupons, stage_free_shipping`. `evaluate` calls `_resolve_coupons` once, then each stage in `PIPELINE` order, then returns `PromoResult` with `total = sum of amounts`. The padding to 700 lines must be real code (docstrings with worked examples per stage, input validation, defensive branches), not blank lines.

## 4. Rule catalog (89 rules)

Source is `<feature>/<file>.py::<symbol>` under `src/market/features/` (infra under `src/market/infra/`). X marks a cross-feature rule (38 of them, with the features in play). Change via is `code` or `config` (key in 2.10).

### 4.1 CAT (catalog), 7 rules

| ID | Rule | Source | Change via | X |
|---|---|---|---|---|
| CAT-01 | A SKU has 3 to 20 characters: uppercase letters, digits and hyphen. A product name has 1 to 80 characters after trimming | catalog/product_validation.py::validate_product | code | |
| CAT-02 | A price is above 0.00, has at most 2 decimals and is at most 100000.00 | catalog/product_validation.py::validate_product | config | |
| CAT-03 | A category is one of books, electronics, fashion, grocery, home, toys, gift_card. Weight is 1 to 30000 g, except gift cards, which weigh 0. Books, grocery and gift cards are tax exempt, all others standard | catalog/product_validation.py::validate_product | code | X catalog, tax |
| CAT-04 | A SKU already in the catalog cannot be added again | catalog/product_store.py::add_product | code | |
| CAT-05 | A deactivated product cannot be put in a cart or bought, and it stays visible in past orders | catalog/product_store.py::require_sellable | code | X catalog, cart, checkout |
| CAT-06 | One price update may not change a price by more than 50% | catalog/product_validation.py::validate_price_change | config | |
| CAT-07 | Search matches names or SKUs containing the text, ignoring case, only active products, sorted by name (or by price up or down), optional category and maximum price | catalog/catalog_search.py::search_products | code | |

### 4.2 PRC (pricing), 6 rules

| ID | Rule | Source | Change via | X |
|---|---|---|---|---|
| PRC-01 | A line subtotal is the current catalog price times the quantity; the cart subtotal is the sum of line subtotals. A cart line never stores a price, and an order keeps the prices it was placed with | pricing/price_calculator.py::quote_lines | code | X catalog, cart, checkout |
| PRC-02 | An empty cart quotes zero everywhere. The total is the subtotal minus all discounts and never goes below 0.00 | pricing/price_calculator.py::quote_lines | code | |
| PRC-03 | Volume break per line, before any promotion: 10 or more units of one SKU get 5% off that line, 50 or more get 10% (rounded half up to cents) | pricing/volume_breaks.py::volume_discount | config | |
| PRC-04 | A discount shared by several lines is split in proportion to their value, rounded half up to cents, with the last line taking the remainder so the pieces add up exactly. Tax and refunds use the line total after this split | infra/money.py::allocate | code | X pricing, promotions, tax, returns |
| PRC-05 | Gift cards never get a volume break | pricing/volume_breaks.py::volume_percent | code | X catalog |
| PRC-06 | The quote lists every discount with its code, kind and amount, and the coupons it rejected with the reason | pricing/price_calculator.py::quote_lines | code | |

### 4.3 PRM (promotions), 13 rules

| ID | Rule | Source | Change via | X |
|---|---|---|---|---|
| PRM-01 | Coupon codes ignore case and surrounding spaces. A code that is not found is rejected as `unknown`; a rejected coupon never fails the quote, it is listed with its reason | promotions/coupon_store.py::normalize_code | code | |
| PRM-02 | A percent coupon takes its percent off the current value of the eligible lines (rounded half up to cents once for the coupon), only if the eligible list subtotal reaches its minimum, otherwise `below_minimum`. A coupon may be limited to some categories | promotions/promotion_engine.py::stage_percent_coupons | code | |
| PRM-03 | A coupon is valid from its start date to its expiry date, both days included | promotions/coupon_validation.py::check_coupon | code | |
| PRM-04 | A coupon has an optional limit per customer and an optional global limit. A use is held when the order is placed, counts for good when the payment is captured, and is given back when the payment fails or the order is cancelled | promotions/promotion_usage.py::hold_uses | code | X promotions, checkout, cart |
| PRM-05 | Discounts apply in this order: category sale, buy-x-get-y, percent coupon, bundle, fixed coupon, free-shipping flag. Each step works on what the previous steps left | promotions/promotion_engine.py::PIPELINE | code | |
| PRM-06 | At most one coupon of each kind (percent, fixed, free shipping) applies to an order; the first one in the cart wins, the others are rejected as `kind_already_applied` | promotions/promotion_engine.py::_resolve_coupons | code | |
| PRM-07 | A category sale takes its percent off every eligible line of its category from its start date to its end date, both days included | promotions/promotion_engine.py::stage_category_sales | code | |
| PRM-08 | Buy 2 get 1 free: for every 3 units of the rule's SKU one unit is free, valued at that line's current value per unit (rounded half up to cents) | promotions/promotion_engine.py::stage_bogo | code | |
| PRM-09 | A bundle gives its fixed amount off for every complete set of its SKUs in the cart (sets = the smallest quantity among its SKUs), never more than the current value of the bundle lines | promotions/promotion_engine.py::stage_bundles | code | |
| PRM-10 | A fixed coupon takes its amount off the current total of the eligible lines, only if the minimum is reached, never more than that total | promotions/promotion_engine.py::stage_fixed_coupons | code | |
| PRM-11 | All promotion discounts together never exceed 40% of the eligible list subtotal; a step that would pass the limit is cut to what is left | promotions/promotion_engine.py::_headroom | config | |
| PRM-12 | Gift cards are never discounted by any promotion and do not count toward coupon minimums | promotions/promotion_engine.py::_eligible | code | X catalog, promotions |
| PRM-13 | A free-shipping coupon follows the same validity checks and gives no money discount; it only sets the free-shipping flag the checkout passes to shipping | promotions/promotion_engine.py::stage_free_shipping | code | X promotions, shipping |

### 4.4 INV (inventory), 8 rules

| ID | Rule | Source | Change via | X |
|---|---|---|---|---|
| INV-01 | Stock on hand is never negative | inventory/stock_store.py::set_on_hand | code | |
| INV-02 | Available stock is the stock on hand minus the quantities held by active reservations | inventory/stock_store.py::available | code | |
| INV-03 | A reservation is all or nothing: if any line is short, nothing is held and the error names every short SKU | inventory/reservations.py::reserve | code | |
| INV-04 | A reservation holds stock for 30 minutes; after that it expires and the stock is available again | inventory/reservations.py::expire_due | config | |
| INV-05 | Releasing an active reservation gives its stock back; releasing it again changes nothing | inventory/reservations.py::release | code | |
| INV-06 | Committing an active reservation removes the quantities from stock on hand and ends the hold; a released or expired reservation cannot be committed | inventory/reservations.py::commit | code | |
| INV-07 | Gift cards are not stock-tracked: always available, never reserved | inventory/stock_store.py::available | code | X catalog, inventory |
| INV-08 | When available stock falls to 5 or below from above 5, a low-stock event is raised once; when a SKU with nothing available gets stock, a restocked event is raised | inventory/low_stock.py::check_low_stock | config | X inventory, notifications |

### 4.5 CRT (cart), 7 rules

| ID | Rule | Source | Change via | X |
|---|---|---|---|---|
| CRT-01 | A line has 1 to 99 units; setting a quantity of 0 removes the line | cart/cart_service.py::set_quantity | config | |
| CRT-02 | Adding a SKU already in the cart adds to its quantity (the total still stays within 99) | cart/cart_service.py::add_item | code | |
| CRT-03 | A cart has at most 20 different SKUs | cart/cart_service.py::add_item | config | |
| CRT-04 | Only known and active products can be added | cart/cart_service.py::add_item | code | X catalog, cart |
| CRT-05 | A quantity above the available stock cannot be added | cart/cart_service.py::add_item | code | X inventory, cart |
| CRT-06 | A coupon can be put on a cart only if it is valid for that cart right now; otherwise the reason is returned as an error. Reapplying the same code changes nothing | cart/cart_coupons.py::apply_coupon | code | X promotions, cart |
| CRT-07 | A cart untouched for 7 days is expired and cannot be changed or bought | cart/cart_expiry.py::is_expired | config | |

### 4.6 CHK (checkout), 10 rules

| ID | Rule | Source | Change via | X |
|---|---|---|---|---|
| CHK-01 | An order is placed only from an open, unexpired cart with at least one line whose products are all still sellable | checkout/order_placement.py::place_order | code | X cart, catalog |
| CHK-02 | Placing an order runs in this order: quote, validate, reserve stock, hold coupon uses, create the order, charge, then commit or roll back | checkout/order_placement.py::place_order | code | X cart, pricing, promotions, inventory, payments |
| CHK-03 | Order total = merchandise after discounts + shipping + tax - loyalty discount, never below 0.00 | checkout/order_quote.py::build_quote | code | X pricing, shipping, tax, loyalty |
| CHK-04 | Loyalty points are redeemed after tax: the loyalty discount reduces the amount to pay, not the tax base | checkout/order_quote.py::build_quote | code | X checkout, loyalty, tax |
| CHK-05 | An order with any physical item needs an address; a gift-card-only order does not | checkout/order_validation.py::validate_checkout | code | X checkout, shipping, catalog |
| CHK-06 | When a payment fails, the stock hold is released and the coupon uses are given back; the order becomes payment_failed and the cart stays open for another try | checkout/order_placement.py::_rollback | code | X checkout, payments, inventory, promotions |
| CHK-07 | Merchandise after discounts must be at least 10.00 | checkout/order_validation.py::validate_checkout | config | |
| CHK-08 | An order moves pending, then paid or payment_failed; paid, then shipped, then delivered; a delivered order becomes partially_refunded or refunded through returns | checkout/order_lifecycle.py::mark_shipped | code | |
| CHK-09 | Only a paid order (not yet shipped) can be cancelled: full refund of what was captured, stock back, coupon uses given back, points earned reversed and redeemed points returned | checkout/order_lifecycle.py::cancel_order | code | X checkout, payments, inventory, promotions, loyalty |
| CHK-10 | An order is not placed if a coupon on the cart is no longer valid; the customer gets the reason | checkout/order_validation.py::validate_checkout | code | X checkout, promotions |

### 4.7 PAY (payments), 8 rules

| ID | Rule | Source | Change via | X |
|---|---|---|---|---|
| PAY-01 | Accepted methods are card, pix and gift card; any other method is rejected | payments/payment_service.py::charge | code | |
| PAY-02 | Card can be paid in 1 to 6 installments with 1.99% interest per extra installment (rounded half up to cents), each installment at least 10.00; pix and gift card are 1 installment | payments/installments.py::installment_plan | config | |
| PAY-03 | A declined payment records the decline code, is never captured, and raises a payment-failed event | payments/payment_service.py::charge | code | |
| PAY-04 | A payment that times out at the gateway is tried again, up to 3 attempts in all; if every attempt times out it is declined as `gateway_timeout` | payments/payment_service.py::charge | config | |
| PAY-05 | Paying with a gift card takes the amount from its balance; not enough balance declines as `insufficient_balance`, an unknown code as `unknown_gift_card` | payments/payment_service.py::charge | code | |
| PAY-06 | The same idempotency key returns the first payment and never charges twice | payments/payment_service.py::charge | code | |
| PAY-07 | The sum of refunds of a payment never exceeds what was captured; refunds of a gift-card payment go back to the card balance | payments/payment_service.py::refund | code | |
| PAY-08 | Interest on installments is not refunded; a refund returns at most the order amount | payments/payment_service.py::refund | code | |

### 4.8 SHP (shipping), 6 rules

| ID | Rule | Source | Change via | X |
|---|---|---|---|---|
| SHP-01 | Standard shipping starts at 10.00 to SP, 18.00 to RJ, MG and ES, and 30.00 to any other region | shipping/shipping_zones.py::zone_for | code | |
| SHP-02 | The first 1000 g are included; each further started 500 g adds 3.00 | shipping/shipping_rules.py::weight_surcharge | config | |
| SHP-03 | Standard shipping is free when merchandise after discounts is 200.00 or more, 100.00 or more for VIP customers | shipping/shipping_rules.py::free_threshold | config | X shipping, pricing, customers |
| SHP-04 | An order of only gift cards has no shipping: fee 0.00, no delivery days | shipping/shipping_rules.py::is_digital_only | code | X catalog, shipping, checkout |
| SHP-05 | Express costs 1.5 times the standard fee before any waiver (rounded half up to cents) and is never free; it is not offered for gift-card-only orders | shipping/shipping_fee.py::quote_shipping | config | |
| SHP-06 | Delivery takes 3, 5 or 8 days (standard) and 1, 2 or 4 (express) by zone; an order over 30000 g of physical goods is refused | shipping/shipping_fee.py::quote_shipping | config | X shipping, promotions (coupon waiver) |

SHP-06 also states: a free-shipping coupon waives the standard fee (free reason `coupon`); threshold and coupon waivers apply to standard only.

### 4.9 TAX (tax), 5 rules

| ID | Rule | Source | Change via | X |
|---|---|---|---|---|
| TAX-01 | The tax rate follows the delivery region: 8% SP, 10% RJ, 9% MG, 7% elsewhere; without an address the customer's region is used | tax/tax_rates.py::rate_for | code | |
| TAX-02 | Exempt products (books, grocery, gift cards) pay no tax; a tax-exempt customer pays none at all | tax/tax_calculator.py::compute_tax | code | X catalog, tax |
| TAX-03 | Tax per line is the rate on the line total after discounts, rounded half up to cents, then summed | tax/tax_calculator.py::compute_tax | code | X pricing, promotions, tax |
| TAX-04 | Shipping is taxed at the same rate (rounded half up to cents); free shipping has no tax | tax/tax_calculator.py::compute_tax | code | |
| TAX-05 | Tax is added on top of the price, never included in it | tax/tax_calculator.py::compute_tax | code | |

### 4.10 LOY (loyalty), 7 rules (one planned)

| ID | Rule | Source | Change via | X |
|---|---|---|---|---|
| LOY-01 | A customer earns 1 point for each whole 1.00 of merchandise after discounts, when the order is paid; shipping and tax earn nothing | loyalty/points_earning.py::points_for_order | code | X checkout, loyalty |
| LOY-02 | VIP customers earn double | loyalty/points_earning.py::tier_multiplier | config | |
| LOY-03 | Gift cards earn no points | loyalty/loyalty_events.py::on_order_paid | code | X catalog, loyalty |
| LOY-04 | Points can be redeemed in multiples of 100 (100 points = 1.00), at least 500 at a time, up to the balance and up to 50% of the merchandise after discounts | loyalty/points_redemption.py::redemption_value | config | X checkout, loyalty |
| LOY-05 | Points expire 365 days after they were earned; the oldest are spent first | loyalty/points_ledger.py::expire_lots | config | |
| LOY-06 | A cancelled order or a return takes back the points it earned (never below a zero balance); a cancelled order gives back the points redeemed on it | loyalty/loyalty_events.py::on_order_cancelled | code | X loyalty, checkout, returns |
| LOY-07 | The first paid order of a customer earns double the points it would normally earn (approved, not yet built) | planned | code | |

### 4.11 RET (returns), 7 rules

| ID | Rule | Source | Change via | X |
|---|---|---|---|---|
| RET-01 | A return must start within 30 days after delivery, on a delivered or partially refunded order | returns/return_policy.py::check_eligibility | config | |
| RET-02 | Gift cards and grocery cannot be returned | returns/return_policy.py::check_eligibility | code | X catalog, returns |
| RET-03 | The refund is the line total after discounts, divided by the line quantity, times the units returned (rounded half up to cents), plus the tax of those units the same way | returns/refund_calculator.py::compute_refund | code | X pricing, tax, returns |
| RET-04 | Shipping is refunded only for reasons `defective` or `wrong_item`, and only when this return brings the returned units to every unit of the order | returns/refund_calculator.py::compute_refund | code | X shipping, returns |
| RET-05 | A customer cannot return more units than bought minus already returned; reasons are defective, wrong_item, changed_mind, other | returns/return_policy.py::check_eligibility | code | |
| RET-06 | Returned goods go back to stock, except when the reason is `defective` | returns/return_service.py::request_return | code | X returns, inventory |
| RET-07 | A completed return refunds the payment, lowers the order status and takes back the points earned on the returned merchandise | returns/return_service.py::request_return | code | X returns, payments, checkout, loyalty |

### 4.12 NTF (notifications), 5 rules

| ID | Rule | Source | Change via | X |
|---|---|---|---|---|
| NTF-01 | A paid order sends the order_confirmation email to the customer | notifications/notification_events.py::on_order_paid | code | X checkout, notifications |
| NTF-02 | A failed payment sends payment_failed to the customer | notifications/notification_events.py::on_payment_failed | code | X payments, notifications |
| NTF-03 | A cancelled order sends order_cancelled; a completed return sends return_completed | notifications/notification_events.py::on_order_cancelled | code | |
| NTF-04 | A low-stock event sends low_stock to ops@market.test | notifications/notification_events.py::on_low_stock | code | X inventory, notifications |
| NTF-05 | The same template for the same order and recipient is sent only once | notifications/dispatcher.py::send | code | |

Counts: CAT 7, PRC 6, PRM 13, INV 8, CRT 7, CHK 10, PAY 8, SHP 6, TAX 5, LOY 7, RET 7, NTF 5 = 89. Cross-feature rows (X): CAT-03, CAT-05, PRC-01, PRC-04, PRC-05, PRM-04, PRM-12, PRM-13, INV-07, INV-08, CRT-04, CRT-05, CRT-06, CHK-01, CHK-02, CHK-03, CHK-04, CHK-05, CHK-06, CHK-09, CHK-10, SHP-03, SHP-04, SHP-06, TAX-02, TAX-03, LOY-01, LOY-03, LOY-04, LOY-06, RET-02, RET-03, RET-04, RET-06, RET-07, NTF-01, NTF-02, NTF-04 (38; the PRD marks them in the Rule text or a "Spans" note).

PRD section files (docs agent): one section per feature, rows exactly as above (ID, Rule, Source, Change via); the `planned` row keeps Source `planned`. Rule IDs in code docstrings of each source symbol (small-fixture convention).

## 5. Public API `market.api` (LG05)

Hidden tests import only `from market import api`. `api` re-exports: `Decimal`-free; dataclasses `Address`, `PaymentRequest`, `Product`, `Customer`, `Order`, `OrderQuote`, `PriceQuote`, `ReturnRequest`, `Notification`, `Review`, `StockAlert` (the last two from L2 and L3); errors `MarketError`, `NotFoundError`, `ValidationError`, `OutOfStockError`, `PolicyError`. Importing `api` registers loyalty and notifications handlers and the loyalty port. All money args accept `Decimal` or `str`; dates are `datetime.date`.

| Function | Returns | Rules exercised |
|---|---|---|
| `reset() -> None` | none | all (clears state, re-registers nothing needed) |
| `seed_demo() -> None` | none | section 1 data; calls `reset()` first |
| `set_now(value: datetime) -> None`, `advance_time(days: int = 0, hours: int = 0, minutes: int = 0) -> datetime` | clock | CRT-07, INV-04, LOY-05, RET-01 |
| `set_config(key: str, value) -> None`, `get_config(key: str)` | config | all `config` rules |
| `add_product(sku, name, category, price, weight_grams) -> Product` | product | CAT-01 to 04 |
| `get_product(sku) -> Product`, `deactivate_product(sku) -> Product`, `update_price(sku, new_price) -> Product` | product | CAT-05, 06 |
| `search_products(query: str = "", category: str \| None = None, max_price=None, sort: str = "name") -> list[Product]` | list | CAT-07 |
| `add_customer(customer_id, email, tier: str = "standard", region: str = "SP", tax_exempt: bool = False) -> Customer` | customer | SHP-03, TAX-01/02, LOY-02 |
| `set_stock(sku, on_hand: int) -> None`, `restock(sku, qty: int) -> int`, `available_stock(sku) -> int`, `expire_reservations() -> int` | stock | INV-01 to 08 |
| `add_coupon(code, kind: str, value=0, min_subtotal=0, starts_on=None, expires_on=None, per_customer_limit=None, global_limit=None, categories=()) -> None` | none | PRM-01 to 04, 10, 13 |
| `add_category_sale(sale_id, category, percent, starts_on, ends_on) -> None`, `add_bogo(rule_id, sku, buy: int = 2, free: int = 1) -> None`, `add_bundle(bundle_id, skus: tuple[str, ...], amount_off) -> None` | none | PRM-07 to 09 |
| `create_cart(customer_id) -> str` (cart id) | id | CRT-* |
| `add_to_cart(cart_id, sku, qty: int = 1) -> None`, `set_cart_quantity(cart_id, sku, qty) -> None`, `remove_from_cart(cart_id, sku) -> None` | none | CRT-01 to 05, CAT-05 |
| `apply_coupon(cart_id, code) -> None`, `remove_coupon(cart_id, code) -> None` | none | CRT-06, PRM-* |
| `quote_cart(cart_id) -> PriceQuote` | quote | PRC-01 to 06, PRM-01 to 13 |
| `quote_order(cart_id, address: Address \| None = None, shipping_method: str = "standard", points_to_redeem: int = 0) -> OrderQuote` | quote | CHK-03, 04, SHP-*, TAX-*, LOY-04 |
| `place_order(cart_id, payment: PaymentRequest, address: Address \| None = None, shipping_method: str = "standard", points_to_redeem: int = 0) -> Order` | order | CHK-01, 02, 05 to 07, 10, PAY-*, PRM-04, INV-03, NTF-01/02 |
| `get_order(order_id) -> Order`, `cancel_order(order_id) -> Order`, `mark_shipped(order_id) -> Order`, `mark_delivered(order_id) -> Order` | order | CHK-08, 09, LOY-06, NTF-03 |
| `issue_gift_card(code, balance) -> None`, `gift_card_balance(code) -> Decimal` | gift card | PAY-05, 07 |
| `get_payment(payment_id) -> Payment` (re-exported `Payment`) | payment | PAY-* |
| `points_balance(customer_id) -> int`, `grant_points(customer_id, points: int) -> None` | points | LOY-01 to 07 |
| `request_return(order_id, items: list[tuple[str, int]], reason: str) -> ReturnRequest`, `get_return(return_id) -> ReturnRequest` | return | RET-01 to 07 |
| `sent_notifications(recipient: str \| None = None, template: str \| None = None) -> list[Notification]` | list | NTF-01 to 05 |
| `event_history(name: str \| None = None) -> list` (of `Event`) | list | 2.9 |

Behavior notes the facade must keep: `add_to_cart` applies CRT/CAT/INV checks; `place_order` on a decline does NOT raise, it returns the Order with status `payment_failed`; any other failure raises the `MarketError` subclass of the rule; `grant_points` adds a lot with reason `grant` (counts toward LOY-05, earns no first-order status).

## 6. Seeded defects (no visible test covers either)

| ID | Where | Exact wrong behavior | Rule it violates | Why no visible test sees it |
|---|---|---|---|---|
| L4 (cross-feature) | `checkout/order_placement.py::_rollback` | The body calls `inventory.release(reservation_id)` only. The `promotion_usage.release_uses(order.order_id)` call is missing, so after a declined payment the coupon use stays held and counts against the customer's limit. `cancel_order` does call `release_uses` (correct). Chosen over a double inventory release because inventory release is idempotent (INV-05) and that keeps the defect where two features (checkout, promotions) and payments interact | CHK-06, PRM-04, CHK-10 (the retry is then refused) | Visible checkout tests on a decline use no limited coupon; visible promotion tests of limits never run a declined payment; visible tests check the reservation is released and the status is `payment_failed` only |
| L5 (inside the big file) | `promotions/promotion_engine.py::PIPELINE` | The tuple is `(stage_category_sales, stage_bogo, stage_bundles, stage_percent_coupons, stage_fixed_coupons, stage_free_shipping)`: the bundle runs before the percent coupon. A fixed bundle amount then shrinks the base of the percent coupon. Example: BK-100 + BK-200 (100.00) with SAVE10: correct discount 25.00 (coupon 10.00 then bundle 15.00, total 75.00), seeded 23.50 (bundle 15.00 then coupon 8.50, total 76.50) | PRM-05 | Visible engine tests cover each stage alone, and pairs sale+percent, bogo+percent, percent+fixed, cap; none puts a bundle and a percent coupon in the same evaluation. No visible test in pricing, cart or checkout does either |

Hidden tests of other scenarios must also avoid these two combinations (the large suite keeps both defects in every seed). Group A writes the correct code first, then applies the two changes above as the last step, and records them only in `eval/fixture-large/DEFECTS.md` (one line each, not shipped in `project/`).

## 7. Scenario hooks (LG06)

Layout per scenario: `request.md`, `decisions.md` (answers to the interview), `expected.json` (`case`, `size`, `prd_facts`, `dup_phrases`), `hidden/test_lN_hidden.py` importing only `from market import api`. Every hidden test starts with `api.reset(); api.seed_demo()`. Common helper in each file: `ADDR = api.Address("BR", "SP", "01000-000")`, `OK = api.PaymentRequest("card", "ok_1")`.

| ID | Case, size | Request (one sentence) | Rules touched | PRD must say after | Hidden test calls | Expected seed result |
|---|---|---|---|---|---|---|
| L1 | cross-feature change, M | The free-shipping threshold must be measured after loyalty points are redeemed, not before | SHP-03, CHK-04, LOY-04, CHK-03 (new CHK-04 text: points redeemed before shipping; shipping judged on merchandise after discounts and after redemption) | SHP-03 states the threshold applies to merchandise after discounts and after the loyalty discount; CHK-04 and LOY-04 are consistent; PRD cross reference between checkout, shipping and loyalty | `add_to_cart`, `grant_points`, `quote_order`, `place_order`. Case: C-REG, SP, EL-200 + HM-100 (200.00, 1800 g), 500 points: expect `shipping.fee == 16.00`, `tax.total == 17.28`, `loyalty_discount == 5.00`, `total == 228.28`; control without points: `shipping.fee == 0.00`, `total == 216.00`; VIP with 500 points on 100.00 or more keeps free shipping | tests with points FAIL (seed gives fee 0.00, total 211.00); control PASSES |
| L2 | new feature, L | Add product reviews: only customers who received a product can review it | New feature `reviews` (REV-01 to REV-05) | New PRD section `reviews` with REV rows; TRD file; feature CLAUDE.md | `submit_review(customer_id, sku, rating, text="") -> Review`, `list_reviews(sku) -> list[Review]`, `average_rating(sku) -> Decimal \| None` (see 7.1) | every test FAILS with `AttributeError` (names do not exist) |
| L3 | new feature, L | Let a customer ask to be told when a sold-out product is back in stock | New feature `stock_alerts` (ALR-01 to ALR-05), uses INV-08 event `inventory.restocked`, NTF | New PRD section `stock_alerts`; NTF rows gain template `back_in_stock`; TRD and CLAUDE.md | `subscribe_stock_alert(customer_id, sku) -> StockAlert`, `list_stock_alerts(customer_id) -> list[StockAlert]`, `restock`, `sent_notifications` (see 7.2) | every test FAILS with `AttributeError` |
| L4 | bug across features, S | A customer whose card was declined cannot use their single-use coupon on the retry | CHK-06, PRM-04, CHK-10 | Rows unchanged in meaning; CHK-06 or PRM-04 gain an explicit "the use is given back on decline" note if not present | `create_cart`, `add_to_cart`, `apply_coupon`, `place_order`. Case: C-REG, EL-200 x1, SAVE20, declined with `PaymentRequest("card", "decline_1")` then `PaymentRequest("card", "ok_1")` on the same cart: second order status `paid`, `discount_total == 24.00`, `total == 114.48` (96.00 + 10.00 + 7.68 + 0.80); also `inventory` available after the decline equals 5 | retry test FAILS with `ValidationError` (CHK-10); decline-state test PASSES |
| L5 | bug in big file, S | Quotes with a bundle and a coupon give the wrong discount | PRM-05, PRM-09, PRM-02 | PRM-05 unchanged (the code was wrong); no rule edit needed beyond a CHANGELOG line | `create_cart`, `add_to_cart`, `apply_coupon`, `quote_cart`. Case: C-REG, BK-100 + BK-200, SAVE10: `discount_total == 25.00`, `total == 75.00`; control: BK-100 + BK-200 alone `discount_total == 15.00`; SAVE10 alone on EL-200 + HM-100 `discount_total == 20.00` | main test FAILS (seed 23.50); controls PASS |
| L6 | refactor, C6, M | Split the 700-line promotion engine into smaller modules without changing behavior | none (TRD only: map, invariants) | PRD untouched; TRD `promotions.md`, `invariants.md` and the promotions CLAUDE.md list the new modules; `repo.md` and the ratchet allowlist drop the big file if it falls under the limit | Characterization over `quote_cart` for 12 carts covering sale, bogo, percent, fixed, cap, rejected coupons (NO bundle plus percent), plus structure tests reading `src/market/features/promotions/`: `promotion_engine.py` at most 350 lines, every `*.py` in that folder at most 300 lines, and `evaluate` still importable from `promotion_engine` | characterization PASSES, structure tests FAIL |
| L7 | rule gap, C5, M | VIP customers should have 60 days, not 30, to return a product | RET-01 (new text: 30 days, 60 for VIP) | RET-01 states 30 days for standard and 60 for VIP, with config key `returns.vip_window_days` (default 60); CHANGELOG entry | `add_to_cart`, `place_order`, `mark_shipped`, `mark_delivered`, `advance_time`, `request_return`. Case: delivered order, `advance_time(days=45)`: C-VIP return completes (`status == "completed"`), C-REG raises `PolicyError`; at `days=25` both complete; at `days=61` C-VIP raises `PolicyError` | VIP at 45 days FAILS; the rest PASS |
| L8 | implement planned, C2, S | Implement the approved first-order points bonus | LOY-07 (Source changes from `planned` to `loyalty/points_earning.py::points_for_order`, plus the `loyalty_events.on_order_paid` wiring) | LOY-07 Source is real code, no `planned` row remains; TRD loyalty file lists it | `place_order`, `points_balance`. Case: C-REG, EL-200 x1 (120.00 merch), card `ok_1`: first order balance `240`; second identical order (balance after second) `360`; C-VIP first order `480`; failed payments do not count as a first order | first-order assertions FAIL (seed 120 and 240); second-order delta (120) PASSES |

### 7.1 L2 contract (fixed names)

Data model `Review(review_id: str, customer_id: str, sku: str, rating: int, text: str, created_at: datetime, verified: bool)` (`verified` always True). Rules after the change (new section, IDs fixed):

| ID | Rule |
|---|---|
| REV-01 | Only a customer with a delivered or partially refunded order containing the SKU can review it; others get `PolicyError("not_verified_buyer")` |
| REV-02 | A rating is a whole number from 1 to 5; text is at most 500 characters; otherwise `ValidationError` |
| REV-03 | A customer has one review per SKU; submitting again replaces it (same `review_id`) |
| REV-04 | The average rating of a SKU is the mean of its ratings rounded half up to 1 decimal, or `None` with no reviews |
| REV-05 | Reviews are listed newest first |

`api.submit_review(customer_id: str, sku: str, rating: int, text: str = "") -> Review`; `api.list_reviews(sku: str) -> list[Review]`; `api.average_rating(sku: str) -> Decimal | None`. Hidden checks: ratings 5 and 4 average `Decimal("4.5")`; 5, 4, 4 average `Decimal("4.3")`; review without a delivered order raises `PolicyError`; rating 6 raises `ValidationError`; replace keeps one review. Files for the winning implementation: `features/reviews/` (not given to group A or B).

### 7.2 L3 contract (fixed names)

Data model `StockAlert(alert_id: str, customer_id: str, sku: str, created_at: datetime, notified: bool)`. Rules after the change:

| ID | Rule |
|---|---|
| ALR-01 | A customer can ask for an alert only on a SKU that has nothing available; otherwise `PolicyError("in_stock")` |
| ALR-02 | Asking twice for the same SKU returns the same alert |
| ALR-03 | A customer has at most 10 alerts waiting (not yet notified); the 11th raises `PolicyError("too_many_alerts")` |
| ALR-04 | When stock arrives for a SKU that had nothing available (`inventory.restocked`), every waiting alert is marked notified and sends the `back_in_stock` email to the customer |
| ALR-05 | A notified alert is not sent again; a new request after being notified creates a new alert |

`api.subscribe_stock_alert(customer_id: str, sku: str) -> StockAlert`; `api.list_stock_alerts(customer_id: str) -> list[StockAlert]`. Hidden checks: `set_stock("EL-200", 0)`, subscribe, `restock("EL-200", 3)`, then `sent_notifications(template="back_in_stock")` has one item for `reg@example.com` and the alert has `notified is True`; subscribing on an in-stock SKU raises `PolicyError`; `restock` again sends nothing new.

## 8. Sizes and visible tests

Source lines (excluding tests): infra 450, catalog 300, pricing 330, promotions 1,070, inventory 330, cart 300 (Group A 2,780); checkout 650, payments 400, shipping 220, tax 130, loyalty 320, returns 300, notifications 200, `api.py` 300, package and feature `__init__.py` about 150 (Group B 2,670). Total about 5,450, inside 4,000 to 6,000. Per-file targets are in section 2; a file may deviate by 25% except `promotion_engine.py` (650 to 750).

Visible tests live in `src/market/features/<f>/tests/test_<module>.py` (mirror of each module) and `src/market/infra/tests/`; `project/conftest.py` has an autouse fixture calling `market.infra.repositories.reset_all()`. `pyproject.toml`: `pythonpath = ["src"]`, `testpaths = ["src"]`. Tests may import features directly; hidden tests may not. Test counts are minimums.

| Feature | Tests (min) | Notes |
|---|---|---|
| infra | 14 | money.q2 half up cases, allocate, clock, config, events, repos |
| catalog | 24 | CAT-01 to 07 |
| pricing | 24 | PRC-01 to 06 |
| promotions | 48 | 26 in `test_promotion_engine.py` per stage and allowed pairs (never bundle with percent), 22 in the other modules |
| inventory | 22 | INV-01 to 08 |
| cart | 24 | CRT-01 to 07 |
| checkout | 30 | CHK-01 to 10 (declines tested with no limited coupon) |
| payments | 26 | PAY-01 to 08 |
| shipping | 24 | SHP-01 to 06 |
| tax | 16 | TAX-01 to 05 |
| loyalty | 20 | LOY-01 to 06 (nothing for LOY-07) |
| returns | 20 | RET-01 to 07 |
| notifications | 12 | NTF-01 to 05 |
| api | 10 | smoke through `market.api` with the demo data |
| Total | 294 | at least 250 required; all green on the seeded project |

Docs deliverable sizes (docs agent): PRD at `project/docs/prd/market/` with `01-summary.md` and one file per feature `02-catalog.md` to `13-notifications.md` in the order catalog, pricing, promotions, inventory, cart, checkout, payments, shipping, tax, loyalty, returns, notifications, plus INDEX, README, CHANGELOG, `prd.html` as in `eval/fixture/project/docs/prd/`; TRD at `project/docs/trd/` with README, one file per feature, `infra.md`, `invariants.md`, `testing.md`; `project/docs/flow.md` (the 2.11 sequence); one `CLAUDE.md` of at most 20 lines per feature folder; `project/repo.md` listing `promotions/promotion_engine.py` as a big file.
