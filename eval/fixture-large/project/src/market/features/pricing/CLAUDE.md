# features/pricing · Pricing

Quotes cart lines: volume breaks, promotions, totals. May import catalog and promotions.

- Rules: PRC-01 to PRC-06 in `docs/prd/market/03-pricing.md`; PRC-04 lives in `infra/money.py::allocate`.
- Entry: `quote_lines` (`price_calculator.py`), re-exported by `__init__.py`.
- Collaborators: `volume_breaks`, `discount_allocation`, `quote_models`; `promotions.promotion_engine.evaluate`.
- Domain: the volume break comes first, then promotions work on the running value.

Must not break:
- a cart line never stores a price (PRC-01);
- the total never goes below 0.00 (PRC-02);
- gift cards get no volume break (PRC-05).

Tests: `tests/` in this folder.

TRD: `docs/trd/pricing.md`
