# features/notifications · Notifications

Emails sent in reaction to events. Peripheral: imports no feature (events and `infra.customers` only).

- Rules: NTF-01 to NTF-05 in `docs/prd/market/13-notifications.md`; index in `docs/prd/INDEX.md`.
- Entry: `register` (called once by `__init__.py`), `send` (`dispatcher.py`).
- Collaborators: `templates` (subjects), `notification_events` (one handler per event), `notification_models`.
- Domain: handlers never change an order; ops gets low-stock mail at ops@market.test.

Must not break:
- one email per template, order and recipient (NTF-05);
- handlers never raise into the publisher.

Tests: `tests/` in this folder.

TRD: `docs/trd/notifications.md`
