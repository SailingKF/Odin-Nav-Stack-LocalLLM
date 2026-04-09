# Current Round Prompt

## Round
Round 049 - Windows WSL Subprocess Decode Cleanup

## Goal
Now that both the live-runtime path and the live-vs-compatibility comparison flow are verified on this PC, the next narrow goal is to remove the remaining Windows-side subprocess decoding risk that was observed while reading WSL process output.

This round is a cleanup and robustness round.
It is not a product-feature round.

## Why This Is The Current Priority

Round 047 and Round 048 proved that the current validation flows work, but they also left one real cleanup item:

- `session_logs/mvsim_validation_harness/round047/harness.stderr.log` captured `UnicodeDecodeError`
- the failures came from Python subprocess reader threads decoding WSL output with the Windows default codec
- the live validation still passed, so this is not a functionality blocker
- but it is still a correctness and observability risk on Windows for future runs

The next highest-value step is therefore not another validation feature.
It is making the current verified flow more robust and quieter on Windows.

## In Scope

- identify the narrow subprocess call sites that read WSL output with text decoding on Windows
- fix only the smallest seam needed so those WSL subprocess reads no longer raise `UnicodeDecodeError`
- prioritize the currently relevant paths:
  - `services/mvsim_validation_harness/runtime.py`
  - `services/sim_publisher_bridge/mvsim_live_source.py`
  - any directly related helper in the same live-runtime seam if required
- preserve current behavior and validation truth
- run the narrowest validation needed to prove:
  - no decode exception is emitted in the same Windows-side path
  - live probe still works
  - at least one representative harness or live-runtime path still works
- update docs only if operator-facing instructions materially change, which is not expected

## Desired Outcome

At the end of this round, the repo should be in one of these honest states:

1. The Windows-side WSL subprocess decode issue is fixed and the relevant validation path no longer emits `UnicodeDecodeError`.
2. The decode issue is reduced but not fully eliminated, and the exact remaining seam is explicit.
3. The attempted cleanup would risk changing validated behavior, and the narrow blocker is explicit.

Do not broaden into unrelated refactors.
Keep this strictly about WSL subprocess decoding robustness.

## Out Of Scope

- new live-runtime features
- new comparison/export features
- broader harness redesign
- UI changes
- Isaac Sim work
- Orin NX work
- unrelated product logic

## Architecture Constraints

- do not change `core` logic
- keep the fix local to subprocess/logging/bridge glue
- prefer explicit encoding/error-handling over broad behavioral rewrites
- preserve the current live-runtime and compatibility validation contracts
- avoid introducing a large abstraction layer just for this cleanup

## Acceptance Criteria

- the round identifies the concrete Windows-side WSL subprocess decode seam
- the round applies the smallest safe fix in that seam
- the relevant validation path no longer emits the observed `UnicodeDecodeError`, or the exact remaining case is recorded
- `python scripts/print_mvsim_live_probe.py --config configs/sim_harness.yaml` still works after the change
- at least one representative harness or live-runtime validation check still works after the change

## Result Requirements

When done, update `coordination/latest_result.md` with:

- what you changed
- exact files changed
- the exact subprocess/decode seam you fixed
- the exact commands used
- the exact observed result of:
  - `python scripts/print_mvsim_live_probe.py --config configs/sim_harness.yaml`
  - the representative harness or live-runtime validation command(s) you used
  - any stderr/log file you checked for decode failures
- whether `UnicodeDecodeError` was still observed
- whether this round ended in:
  - `windows_wsl_decode_cleanup_completed`
  - `windows_wsl_decode_cleanup_partially_completed`
  - `windows_wsl_decode_cleanup_blocked`
- what the next narrow step is after this
- exact validation performed
- branch name
- full `git status --short --branch`
- commit hash
- whether files are staged and/or committed
- blockers, risks, or remaining gaps

If blocked, do not broaden into product work.
Stop at the narrowest decode-cleanup blocker and record it clearly.
