# AGENTS.md

This file supplements [docs/AGENT.md](D:\Vibe Coding Projects\Odin-Nav-Stack-LocalLLM\docs\AGENT.md).

Use `docs/AGENT.md` for project-level product, architecture, and platform discipline.
Use this file for execution coordination and round-state handling.

## Coordination workflow alignment

### Required inputs before any work
- Before starting any implementation, always read:
  - `coordination/bootstrap_prompt.md`
  - `coordination/latest_prompt.md`
- Treat `coordination/latest_prompt.md` as the single source of truth for the current round's scope, constraints, and acceptance criteria.

### Allowed execution roles
- Planner / Coordinator: defines the current round scope and acceptance criteria, primarily via `coordination/latest_prompt.md`
- Builder: implements only the current round's scoped changes
- Reviewer: validates the current round's implementation, verification, and scope discipline

### Subagent policy
- The main execution thread may explicitly create at most two subagents:
  - `builder-subagent`
  - `reviewer-subagent`
- Subagents must have single, narrow responsibilities
- Subagents may not create further subagents
- Subagent output is advisory; final responsibility remains with the main thread

### Workflow state machine
`PLANNED -> BUILDING -> REVIEWING -> PASSED / REWORK / NEEDS_HUMAN`

### PASS conditions
A round may enter `PASSED` only if all are true:
- the scoped task is completed
- acceptance criteria from `coordination/latest_prompt.md` are checked explicitly
- required verification or tests have been run
- no obvious out-of-scope edits were introduced
- `coordination/latest_result.md` has been updated

### REWORK conditions
Enter `REWORK` if any of the following is true:
- implementation does not satisfy `coordination/latest_prompt.md`
- verification fails
- reviewer identifies material risk, omission, or mismatch
- handoff / result documentation is incomplete

### NEEDS_HUMAN conditions
Stop and request human input if any of the following is true:
- architecture boundaries need to change
- security / secrets / production-risk issues appear
- more than one implementation direction is reasonable and requires product or CTO judgment
- the change would be destructive or breaking
- two review cycles fail to produce a stable `PASS`

### Delivery discipline
- Make the smallest viable change
- Read relevant code before editing
- Do not expand scope
- Do not perform unrelated refactors
- Update `coordination/latest_result.md` before concluding the round
- Commit only after verification passes
