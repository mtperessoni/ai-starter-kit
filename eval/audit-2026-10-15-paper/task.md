Add a weight validator to this repository, following the existing height validator exactly.

- New file `src/lib/validators/weight.ts`, same three layered exports as `height.ts`: `isValidWeight`, `weightCheck`, `weightSchema`. It accepts a stored value like `"70 kg"` or `"70"`, strips the unit, and is valid between 1 and 400 inclusive. Reuse the message pattern height uses; add a message under `zodMessages.validators` if height has one.
- Export it from `src/lib/validators/index.ts` the same way height is exported.
- New test `src/lib/validators/__tests__/weight.test.ts` mirroring the height test: valid values, the bounds, a value with the unit, an empty string and a non-number.
- Run only that test file with `bash scripts/gates.sh one src/lib/validators/__tests__/weight.test.ts` until it passes.

Do not commit. When it passes, reply with one line: the files you changed.
