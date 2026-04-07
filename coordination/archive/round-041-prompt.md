# Current Round Prompt

## Round
Round 041 - Latest Comparison Export Artifact Baseline

## Goal
Now that the harness can build a guardrailed latest `live_runtime` vs `compatibility_shim` comparison summary, add a small operator-facing export path so the latest comparison can be saved and shared as a stable artifact without copying raw JSON out of the browser manually.

## Why This Is The Current Priority

The current PC validation baseline is already strong:

- the harness can run truthful live validation
- it can run compatibility replay
- it persists report artifacts
- it can compare the latest live and compatibility reports
- it now guards against comparing incompatible validation assets

The next small but useful gap is exportability:

- the comparison is visible through the harness, but not yet packaged as a stable operator artifact
- future review, handoff, and edge/hardware bring-up will benefit from having a clear exported comparison snapshot

This round should stay narrow:

- export the latest already-computed comparison
- do not broaden into a generic reporting system

## In Scope

- define a compact export artifact shape for the latest comparison summary
- persist it in a clear repo-local location
- make it easy for the harness to generate or retrieve the latest export without rerunning validation
- include high-signal fields only, such as:
  - comparison status
  - comparability status
  - guardrail reasons
  - latest live report identity
  - latest compatibility report identity
  - compared outcome flags
- expose the export through a narrow API or harness action
- if natural, add a small harness UI affordance to trigger or open the latest export
- update docs and focused tests

## Desired Outcome

At the end of this round, the repo should be in one of these honest states:

1. The latest comparison can be exported as a stable operator artifact without rerunning validation.
2. Export is partially implemented but the exact remaining blocker is explicit.

What is not acceptable is broadening this into a general report-generation platform.

## Out Of Scope

- ROS 2 formal adapter
- simulator redesign
- map-format architecture
- autonomous navigation/path planning
- Isaac Sim
- Orin NX deployment work
- large UI redesign
- TTS/ASR expansion
- broad analytics or historical dashboards

## Architecture Constraints

- keep `core` platform-agnostic
- keep export logic in the harness/operator-facing service layer
- reuse persisted comparison/report data rather than recomputing from raw event logs
- prefer simple file-backed export artifacts
- keep the export concise and operator-readable

## Acceptance Criteria

- the harness can export the latest comparison summary without rerunning validation
- the export artifact location is clear and stable
- missing-comparison cases are handled explicitly and readably
- focused tests still pass
- existing related tests still pass

## Result Requirements

When done, update `coordination/latest_result.md` with:

- what you changed
- exact files changed
- what export strategy was chosen
- where export artifacts are stored
- what the exported comparison includes
- whether the harness can now export the latest comparison without rerunning validation
- how missing-comparison cases are represented
- exact commands used
- what operator fact was actually validated
- whether the round ended in:
  - comparison_export_enabled
  - comparison_export_partially_enabled
  - comparison_export_blocked
- what the next narrow step is after this
- exact validation performed
- branch name
- full `git status --short --branch`
- commit hash
- whether files are staged and/or committed
- blockers, risks, or remaining gaps

If you hit a blocker, do not broaden into ROS, simulator redesign, or map-format work.
Stop at the narrowest real blocker and describe it clearly.
