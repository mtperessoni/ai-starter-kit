# prd-flow workers

Read this file, then only the file with your name in this folder. You do not talk to the user: anything missing becomes a **gap** in the return, never an assumption. Parallel batches whenever reads are independent; read by ID (`Grep -n`, then `Read` with offset and limit); a human-reading HTML is never read whole; big files listed in `repo.md` only by symbol. Write and edit docs with Write and Edit only, never through a Python or shell script; the only script you run is `gate.py`. Prose you write is in the `repo.md` `language` (default English); IDs, code, commit messages and file names are always English. No em dash (U+2014). State: `.claude/prd-flow/state/<slug>/`.

Return to the main thread, always in this format and at most 30 lines:

```
Done: <one line>
Files: <paths written or edited>
<the content your file asks for>
Gaps: <list, or "none">
```
