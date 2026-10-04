# Node (JavaScript and TypeScript)

## Detect
| Signal | Means |
|---|---|
| `pnpm-lock.yaml`, `yarn.lock`, `package-lock.json`, `bun.lockb` | package manager: pnpm, yarn, npm, bun; install with the frozen lockfile flag |
| `vitest` in devDependencies | Vitest |
| `jest` in devDependencies | Jest |
| `@playwright/test`, `cypress` | end-to-end tier: never part of the offline target |
| `tsconfig.json` | TypeScript: type check with `tsc --noEmit` |
| `eslint.config.*`, `.eslintrc*`, `biome.json` | linter already chosen |
| `next.config.*`, `nest-cli.json`, `vite.config.*`, `angular.json` | framework, for the source folders and the entry point |
| `workspaces` in `package.json`, `pnpm-workspace.yaml`, `turbo.json`, `nx.json` | monorepo: one commands block per package |

Prefer the project's own scripts in `package.json` (`test`, `lint`, `typecheck`) when they exist.

## Commands
| Key | Vitest | Jest |
|---|---|---|
| `commands.test` | `npx vitest run` | `npx jest` |
| `commands.offline_args` | `--exclude "**/*.int.test.*"` (or the project's integration pattern) | `--testPathIgnorePatterns integration` |
| `commands.integration_args` | `--dir tests/integration` | `--testPathPattern integration` |
| `commands.no_coverage_args` | `--coverage.enabled=false` | `--coverage=false` |
| `commands.lint` | `npx eslint . && npx prettier --check . && npx tsc --noEmit` | same |
| `commands.fix` | `npx eslint . --fix && npx prettier --write .` | same |
| `commands.import_check` | `npx tsc --noEmit` (plus `npx madge --circular src` for cycles) | same |
| `tests.runner` | `npx vitest run {files}` | `npx jest {files}` |
| `tests.native_related` | `npx vitest related {changed} --run` | `npx jest --findRelatedTests {changed}` |
| `tests.failure_regex` | `^\s*(?:FAIL\|×)\s+(\S+)` | `^FAIL\s+(\S+)` |

## Structure enforcement
ESLint core rules, at the kit's limits:
- `max-lines`: `["error", {"max": 500, "skipBlankLines": false, "skipComments": false}]` (AR03 modules; tests get 1200 through an override for test globs);
- `max-lines-per-function`: `["error", {"max": 80}]` (AR03 functions; there is no class-length rule, `max-lines` bounds the file);
- import direction (AR09): `eslint-plugin-boundaries` element types per feature, or `dependency-cruiser` with forbidden rules (`no-circular`, feature to feature only through `index`);
- AR04 and AR05 are reviewed (no core rule).
Baseline day one: run ESLint once, put the current violations in an `overrides` block listing those files (shrink-only, reviewed like the ratchet allowlist), or use `eslint --max-warnings` with the new rules as warnings and lower the number each wave.

## Offline guard
A setup file (`setupFiles` in Vitest, `setupFilesAfterEach` in Jest) that rejects network calls outside loopback (for example `nock.disableNetConnect()` with `enableNetConnect(/127\.0\.0\.1|localhost/)`, or MSW with `onUnhandledRequest: "error"`), and under the offline flag also rejects localhost and database clients.

## CI setup
```yaml
      - uses: actions/setup-node@v4
        with:
          node-version-file: .nvmrc
          cache: <npm|pnpm|yarn>
      - name: Install dependencies (locked)
        run: <npm ci | pnpm install --frozen-lockfile | yarn install --frozen-lockfile>
```

## Ignore
`**/node_modules/**`, `**/dist/**`, `**/build/**`, `**/.next/**`, `**/coverage/**`, `**/.turbo/**`, lockfiles.
