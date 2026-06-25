# ENIGMA-MCU — Operating Manual for Claude Code Sessions

This file is read first by every Claude Code session. You may be a **fresh
session with no memory of prior work**. That is expected and by design. This
document tells you how to reconstitute full context from the repository and how
this project is built. **The repository is the memory — not any chat.**

## Bootstrap — read these, in order, before doing anything

1. `CONSTITUTION.md` — the invariants of the system. Never violate them.
2. `docs/ROADMAP.md` — the phase map. Identify the **current phase**.
3. The **active SPEC** for the current phase (`docs/specs/SPEC-NNN-*.md`). Your
   scope for this session is defined here and in the session brief.
4. The existing **test suite** (`tests/`) — the real, current state of the
   system. Trust the tests over any prose.
5. The **last session report**, if one is included in your brief.

After step 5 you have full context. Do not rely on memory of any previous chat.

## How this project is built — the two-loop model

- **Outer loop (architect, in chat).** Holds the macro-plan, writes and updates
  the durable artifacts (Constitution, SPECs, ADRs), reviews each session report,
  and dispatches the next session brief.
- **Inner loop (you, Claude Code).** Receive a bounded brief plus the repository,
  execute one scoped unit harness-first (RED → GREEN), commit, and emit a session
  report.

## Working rules (non-negotiable)

- **Harness-first.** Write or confirm the failing test that encodes the contract
  *before* implementing. Implement until GREEN. Never edit a test to make it pass
  without explicit instruction.
- **Stay in scope.** Do only what the active SPEC and the session brief declare.
  Respect the brief's "do-not-touch" list. Out-of-scope ideas go into the session
  report as proposals, not into the code.
- **Never merge RED.** No commit to `main` leaves the harness failing.
- **Artifacts in English.** Code, comments, docs, commit messages — all English.
  Use conventional commit messages.
- **Provenance & idempotency.** When writing ingestion code, honor Constitution
  §3 (provenance) and §7 (idempotent, stable IDs) without exception.

## Stop conditions — prevent hallucination

Stop the session and emit a report when **either** is true:

- the session's declared scope is complete; **or**
- you notice **context degradation** — repeating earlier mistakes, forgetting
  decisions already made, or re-asking questions already answered.

Do not push through degradation. Stop, report, end the chat. A new session
resumes cleanly via **Bootstrap**.

## Session report — emit this at session end

Output exactly this structure. The architect pastes it back into the outer loop.

```
## Session Report — <phase / scope>

**Commits:** <hash> <message>   (one line each)

**Harness:** <tests added>; <RED → GREEN summary>; <current pass/fail count>

**Decisions taken:** <decision> — <one-line rationale>   (or "none")

**Open questions / blockers:** <item>   (or "none")

**Deviations from SPEC:** <what differed and why>   (or "none")

**Proposed next step:** <the single most logical next scope>
```

## Prime directive

Leave the repository in a state where a fresh session, reading only the
repository, could continue your work. If it could not, your documentation is
incomplete — fix that before you stop.
