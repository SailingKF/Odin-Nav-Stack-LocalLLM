# Current Round Prompt

## Round
Round 042 - Human-Readable Comparison Export Baseline

## Goal
Now that the harness can export the latest guardrailed `live_runtime` vs `compatibility_shim` comparison as a JSON artifact, add a small human-readable export so operators can review and share the latest comparison without opening raw JSON.

## Why This Is The Current Priority

The current PC validation baseline is already strong:

- the harness can run truthful live validation
- it can run compatibility replay
- it persists report artifacts
- it can compare the latest live and compatibility reports
- it can export the latest comparison as JSON

The remaining operator gap is readability:

- the JSON export is durable and correct, but not the easiest artifact to scan or share quickly
- a compact Markdown or plain-text export would improve handoff without broadening scope

This round should stay narrow:

- keep the JSON export as the source of truth
- add one human-readable companion export
- do not broaden into a full reporting or document-generation system

## In Scope

- define a compact human-readable export shape for the latest comparison
- preferably generate it from the existing comparison summary / JSON export rather than recomputing from raw logs
- persist it in a clear repo-local location alongside or near the JSON export
- include only high-signal fields such as:
  - comparison status
  - comparability status
  - guardrail reasons
  - latest live report identity
  - latest compatibility report identity
  - compared outcome flags
- expose the latest human-readable export through a narrow API or harness affordance if natural
- update docs and focused tests

## Desired Outcome

At the end of this round, the repo should be in one of these honest states:

1. The latest comparison can be exported as both machine-readable JSON and a compact human-readable artifact.
2. Human-readable export is partially implemented but the exact remaining blocker is explicit.

What is not acceptable is broadening this into a generic document/report generation platform.

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
- reuse existing comparison/export data rather than recomputing from raw event logs
- prefer a very small Markdown or plain-text artifact
- keep the export concise and operator-readable

## Acceptance Criteria

- the harness can produce a human-readable latest comparison export without rerunning validation
- the artifact location is clear and stable
- missing-comparison cases are handled explicitly and readably
- focused tests still pass
- existing related tests still pass

## Result Requirements

When done, update `coordination/latest_result.md` with:

- what you changed
- exact files changed
- what human-readable export strategy was chosen
- where the human-readable artifacts are stored
- what the human-readable export includes
- whether the harness can now emit both JSON and human-readable latest comparison exports
- how missing-comparison cases are represented
- exact commands used
- what operator fact was actually validated
- whether the round ended in:
  - human_readable_comparison_export_enabled
  - human_readable_comparison_export_partially_enabled
  - human_readable_comparison_export_blocked
- what the next narrow step is after this
- exact validation performed
- branch name
- full `git status --short --branch`
- commit hash
- whether files are staged and/or committed
- blockers, risks, or remaining gaps

If you hit a blocker, do not broaden into ROS, simulator redesign, or map-format work.
Stop at the narrowest real blocker and describe it clearly.
