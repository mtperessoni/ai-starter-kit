# Evaluation: current flow versus living truth

Compares two arms on the same synthetic project and the same requests, run unattended with `claude -p`:

| Arm | Kit | Spec-kit |
|---|---|---|
| A (current) | `main` | initialized (`specify init`), as in the projects where the flow works today |
| B (candidate) | `feat/living-truth` | none |

The candidate is adopted only when it is at least as good on quality and not worse on cost (M01 of `MAINTAINING.md`).

## Contract
| ID | Rule |
|---|---|
| EV01 | `eval/fixture/project/` is a small Python service (pytest, no third-party runtime deps) organized by feature under `src/orders/features/<feature>/` with tests beside the code in `<feature>/tests/`. Features: `pricing`, `shipping`, `checkout`. It already has what `/prd-create` and `/trd-create` would leave: `docs/prd/` (INDEX, README, CHANGELOG, one section file per feature with rule rows `| ID | Rule | Source | Change via |`), `docs/trd/` (README, one file per feature, invariants.md, testing.md), `docs/flow.md`, and a `CLAUDE.md` map of at most 20 lines per feature folder. Every module and test cites its PRD ID. The visible suite is green except the seeded bug of S3, which has no visible test |
| EV02 | Domain rules (illustrative IDs, the fixture fixes the final ones): PRC-01 VIP customers get 15% off; PRC-02 a coupon gives its percentage off; PRC-03 the total discount is capped at 30% of the subtotal; SHP-01 shipping costs 15.00; SHP-02 shipping is free when the subtotal after discounts is 200.00 or more (seeded bug: code uses `>`); CHK-01 total = subtotal - discount + shipping, rounded half up to cents; CHK-02 checkout returns a `Receipt` with `subtotal`, `discount`, `shipping`, `total`. Money is `Decimal` |
| EV02b | Public API, the only surface hidden tests import: `from orders import checkout, Cart, CartItem, Customer, Coupon, Receipt`. `Customer(id: str, vip: bool = False)`, `CartItem(sku: str, unit_price: Decimal, qty: int)`, `Cart(items: list[CartItem])`, `Coupon(code: str, percent: Decimal)`, `checkout(cart, customer, coupon=None) -> Receipt`, `Receipt(subtotal, discount, shipping, total)` all `Decimal`. S2 adds `Customer.store_credit_balance: Decimal = Decimal("0")`, `Receipt.store_credit_used` and `orders.confirm(receipt, customer)`, which decreases the balance. `src/orders/features/checkout/` starts as one module of about 300 lines that mixes validation, totals, rounding and receipt building, so S4 has something to split |
| EV03 | `eval/fixture/fill.json` maps, per installed file path, each placeholder literal to its value for this project (`{"CLAUDE.md": {"<placeholder>": "value"}}`). It covers the placeholders of both refs (`main` and `feat/living-truth`); keys absent from a file are ignored |
| EV04 | `eval/build.py --ref <git ref> --out <dir> [--spec-kit]` builds a fresh project: copies the fixture, extracts `kit/` from the ref with `git archive`, installs the payload as `installer/ai-kit/reference/ownership.md` says (appending `gitignore.kit` to `.gitignore`), applies `fill.json`, and fails when a `<...>` or `{{...}}` placeholder remains outside `docs/templates/`. With `--spec-kit` it first runs `specify init` for Claude (via `uvx --from git+https://github.com/github/spec-kit.git@<pinned tag>`), then lets the kit's constitution win. Ends with `git init` and one commit `chore: seed`. The arm's `gate.py` passes on the result |
| EV05 | `eval/scenarios/<id>/` has `request.md` (what a user would type), `decisions.md` (the answers a user would give to any question, in product language), `expected.json` and `hidden/` (pytest files the agent never sees, copied into `tests/hidden/` only for grading). `expected.json`: `case`, `size`, `rule_ids` (touched), `prd_patterns` (regexes the PRD must contain after the run), `dup_phrases` (regexes for the behavior text, counted outside `docs/prd/`) |
| EV06 | Scenarios. **S1** (C5, M): non-VIP customers get a discount cap of 20%; VIPs keep 30%. **S2** (C5, L): store credit: a customer has a `store_credit_balance`; checkout applies it after discounts and shipping, up to the total, and the `Receipt` gains `store_credit_used`; the balance decreases only on confirmation. **S3** (C3, S): "a customer with exactly 200.00 after discounts was charged shipping". **S4** (C6, S): split `checkout` into modules by responsibility, behavior unchanged. Hidden tests pin each behavior through the public `checkout(...)` entry and the names fixed in `decisions.md` |
| EV07 | `eval/prompt.md` is the one unattended prompt template for both arms: the request, the decisions, and "nobody can answer questions: follow this repository's own instructions end to end, including execution and commits; where you would ask, use the decisions, otherwise take the recommended option; never push" |
| EV08 | `eval/run.py --arms A B --scenarios S1 S2 S3 S4 --parallel 4 --budget-usd 12 --timeout-min 45 --out eval/results/<date>/` builds one project per pair in a throwaway folder outside the repository, runs `claude -p --output-format json --dangerously-skip-permissions --max-budget-usd <n>` with the prompt on stdin, saves the JSON, then grades. `--dry-run` builds and grades without calling claude |
| EV09 | `eval/grade.py <project> <scenario>` prints JSON metrics (below); `eval/report.py <results>` writes `report.md` with one table per scenario and the totals, A versus B |
| EV10 | `eval/results/` and the spec-kit cache are git-ignored except each run's `report.md` |

## Metrics
| Group | Metric | How |
|---|---|---|
| Quality | `hidden_pass` | Passed over total of `hidden/` |
| Quality | `suite_green` | The visible suite passes |
| Quality | `gate_ok` | The arm's own `gate.py` exits 0 |
| Fidelity | `prd_ok` | Every `prd_patterns` regex found in `docs/prd/` |
| Fidelity | `ids_in_tests` | Touched rule IDs cited by at least one test file, over all touched IDs |
| Fidelity | `docs_first` | For C5, the first commit touching `docs/prd/` precedes the first touching `src/` |
| Fidelity | `planned_left` | PRD rows still `planned` plus `## Planned` sections left |
| Duplication | `dup_count` | Matches of `dup_phrases` outside `docs/prd/`, `src/`, tests and `.claude/prd-gate/state/` |
| Duplication | `fr_lines` | Lines matching `FR-\d+` |
| Cost | `cost_usd`, `duration_min`, `turns`, tokens | From the `claude -p` JSON |
| Footprint | `doc_bytes` | Bytes added under `docs/`, `specs/`, `changes/` since the seed |
| Outcome | `completed` | Run ended without error and left commits after the seed |

## Decision rule
B is adopted when, over the four scenarios: `hidden_pass` and `prd_ok` are not lower than A, `gate_ok` holds in every B run, `dup_count` is not higher, and `cost_usd` and `duration_min` are at most 10% above A. One repetition per pair gives the direction only; a scenario within 10% is rerun before deciding.

## Running
```bash
python eval/run.py --dry-run                       # builds both arms and grades the seed, no claude call
python eval/run.py --arms A B --scenarios S1 S2 S3 S4
```
