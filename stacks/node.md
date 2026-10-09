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
| `tests.runner` | `npx vitest run {files} --reporter=default --reporter=junit --outputFile.junit=reports/junit.xml` | `npx jest {files} --reporters=default --reporters=jest-junit` |
| `tests.junit_xml` | `reports/junit.xml` (default on) | `reports/junit.xml` (default on, with `JEST_JUNIT_OUTPUT_FILE`) |
| `tests.native_related` | `npx vitest related {changed} --run` | `npx jest --findRelatedTests {changed}` |
| `tests.failure_regex` | `^\s*(?:FAIL\|×)\s+(\S+)` | `^FAIL\s+(\S+)` |

## Structure enforcement
ESLint core rules, at the kit's limits:
- `max-lines`: `["error", {"max": 500, "skipBlankLines": false, "skipComments": false}]` (AR03 modules; tests get 1200 through an override for test globs);
- `max-lines-per-function`: `["error", {"max": 80}]` (AR03 functions; there is no class-length rule, `max-lines` bounds the file);
- import direction (AR09): `eslint-plugin-boundaries` element types per feature, or `dependency-cruiser` with forbidden rules (`no-circular`, feature to feature only through `index`);
- AR04 and AR05 are reviewed (no core rule).
| Rule | Tool | Baseline |
|---|---|---|
| AR24 complexity | ESLint `complexity` (10), `max-depth` (4), `max-nested-callbacks`, `max-params` (5) | the `overrides` block below |
| AR25 dead code | `knip` (unused files, exports, dependencies; `knip.json` `ignore` for framework-reached files), or `ts-prune` | `knip --baseline`-style file: look up the installed version, else an `ignore` list, shrink-only |
| AR26 duplicates | `jscpd --min-lines 10 --min-tokens 70 src` | report of today, new duplicates fail |
| AR27 typing | TypeScript `strict: true` per package; in a JS or loose TS repo, `tsconfig.strict.json` extending the base with `strict` and an `include` list of strict modules that only grows (or `// @ts-check` per file) | the `include` list |
| AR22 dispatch | ESLint `import/no-dynamic-require`, `no-eval`, `no-new-func`, `@typescript-eslint/no-implied-eval`; computed property calls (`obj[name]()`) are review | linter plus review |

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

## Layout
| Layout | Declare |
|---|---|
| Feature folders (`src/features/<f>/`) | `layout: "Feature folders under src/features"`, `feature_root` |
| NestJS: one module per domain (`src/<m>/<m>.module.ts`, `.controller.ts`, `.service.ts`) | `layout: "NestJS, one module per domain under src/"`, `areas: {"<m>": ["src/<m>/**"]}`, or `feature_root: "src"` when every subfolder is a module |
| Angular: feature modules or standalone feature folders (`src/app/<f>/`) | `layout: "Angular feature folders under src/app"`, `feature_root: "src/app"` |
| Next.js App Router: `app/<route>/` plus `components/`, `lib/` | `layout: "Next.js App Router: route folders in app/ plus shared components/ and lib/"`, `areas` per PRD area with its route folder and component globs, `map_dirs: ["app", "components", "lib"]` |
| Express or React by layer (`routes/`, `services/`, `components/`, `hooks/`) | `layout: "Folders by technical role (routes, services, components, hooks); product areas spread across them"`, `areas` by file name per PRD area, `map_dirs` the layer folders |
| Monorepo packages (`packages/*`, `apps/*`) | `layout: "Monorepo with one package per app or domain"`, one area per package: `areas: {"<p>": ["packages/<p>/**"]}` |

## Test naming
- `tests.mirror_patterns`: `["{name}.test", "{name}.spec"]`; `tests.match_symbol: false`.
- Tests beside the code (`<area>/tests/` or `{name}.test.ts` next to the module) or a top-level `tests/` or `__tests__/` mirroring the tree (AR10).
- `tests.junit_xml`: `reports/junit.xml`; Vitest `--reporter=default --reporter=junit --outputFile.junit=reports/junit.xml`; Jest with the `jest-junit` package (`JEST_JUNIT_OUTPUT_FILE=reports/junit.xml`, `--reporters=default --reporters=jest-junit`).

## Generated files
`generated_patterns`: `**/*.generated.ts`, `**/*.gen.ts`, `**/generated/**`, `**/__generated__/**`, `**/*.d.ts` in generated folders, `src/graphql/types.ts` (graphql-codegen), `**/*.pb.ts`, Prisma client output, `**/routeTree.gen.ts`. Markers: graphql-codegen and openapi-typescript write `/* eslint-disable */` plus `This file was auto-generated`; protobuf writes `Generated by`; for others add `// generated, do not edit`.

## Framework exemptions
- `unique_name_exempt`: `index.ts`, `index.tsx`, `page.tsx`, `layout.tsx`, `route.ts`, `loading.tsx`, `error.tsx`, `not-found.tsx` (Next.js), `main.ts`, `app.module.ts`, `app.component.ts`, `*.module.ts` (NestJS and Angular), `vite.config.ts`, `setupTests.ts`.
- AR04: classes the framework requires (Angular components and services, NestJS providers, React error boundaries as classes) are allowed.
- AR05: React hooks (`useState`, `useReducer`, context), Redux or Zustand or Pinia stores, signals, NgRx stores and XState actors count as explicit state.
- `id_header_lines`: default; raise to the number of import lines only when files open with a long import block (a comment above the imports is preferred).

## Snapshots
Agents never run `vitest -u` or `vitest --update`, `jest -u` or `jest --updateSnapshot`, or `playwright test --update-snapshots`. Globs: `**/__snapshots__/**`, `**/*.snap`, `**/*-snapshots/**`.

## Contracts
- NestJS: a script that builds the Swagger document (`SwaggerModule.createDocument`) and writes `docs/contracts/openapi.json`; GraphQL: `schema.gql` autoSchemaFile or `npx graphql-inspector introspect` (look up).
- Prisma: `prisma/schema.prisma` is the snapshot; Drizzle: `drizzle-kit` schema folder; otherwise a SQL schema dump.
- Next.js or Express without a schema: the project's OpenAPI file, or `contracts: []` and a note in the TRD.

## Setup
`commands.setup`: `npm ci`, `pnpm install --frozen-lockfile`, `yarn install --frozen-lockfile` or `bun install --frozen-lockfile`; add the generate step when the project has one (`npx prisma generate`, `npm run codegen`).
