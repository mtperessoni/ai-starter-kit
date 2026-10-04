# Rust

## Detect
| Signal | Means |
|---|---|
| `Cargo.toml` with `[workspace]` | workspace: one crate per feature area is natural |
| `clippy.toml` | clippy configured |
| `tests/` folders | integration tests per crate |

## Commands
| Key | Value |
|---|---|
| `commands.test` | `cargo test` |
| `commands.offline_args` | `--lib --bins` (integration tests in `tests/` excluded) |
| `commands.integration_args` | `--test '*'` |
| `commands.no_coverage_args` | empty |
| `commands.lint` | `cargo fmt --check && cargo clippy --all-targets -- -D warnings` |
| `commands.fix` | `cargo fmt && cargo clippy --fix --allow-dirty` |
| `commands.import_check` | `cargo check` |
| `tests.runner` | `cargo test {filter}` with the installer turning files into module paths |
| `tests.native_related` | empty |
| `tests.failure_regex` | `^test (\S+) \.\.\. FAILED` |

## Structure enforcement
- Function length (AR03): clippy `too_many_lines` (pedantic) with `too-many-lines-threshold = 80` in `clippy.toml`; file length by `scripts/ratchet.py`.
- Import direction (AR09): crate boundaries in the workspace (a crate cannot import what it does not depend on); inside a crate, `pub(crate)` and module privacy.
- AR04 does not apply; AR05: review `static mut` and interior mutability shared across modules.
- Baseline: `#[allow(clippy::too_many_lines)]` on existing offenders, listed and removed wave by wave.

## Offline guard
Traits and fakes in unit tests; network and database tests live in `tests/` or behind a feature flag.

## CI setup
```yaml
      - uses: dtolnay/rust-toolchain@stable
        with:
          components: clippy, rustfmt
      - uses: Swatinem/rust-cache@v2
```

## Ignore
`**/target/**`, `Cargo.lock` (for gitleaks only).
