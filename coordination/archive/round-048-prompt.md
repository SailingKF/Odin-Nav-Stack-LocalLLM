# Current Round Prompt

## Round
Round 048 - Compatibility Shim Validation And Comparison Export Closure

## Goal
Now that the live MVSim end-to-end path is verified on this PC, the next narrow goal is to run one fresh `compatibility_shim` harness validation so the latest comparison export can move from `missing_reports` to a real live-vs-compatibility comparison.

This round is a comparison-closure round.
It is not a feature-expansion round.

## Why This Is The Current Priority

Round 047 verified the live path end-to-end:

- the isolated harness stack completed a truthful `live_runtime` validation run
- live pose reached the stack
- first stop, second stop, and route completion were all observed
- a fresh live-runtime report was written

But the latest comparison export still says:

- `comparison_status = "missing_reports"`
- `missing_modes = ["compatibility_shim"]`

So the main remaining risk is no longer live-runtime bring-up.
The main remaining risk is that the repo still lacks one fresh compatibility-side report using the same validation assets, which means the latest comparison/export guardrail path is not yet closed on this PC.

## In Scope

- run one fresh harness validation in `compatibility_shim` mode using the current isolated harness stack
- use the same repo-owned harness/report surfaces already used in Round 047
- collect the new compatibility report
- trigger the comparison/export path again
- verify whether the latest comparison now becomes available and what it truthfully says
- verify whether the live and compatibility reports are directly comparable under the current guardrails
- update docs only if the current operator instructions or comparison truth become stale
- make only the smallest code changes needed if a narrow comparison/report seam bug is found

## Desired Outcome

At the end of this round, the repo should be in one of these honest states:

1. A fresh `compatibility_shim` report exists and the latest comparison export truthfully compares live vs compatibility on this PC.
2. The compatibility validation passes, but the comparison/export seam still has a narrow blocker that is recorded explicitly.
3. The compatibility validation itself is blocked, and the exact blocker is recorded explicitly.

Do not claim comparison closure unless a fresh compatibility report was actually written and the comparison surfaces were re-read.

## Out Of Scope

- new live-runtime work
- new UI features
- map/report redesign
- broader harness refactors
- Isaac Sim expansion
- Orin NX deployment work
- unrelated product functionality

## Architecture Constraints

- preserve the current harness/report/comparison seams
- do not push simulator-specific behavior into `core`
- prefer validating the existing isolated harness path over inventing a new flow
- if a bug is found, fix only the narrow compatibility/report/comparison seam required for truthful comparison output
- keep artifacts and result files honest about what was actually observed on this PC

## Acceptance Criteria

- the round runs a fresh `compatibility_shim` harness validation or records the exact blocker
- a fresh compatibility report is written, or the exact reason it was not is recorded
- the latest comparison/export surfaces are re-read after that compatibility attempt
- the round determines whether live and compatibility reports are directly comparable under current guardrails
- the round records the truthful comparison result or the exact narrow blocker

## Result Requirements

When done, update `coordination/latest_result.md` with:

- what you changed
- exact files changed
- the exact commands used
- the exact observed result of:
  - `python scripts/print_mvsim_live_probe.py --config configs/sim_harness.yaml`
  - harness run / API calls / status checks used for `compatibility_shim`
  - `GET /reports/latest`
  - `GET /reports/recent`
  - `GET /reports/compare`
  - `POST /reports/compare/export`
- whether a fresh `compatibility_shim` report was written and its path
- whether the latest comparison export still says `missing_reports`, or now reports a real comparison
- whether the reports were:
  - `comparable`
  - `comparable_with_warnings`
  - `not_directly_comparable`
- the key guardrail reasons, if any
- whether this round ended in:
  - `compatibility_comparison_closed`
  - `compatibility_report_written_but_comparison_blocked`
  - `compatibility_validation_blocked`
- what the next narrow step is after this
- exact validation performed
- branch name
- full `git status --short --branch`
- commit hash
- whether files are staged and/or committed
- blockers, risks, or remaining gaps

If blocked, do not broaden into new product work.
Stop at the narrowest compatibility/comparison blocker and record it clearly.
