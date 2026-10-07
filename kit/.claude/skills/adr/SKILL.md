---
name: adr
description: |
  Creates a new Architecture Decision Record in `docs/adr/`. Reads `docs/adr/README.md` for the
  template, the numbering rule and the index, interviews the user for the real forces when they
  are not already clear from context, writes `docs/adr/NNNN-kebab-title.md`, and updates the index.
  Insists on at least two honest negative consequences and at least two genuinely considered
  alternatives with specific reasons they lost: an ADR with weak negatives is a sales pitch, not a
  record.
  TRIGGER on: "create an ADR", "write an ADR", "record this decision", "document this architecture
  decision", "/adr", "supersede ADR NNNN", when prd-flow routes a change to a protected rule here,
  and when a decision changes the constitution's Technology Constraints or reverses a recorded one.
  DO NOT TRIGGER on: product rules (prd-flow), feature specifications, implementation plans,
  constitution amendments by themselves, or anything that is not a decision with real alternatives.
---

# Create an ADR

An ADR is a record, not a proposal: it explains why the code looks the way it does to whoever inherits it, and preserves what was believed at the time, including where it was wrong.

## First: is this actually an ADR?
Per `docs/adr/README.md`, "When a new ADR is required". If nothing was chosen over something else, stop and say so: a decision with one option is a constraint, and it belongs in the constitution or `AGENTS.md`.

If the decision **reverses** an accepted ADR: never edit the old one to say the opposite. Write a new ADR and set the old one's status to `Superseded by NNNN`. Say this to the user before starting.

## Procedure

### 1. Read the source of truth
Read `docs/adr/README.md` in full: template, index, numbering, length. If it changed, it wins over this skill.

### 2. Number and title
`Glob docs/adr/*.md`. The next number is sequential from the highest, four digits, never reused. Filename `NNNN-kebab-title.md`, matching the `# ADR NNNN: <title>` heading. Title the decision, not the topic: "Configuration as versioned data per tenant" is a decision; "Configuration" is a topic.

### 3. Gather the real forces
Take what you can from the conversation, the code, the PRD and the repository. Ask, in one batch of at most 4 questions, only for what is missing:
- What actually forced this? The concrete situation, not the abstract benefit.
- What did we give up? The real cost.
- What else was genuinely on the table, and what specifically killed it?
- What would make us reverse this?
- Who decided, and when?

Never invent a force: a fabricated one reads as authoritative to the person inheriting it.

### 4. Ground it in evidence
Cite specifics: PRD rule IDs, constitution principles by number and name, specs, incidents, measurements, other ADRs. An ADR whose Context could describe any project is a bad ADR.

### 5. Write it
Follow the template exactly: Status, Date, Deciders, Context, Decision, Consequences (Positive, Negative, Neutral), Alternatives considered. About 400 to 700 words. Status `Accepted`, Date today.

Two non-negotiable bars:
- **At least two honest negatives.** A negative is honest when someone who opposed the decision would read it and feel heard. "It requires discipline", "there is a learning curve", "we need to document it" are advertisements: delete them. Name what could go wrong and who pays. If you cannot produce two, ask the user: "What is the strongest argument against this?"
- **At least two genuinely considered alternatives.** No strawmen. Each gets what it was good at and the specific reason it lost, tied to this project and date. "Do nothing" is often a real alternative.

### 6. Update the index
Add `| [NNNN](NNNN-kebab-title.md) | Title | Accepted |` in number order. If this supersedes an earlier ADR, change only that ADR's Status line and its index row; never its Context, Decision, Consequences or Alternatives.

### 7. Report
What you wrote, the path, the index row, and honestly: whether the negatives are real or weak for lack of forces; whether the constitution needs an amendment (its own pull request, with a semantic version bump); whether `AGENTS.md`, the TRD or the PRD now contradict the record.

## Hard rules
- No em dash (U+2014).
- English.
- Every sentence carries a fact or a reason.
- Do not record a decision that has not been made; help the user decide first.
- Commit `docs(adr): <decision>`; no push without an explicit request.
