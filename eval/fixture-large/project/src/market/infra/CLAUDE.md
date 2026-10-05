# infra · Shared code

Errors, money, clock, config, events, repositories, ids, shared models and customers. Imports no feature.

- Rules: PRC-04 (`money.allocate`) in `docs/prd/market/03-pricing.md`; config keys feed every `config` rule.
- Entry: `money.q2`, `money.allocate`, `events.publish`, `config.get`, `repositories.repo`, `clock.now`.
- Domain: `reset_all` clears repos, ids, config overrides, clock and event history; subscribers stay.

Must not break:
- money is `Decimal`; `q2` only where a rule says so;
- `allocate` pieces sum exactly to the amount (PRC-04);
- event names and payload keys (see the TRD).

Tests: `tests/` in this folder.

TRD: `docs/trd/infra.md`
