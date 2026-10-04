# features/tax · Tax

Regional rates and tax per line and on shipping. May import pricing (models only) and catalog (`category_rules`).

- Rules: TAX-01 to TAX-05 in `docs/prd/market/10-tax.md`; index in `docs/prd/INDEX.md`.
- Entry: `compute_tax` (`tax_calculator.py`).
- Collaborators: `tax_rates` (`rate_for`).
- Domain: tax per line on the line total after the discount split, rounded, then summed; shipping taxed the same way.

Must not break:
- exempt products and tax-exempt customers pay nothing (TAX-02);
- free shipping has no tax (TAX-04);
- tax is added on top, never included (TAX-05).

Tests: `tests/` in this folder.

TRD: `docs/trd/tax.md`
