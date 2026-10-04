# Code structure for AI (AR) and code constraints (CX)

An agent finds code by name (Glob, Grep) and pays for every file and every hop it reads. Small files, one responsibility, a name that says what the file does and the PRD ID at the top let the agent read only what the task needs. In the source repository, one product rule was once spread over 10 folders and one function had 4,120 lines.

## Structure rules (AR)

The target repo's copy lives in `docs/code-structure.md` ([kit copy](../kit/docs/code-structure.md)). "Ratchet" means `scripts/ratchet.py` or the stack's linter enforces it; "review" means the reviewer and the planner check it.

| ID | Rule | Checked by | Why |
|---|---|---|---|
| AR01 | New code lives in the feature of the PRD area it implements (`src/features/<f>/`); what three or more features use and is not product rule goes to `src/infra/` (or `shared kernel` equivalent) | review | PRD area, TRD file, code folder and tests line up 1:1 |
| AR02 | One responsibility per file; the file name states it and is unique in the repository. Forbidden names: `helpers`, `utils`, `shared`, `common`, `misc`, `state` | ratchet | A generic name cannot be found by Grep and attracts unrelated code |
| AR03 | Size limits: module up to 500 lines, function up to 80, class up to 300, test file up to 1,200 | ratchet (modules, tests), linter (functions, classes) | Each read is bounded; an agent never needs a whole giant file |
| AR04 | Composition over mixins: a class receives small collaborators in its constructor, each readable alone. Never inherit from two in-repo classes | linter | Behavior is traceable without walking a hierarchy |
| AR05 | Explicit state: no `nonlocal` or closures sharing mutable state; a session's state is an object passed along | linter | Hidden state is invisible to Grep and to the reader |
| AR06 | Every feature module's docstring (or header comment) cites the PRD IDs it implements; every test cites the ID it proves | ratchet | One Grep by ID finds rule, code and test |
| AR07 | Every feature has a `CLAUDE.md` of at most 20 lines: responsibility, PRD IDs with their file, entry point, pieces, what must not break, where the tests are, link to its TRD. Changing a piece changes the map in the same commit. One per feature folder, not per folder | ratchet | Claude Code loads a subfolder's `CLAUDE.md` lazily, when a file of that folder is read, written or edited (not on Grep or Glob), and reloads it after `/compact`. Once loaded it is resent every call, so it must be short and only where a product unit lives |
| AR08 | Re-exports only in a feature's public entry (the package or module index); importers use the defining module. The public entry has no side effects (no route mounting, no engine import) | review | Patches and Grep land on the real definition; side effects in the entry closed an import cycle |
| AR09 | Dependency direction: feature uses `infra`; feature uses another feature only through its public entry; core features do not import peripheral ones; `infra` never imports a feature | linter | Changes stay local; cycles impossible |
| AR10 | Tests beside the code in `features/<f>/tests/`; harness files have their own name; a test class imported by another file gets an alias starting with `_` so the collector does not run it twice | review | Locality; the collector does not run imported classes twice |
| AR11 | Mocks target the module of the caller, not the definer nor a re-export | review | A misplaced patch silently stops working |
| AR12 | Moving code is done by script (line ranges or AST), never retyped; the model decides the map and fixes imports | review | Retyping is slow and introduces bugs |
| AR13 | The TRD is 1:1 with the features: `docs/trd/<f>.md` is the technical map of the folder, and the folder's `CLAUDE.md` points to it | review | One map per folder, no overlap |
| AR14 | Paths computed from the module's own location (`Path(__file__).parents[N]`, `import.meta.url`) use the module's real depth; after moving, check them | review | Moves break these silently |

## The ratchet

| ID | Rule | Why |
|---|---|---|
| AR15 | A structural check fails when a "ratchet" rule is violated outside an allowlist | Rules nobody enforces rot |
| AR16 | The allowlist only shrinks: a value above its entry fails; an entry that is already within the limit, or whose target no longer exists, also fails until removed; an entry that dropped must be lowered | Progress is locked in automatically |
| AR17 | Start with an allowlist of the current state (`python scripts/ratchet.py --init`); no refactor is required before adopting the rules | Adoption on day one, improvement over time |
| AR18 | The ratchet is always run with the related tests of any task (TS02) | Violations are caught in the task that creates them |
| AR19 | Split of enforcement: `scripts/ratchet.py` checks what text can see in any stack (module and test file size, generic names, duplicate names, PRD ID in feature module headers, feature `CLAUDE.md` present and short). Function and class size, inheritance, closures and import direction are syntax: the stack's linter enforces them, configured at setup with the same limits and its own baseline | The kit stays stack-free; the source repo did all of it in one AST test because it had one language |

## Code constraints (CX)

Recommended constraints for the target repo's `AGENTS.md` "Critical constraints". Adjust to the domain; each one prevented a real class of defect in the source repository.

| ID | Rule | Why |
|---|---|---|
| CX01 | Never swallow an exception and never fire-and-forget: every failure is persisted or logged with its cause; an empty `catch`/`except` is a violation | Silent failures were the hardest bugs to find |
| CX02 | Never hardcode a credential, token, key, model id, prompt or per-customer rule. It is typed configuration or versioned data | Hardcoded secrets leaked through exports |
| CX03 | Configuration is typed and validated at boot; the service refuses to start on missing or malformed config | A bad config found in production is an outage |
| CX04 | Never branch on a customer or tenant name (`if tenant == "X"`); per-tenant behavior is a configuration row resolved at runtime | Copy-pasted per-customer flows are the anti-pattern |
| CX05 | Framework and vendor types do not cross into the domain layer; framework at the edges, domain testable in isolation | Domain tests stay fast and offline |
| CX06 | Every side effect logs, structured, with the correlation ids of the request | Auditability |
| CX08 | An environment variable only for what changes per environment (secret, address, route, rollout flag); product behavior goes to typed configuration in code or versioned data | Behavior hidden in env vars cannot be reviewed, tested or rolled back per tenant |
| CX09 | `.env.example` lists every configuration key with a safe placeholder; a test asserts every settings field has a key there and no value has a secret shape. A removed variable is ignored, and a test proves it is no longer a setting | The example file is the contract with deploy; it drifted silently before the test |
| CX10 | Secrets scan in CI over tracked files (gitleaks with the default rules plus an allowlist of generated paths) | A credential in a commit is a leak even after revert |
| CX11 | Every text file is LF in the repository and every checkout (`.gitattributes`: `* text=auto eol=lf`), whatever the machine's `core.autocrlf` says | A CRLF checkout on Windows broke byte-for-byte comparisons and produced lint noise |
| CX07 | A behavior that the product decides by an AI agent is never replaced by a code heuristic on failure (term lists, similarity cuts, reserve plans); offer agent-based retries or explicit end states. A code check that is a safety guardrail is named as such | Heuristic fallbacks produced the very defects the agent was meant to fix (applies to AI-driven products) |
