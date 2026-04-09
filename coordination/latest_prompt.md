# Current Round Prompt

## Round
Round 050 - MVSim GUI Manual Review Bring-Up

## Goal
Now that the repo has a validated headless `live_runtime` path and the Windows-side WSL decode cleanup is complete, the next narrow goal is to make one truthful GUI-based MVSim operator review path available on this PC.

This round is a manual-review bring-up round.
It is not a new product-feature round.

## Why This Is The Current Priority

The current repo truth is good enough for automated and semi-automated validation:

- `live_runtime` has already passed end-to-end
- `compatibility_shim` comparison closure is already complete
- the recent Windows-side `UnicodeDecodeError` cleanup passed and is already merged on `main`

But there is still one practical gap for product review:

- almost all validated live-runtime flows still launch MVSim in `--headless` mode
- the repo does not yet provide a clean operator-owned path for "start the GUI simulator, watch the run, and attach the current bridge/harness to that same runtime"
- that means the project is technically validated, but still awkward for human demo/review

The next highest-value step is therefore not another correctness fix.
It is making one narrow GUI review path truthful and repeatable.

## Execution Discipline

- Follow the repo-root `AGENTS.md` workflow.
- Read `coordination/bootstrap_prompt.md` and this file before doing any work.
- Use the same bounded subagent pattern as the previous round:
  - `builder-subagent`
  - `reviewer-subagent`
- Keep subagent output advisory only; the main executor remains responsible for the final patch, validation, result file, commit, and push.

## In Scope

- identify the narrowest truthful way to launch the current repo-owned MVSim live-validation world with a visible GUI on this PC
- preserve the already-validated headless path; do not replace it
- prefer the same validated live asset seam where possible:
  - `content/sim/mvsim/worlds/odin_live_multistop_tour.world.xml`
  - the existing `live_runtime` WSL bring-up path
- determine whether the best repo-owned GUI review path should be:
  - a small launcher/script addition
  - a narrow extension of an existing script
  - or a documentation-first operator command path if no code is needed
- if GUI launch succeeds, prove at least one existing Windows-side consumer can attach to the already-running GUI runtime, preferably through one of:
  - the current live bridge demo with `--attach-existing-runtime`
  - the current validation harness / live validation path
- record the exact operator steps for a future human review session
- update docs only where the operator-facing review path becomes materially clearer

## Desired Outcome

At the end of this round, the repo should be in one of these honest states:

1. A repo-owned GUI MVSim review path works on this PC, and the current stack can attach to it for at least one representative live review flow.
2. A GUI MVSim window can be launched, but the current bridge/harness attach path has a narrow blocker that is explicitly recorded.
3. GUI bring-up is blocked by a concrete environment/runtime issue on this PC, and that blocker is explicitly recorded with exact attempted commands.

Do not claim GUI review readiness unless a real GUI launch attempt was made on this machine.

## Out Of Scope

- new POI/content features
- new Android UI work
- broader harness redesign
- new comparison/export features
- simulator world redesign unless a tiny launch-related asset correction is absolutely required
- Isaac Sim work
- Orin NX work
- general-purpose simulator control frameworks

## Architecture Constraints

- keep `core` platform-independent
- keep simulator/runtime specifics in adapters/scripts/services seams
- do not introduce a new simulator orchestration layer just for this round
- prefer a tiny operator-facing launcher or doc path over broad service changes
- preserve the current validated headless `live_runtime` path
- do not let the business/runtime core depend directly on a GUI-only path

## Acceptance Criteria

- the round attempts one real GUI MVSim launch path on this PC
- the round identifies the narrowest truthful operator path for GUI review
- if GUI launch works, the round proves at least one current Windows-side consumer can attach to that already-running runtime
- the round records whether a visible GUI review path is now available for a human operator
- the round preserves the already-validated headless live-runtime path
- `coordination/latest_result.md` is updated with exact commands, observed results, and the true blocker state if any

## Result Requirements

When done, update `coordination/latest_result.md` with:

- what you changed
- exact files changed
- whether the round used:
  - a new script
  - an updated script
  - docs only
- the exact GUI launch command attempted
- the exact observed result of the GUI launch attempt
- whether a visible MVSim GUI window was actually available to the operator
- the exact attach/consumer command attempted after GUI bring-up
- the exact observed result of that attach path
- whether the headless validation path was rechecked and what happened
- whether this round ended in:
  - `mvsim_gui_review_path_ready`
  - `mvsim_gui_launch_ready_but_attach_blocked`
  - `mvsim_gui_review_blocked`
- the recommended human-review steps after this round
- exact validation performed
- branch name
- full `git status --short --branch`
- commit hash
- whether files are staged and/or committed
- whether push succeeded
- blockers, risks, or remaining gaps

If blocked, do not expand into general simulator engineering.
Stop at the narrowest GUI-review blocker and record it clearly.
