# Current Round Prompt

## Round
Round 040 - Validation Asset Identity And Comparison Guardrails Baseline

## Goal
Now that the harness can compare the latest `live_runtime` and `compatibility_shim` reports, make that comparison explicitly aware of which validation assets produced those reports so operators do not accidentally compare incompatible runs.

## Why This Is The Current Priority

The current operator baseline is already strong:

- the harness can run truthful live validation
- it can run compatibility replay
- it persists durable reports
- it can compare the latest live and compatibility reports

The main remaining risk is comparison ambiguity:

- future runs may use different validation worlds, vehicles, motion strategies, route/POI assets, or configs
- a latest-vs-latest comparison could become misleading if the underlying validation assets differ

The next most valuable step is to make report identity and comparison guardrails explicit before more simulator or deployment variants appear.

## In Scope

- define a small validation-asset identity contract for harness reports, including only the fields needed to decide whether two runs are meaningfully comparable
- likely candidates include:
  - config identity
  - validation mode
  - world file
  - vehicle identity
  - live alignment / motion strategy
  - route / POI asset identity when naturally available
- persist that identity into report artifacts
- extend the latest live-vs-compatibility comparison summary so it can say:
  - comparable
  - comparable with warnings
  - not directly comparable
- surface compact guardrail fields in the harness API/UI
- handle missing identity fields explicitly and readably
- update docs and focused tests

## Desired Outcome

At the end of this round, the repo should be in one of these honest states:

1. The harness comparison summary can clearly indicate whether the latest live and compatibility reports came from comparable validation assets.
2. Asset identity is partially captured but the exact remaining blocker is explicit.

What is not acceptable is silently implying that two reports are comparable when they come from different validation assets.

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
- keep validation-asset identity and comparison guardrails in the harness/operator-facing service layer
- reuse existing config/report information where possible
- prefer a concise identity contract over a large schema
- keep truth claims explicit: comparable vs not directly comparable

## Acceptance Criteria

- new reports include a clear validation-asset identity block
- the latest comparison summary explicitly reports comparability status
- mismatched or incomplete identity is handled readably
- focused tests still pass
- existing related tests still pass

## Result Requirements

When done, update `coordination/latest_result.md` with:

- what you changed
- exact files changed
- what validation-asset identity strategy was chosen
- what fields define report identity
- how comparison guardrails now work
- whether comparable vs non-comparable cases are explicit
- exact commands used
- what operator fact was actually validated
- whether the round ended in:
  - comparison_guardrails_enabled
  - comparison_guardrails_partially_enabled
  - comparison_guardrails_blocked
- what the next narrow step is after this
- exact validation performed
- branch name
- full `git status --short --branch`
- commit hash
- whether files are staged and/or committed
- blockers, risks, or remaining gaps

If you hit a blocker, do not broaden into ROS, simulator redesign, or map-format work.
Stop at the narrowest real blocker and describe it clearly.
