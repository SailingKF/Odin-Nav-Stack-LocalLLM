# Current Round Prompt

## Round
Round 039 - Harness Live Vs Compatibility Comparison Summary Baseline

## Goal
Now that the harness persists durable validation reports for both `live_runtime` and `compatibility_shim`, add a small operator-facing comparison surface that can summarize the latest live run against the latest compatibility run without rerunning either path.

## Why This Is The Current Priority

The current baseline is already strong:

- the harness can run truthful live MVSim validation
- the harness can run compatibility replay
- each run leaves behind a durable report artifact

The next small but valuable gap is comparison:

- the operator can inspect individual reports, but still has to mentally diff them
- future simulator, content, and edge work will benefit from a stable “latest live vs latest compatibility” sanity-check surface

This round should keep that scope tight:

- compare already-persisted reports
- do not build a generic analytics or dashboard system

## In Scope

- define a small comparison contract between the latest available:
  - `live_runtime` report
  - `compatibility_shim` report
- include only high-signal fields such as:
  - pass/fail
  - route completion
  - first/second stop truth
  - recent triggered/narrated spots
  - latest spot / latest narration
  - config identity when useful
- expose the comparison through the harness API
- if natural, surface a compact comparison card in the harness page
- keep comparison explicit about missing cases, for example:
  - no recent live report
  - no recent compatibility report
- update docs and focused tests

## Desired Outcome

At the end of this round, the repo should be in one of these honest states:

1. The harness can show a concise latest live-vs-compatibility comparison using persisted report artifacts only.
2. Comparison is partially implemented but the exact remaining blocker is explicit.

What is not acceptable is broadening this into a generic historical analytics system.

## Out Of Scope

- ROS 2 formal adapter
- simulator redesign
- map-format architecture
- autonomous navigation/path planning
- Isaac Sim
- Orin NX deployment work
- large UI redesign
- TTS/ASR expansion
- broad analytics or visualization platform work

## Architecture Constraints

- keep `core` platform-agnostic
- keep comparison logic in the harness/operator-facing service layer
- reuse persisted report artifacts rather than re-deriving comparison from raw event logs
- prefer a concise summary contract over a large schema
- keep live and compatibility truth claims explicit and separate

## Acceptance Criteria

- the harness can return a latest live-vs-compatibility comparison without rerunning validation
- missing-report cases are handled explicitly and readably
- if a UI surface is added, it remains compact and operator-focused
- focused tests still pass
- existing related tests still pass

## Result Requirements

When done, update `coordination/latest_result.md` with:

- what you changed
- exact files changed
- what comparison strategy was chosen
- what fields are compared
- whether the harness can now compare latest live and compatibility runs
- how missing-report cases are represented
- exact commands used
- what operator fact was actually validated
- whether the round ended in:
  - harness_comparison_summary_enabled
  - harness_comparison_summary_partially_enabled
  - harness_comparison_summary_blocked
- what the next narrow step is after this
- exact validation performed
- branch name
- full `git status --short --branch`
- commit hash
- whether files are staged and/or committed
- blockers, risks, or remaining gaps

If you hit a blocker, do not broaden into ROS, simulator redesign, or map-format work.
Stop at the narrowest real blocker and describe it clearly.
