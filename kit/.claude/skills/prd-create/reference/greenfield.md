# Greenfield interview (M2)

There is no code, so the user is the only source. The interview runs in this conversation, at most 4 questions per AskUserQuestion, each with a concrete scenario, options with trade-offs and the recommended one first. Record every answer in `interview.md` (`| Dimension | Question | Answer | Origin |`, origin `user` or `default`).

## Product level (before the outline)
| ID | Dimension | Guiding question |
|---|---|---|
| G01 | Problem | What goes wrong today, for whom, and how often? |
| G02 | Actors | Who uses it, who operates it, which systems call it or are called by it? |
| G03 | Goals | What must be true when this works? How is it measured? |
| G04 | Non-goals | What will deliberately not be done now? |
| G05 | Journey | The steps, in order, from trigger to result |
| G06 | Variants and tenants | Does it run on several platforms, channels or for several customers? What differs? |
| G07 | Constraints | Regulation, privacy, safety, latency, cost limits |

G01 to G03 come first: a wrong problem invalidates the rest. With G01 to G07 answered, write the outline (sections per step of G05) and approve it.

## Step level (per section)
For each journey step, the dimensions D01 to D15 of `.claude/skills/prd-gate/reference/interview.md` plus the extra ones in `repo.md`. Ask only what is open; adopt defaults the user accepts. A dimension the user does not want to decide becomes an open question with its default.

## Writing
Every rule gets Source `planned` and the marker `*(approved YYYY-MM-DD, pending code)*` is not used: in greenfield the whole PRD is planned, and `README.md` "How this document was made" says so. When code arrives, prd-gate C2 fills the Sources task by task.
