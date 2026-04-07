# Coordination Protocol

## Purpose

This repository uses a file-based handoff between the CTO / PM / architecture-owner thread and the programmer thread.

Why:
- the CTO thread can reliably read repository files and git state
- separate chat threads should not depend on hidden conversation context
- each round should have one current prompt and one current result

---

## Source of Truth

- `coordination/latest_prompt.md`
  - maintained by the CTO / PM / architecture-owner thread
  - defines the current round goal, scope, constraints, and acceptance

- `coordination/latest_result.md`
  - maintained by the programmer thread
  - reports the actual outcome of the current round

- `coordination/archive/`
  - optional history snapshots when a round should be preserved before overwrite

- `coordination/bootstrap_prompt.md`
  - one-time message to send to the programmer thread so it adopts this protocol

---

## Round Workflow

1. CTO thread updates `coordination/latest_prompt.md`.
2. Programmer thread reads `coordination/latest_prompt.md` before starting work.
3. Programmer thread executes one coherent bundle only.
4. Programmer thread writes `coordination/latest_result.md` after the round.
5. User returns to CTO thread and asks it to read the latest result and decide the next round.
6. CTO thread reviews:
   - `coordination/latest_result.md`
   - current repo state
   - relevant code changes
   - git branch / status / commit state
7. CTO thread either closes the round or issues the next prompt by updating `coordination/latest_prompt.md`.

---

## Operating Rules

- `latest_prompt.md` and `latest_result.md` are intentionally overwritten each round.
- If history matters, copy them into `coordination/archive/round-XXX-prompt.md` and `coordination/archive/round-XXX-result.md` first.
- The programmer thread should not widen scope on its own when blocked.
- If the round fails, the programmer thread should write the narrowest accurate blocker and stop.
- Result files must describe the real repository state, not intended state.
- Git metadata in the result must match the current workspace.

---

## Required Prompt Sections

Each `latest_prompt.md` should include at least:
- round id or title
- current goal
- why this is the current priority
- in-scope work
- out-of-scope work
- architecture constraints
- acceptance criteria
- required result format reminders

---

## Required Result Sections

Each `latest_result.md` should include at least:
- round id or source prompt reference
- summary of what was done
- changed files
- validation or test results
- branch name
- `git status --short --branch`
- commit hash
- whether work is staged and/or committed
- blockers, risks, or limitations
- recommended next step

---

## Boundary Reminder

This protocol does not let one chat thread directly read or write another chat thread's hidden conversation.
It keeps coordination inside the repository, which is stable and reviewable.
