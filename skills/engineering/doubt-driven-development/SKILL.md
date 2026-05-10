---
name: doubt-driven-development
description: Subjects every non-trivial decision to a fresh-context adversarial review before it stands. Use when correctness matters more than speed, when working in unfamiliar code, when stakes are high (production, security-sensitive logic, irreversible operations), or any time a confident output would be cheaper to verify now than to debug later.
source: https://github.com/addyosmani/agent-skills
installed: 2026-05-10
---

# Doubt-Driven Development

> Source: [addyosmani/agent-skills](https://github.com/addyosmani/agent-skills/tree/main/skills/doubt-driven-development)

A confident answer is not a correct one. Long sessions accumulate context that quietly turns assumptions into "facts" without anyone noticing. Doubt-driven development is the discipline of materializing a fresh-context reviewer — biased to disprove, not approve — before any non-trivial output stands.

This is not /review. /review is a verdict on a finished artifact. This is an in-flight posture: non-trivial decisions get cross-examined while course-correction is still cheap.

## When to Apply

**Apply when a decision is non-trivial** (at least one of these is true):
- It introduces or modifies branching logic
- It crosses a module or service boundary
- It asserts a property the type system or compiler cannot verify (thread safety, idempotence, ordering, invariants)
- Its correctness depends on context the future reader cannot see
- Its blast radius is irreversible (production deploy, data migration, public API change)

**Use when:**
- About to make an architectural decision under uncertainty
- About to commit non-trivial code
- About to claim a non-obvious fact ("this is safe", "this scales", "this matches the spec")
- Working in code you don't fully understand

**Skip when:**
- Mechanical operations (renaming, formatting, file moves)
- Following a clear, unambiguous user instruction
- One-line changes with obvious correctness
- Pure tooling operations (running tests, listing files)
- The user explicitly asked for speed over verification

## Doubt Cycle Checklist

```
Doubt cycle:
- [ ] Step 1: CLAIM — wrote the claim + why-it-matters
- [ ] Step 2: EXTRACT — isolated artifact + contract, stripped reasoning
- [ ] Step 3: DOUBT — invoked fresh-context reviewer with adversarial prompt
- [ ] Step 4: RECONCILE — classified every finding against the artifact text
- [ ] Step 5: STOP — met stop condition (trivial findings, 3 cycles, or user override)
```

## The 5 Steps

### Step 1: CLAIM
Name the decision in two or three lines:

```
CLAIM: "The new caching layer is thread-safe under the read-heavy workload described in the spec."
WHY THIS MATTERS: a race here corrupts user data and is hard to detect in QA.
```

If you can't write the claim that compactly, you have a vibe, not a decision. Surface it before scrutinizing it.

### Step 2: EXTRACT
A fresh-context reviewer needs the artifact and the contract, not the journey:
- **Code**: the diff or the function — not the whole file
- **Decision**: the proposal in 3–5 sentences plus the constraints it has to satisfy
- **Assertion**: the claim plus the evidence that supposedly supports it

Strip your reasoning. If you hand over conclusions, you'll get back validation of your conclusions.

### Step 3: DOUBT
The reviewer's prompt must be adversarial. Framing decides the answer.

```
> Adversarial review. Find what is wrong with this artifact.
> Assume the author is overconfident. Look for:
> - Unstated assumptions
> - Edge cases not handled
> - Hidden coupling or shared state
> - Ways the contract could be violated
> - Existing conventions this might break
> - Failure modes under unexpected input
> Do NOT validate. Do NOT summarize. Find issues, or state explicitly that you cannot find any after thorough examination.
>
> ARTIFACT: <paste artifact>
> CONTRACT: <paste contract>
```

**In Claude Code**: Use role-based reviewers in agents/ — they start with isolated context by design.

### Step 4: RECONCILE
Classify every finding in this precedence order:
1. **Contract misread** — Fix the contract first, re-classify on next cycle
2. **Valid + actionable** — Change it, re-loop
3. **Valid trade-off** — Document explicitly so the user sees it
4. **Noise** — Note it, move on

### Step 5: STOP
Stop when:
- Next iteration returns only trivial or already-considered findings
- 3 cycles completed (escalate to user)
- User explicitly says "ship it"

## Cross-Model Review

After single-model review, ask:

> "Single-model review complete. Want a cross-model second opinion? Options: Gemini CLI, Codex CLI, or skip."

Options:
- **Codex**: `codex exec --sandbox read-only -C <repo-path> - < /tmp/doubt-prompt.md`
- **Gemini**: `gemini --approval-mode plan -p "" < /tmp/doubt-prompt.md`

Always verify the tool is in PATH before invoking.

## Rationalization vs Reality

| "I'm confident, skip the doubt step" | Confidence correlates poorly with correctness on novel problems |
|---|---|
| "Spawning a reviewer is expensive" | Debugging a wrong commit in production is more expensive |
| "I'll do doubt at the end with /review" | By PR time it's too late — doubt-driven catches wrong directions early |
| "If I doubt every step I'll never ship" | The skill applies to non-trivial decisions, not every keystroke |

## Anti-Patterns

- Treating reviewer output as authoritative without re-reading the artifact text
- Looping >3 cycles without escalating to the user
- Prompting the reviewer with "is this good?" instead of "find issues"
- Re-spawning fresh-context on an unchanged artifact (same findings = stalling)
- Doubt theater: across 2+ cycles where reviewer surfaced substantive findings, zero were actionable

## Related Skills

- **code-review-and-quality / /review**: Complementary. /review is post-hoc; doubt-driven is in-flight per-decision
- **source-driven-development**: SDD checks the API exists; doubt-driven checks you used it correctly
- **test-driven-development**: TDD's RED step is doubt made concrete — a failing test is the doubt step
- **debugging-and-error-recovery**: When reviewer surfaces a failure mode, drop into debugging skill
