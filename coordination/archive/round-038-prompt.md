# Current Round Prompt

## Round
Round 038 - Harness Validation Report Artifact And Run History Baseline

## Goal
Now that the MVSim validation harness can truthfully run both `live_runtime` and `compatibility_shim` on an isolated local stack, make each run leave behind a clear operator-facing validation artifact that can be inspected later without replaying the whole session.

## Why This Is The Current Priority

The core operator repeatability gap is now closed:

- the harness can start its own isolated stack
- the harness can run truthful live MVSim validation
- the harness can also run compatibility replay

The next most valuable gap is evidence and comparison:

- after a run finishes, the operator still relies mostly on the live page response
- there is not yet a clearly defined per-run validation artifact / report surface for later inspection
- future simulator, edge, and hardware work will benefit from having stable run summaries to compare against

This round should make the harness produce and expose a concise, durable report of what actually happened in each validation run.

## In Scope

- define a narrow validation-report artifact shape for harness runs
- persist one report per validation run in a clear repo-local location
- include truthful essentials such as:
  - timestamp
  - validation mode
  - config path or config identity
  - whether the run passed
  - first/second stop truth
  - route completion truth
  - recent triggered/narrated spots
  - relevant URLs or session identifiers when useful
- expose the latest report and, if small and natural, a short recent-history list through the harness API/UI
- keep compatibility and live runs clearly distinguishable in the artifact
- update docs and focused tests

## Desired Outcome

At the end of this round, the repo should be in one of these honest states:

1. Every harness validation run leaves behind a durable, operator-readable report artifact, and the harness can show the latest report without replaying the run.
2. Report persistence is partially working but a precise remaining blocker is explicit.

What is not acceptable is turning the harness into a heavy supervisor or generic database system.

## Out Of Scope

- ROS 2 formal adapter
- simulator redesign
- map-format architecture
- autonomous navigation/path planning
- Isaac Sim
- Orin NX deployment work
- large UI redesign
- TTS/ASR expansion
- general analytics platform work

## Architecture Constraints

- keep `core` platform-agnostic
- keep validation-report persistence in service/operator-facing layers
- do not turn this into a generic telemetry warehouse
- prefer simple file-backed artifacts and clear contracts
- keep live and compatibility truth claims explicit
- reuse existing session/harness information where possible rather than duplicating state machines

## Acceptance Criteria

- a completed harness validation run produces a durable report artifact
- the harness can show the latest report without rerunning validation
- if recent-history support is added, it remains small and clearly scoped
- focused tests still pass
- existing related tests still pass

## Result Requirements

When done, update `coordination/latest_result.md` with:

- what you changed
- exact files changed
- what validation-report strategy was chosen
- where report artifacts are stored
- what the report includes
- whether both live and compatibility runs produce truthful artifacts
- exact commands used
- what operator fact was actually validated
- whether the round ended in:
  - harness_report_artifacts_enabled
  - harness_report_artifacts_partially_enabled
  - harness_report_artifacts_blocked
- what the next narrow step is after this
- exact validation performed
- branch name
- full `git status --short --branch`
- commit hash
- whether files are staged and/or committed
- blockers, risks, or remaining gaps

If you hit a blocker, do not broaden into ROS, simulator redesign, or map-format work.
Stop at the narrowest real blocker and describe it clearly.
