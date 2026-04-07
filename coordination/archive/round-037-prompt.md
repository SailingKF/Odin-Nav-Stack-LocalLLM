# Current Round Prompt

## Round
Round 037 - Live MVSim Harness Mode And Port-Isolated Validation Baseline

## Goal
Now that a truthful live MVSim multistop path has been validated, make that path operator-usable from the repo validation harness without requiring manual multi-process orchestration or dependence on a globally free default API port.

## Why This Is The Current Priority

The project has now already closed the core live-simulation proof:

- MVSim runs in WSL
- a real live pose stream reaches the Windows-side stack
- truthful POI hits and narrations occur
- the current route can complete truthfully in an isolated validation asset

The main remaining gap is not simulator truth anymore. It is operator repeatability:

- the live path is still driven through manual commands rather than a first-class harness flow
- `8000` is not reliably free on this machine, so operator validation should not depend on default-port luck

The next most valuable step is to turn the already-proven live path into a clear, isolated, repeatable harness mode.

## In Scope

- extend the MVSim validation harness so it can explicitly distinguish:
  - compatibility-shim validation
  - live MVSim validation
- add a live-validation path that reuses the existing truthful live bridge/runtime surfaces
- avoid changing `core` or simulator truth claims; focus on operator entry and repeatability
- provide a narrow way for the harness to use a port-isolated local stack for validation, such as:
  - a dedicated harness config variant
  - explicit local override ports
  - or another small isolated mechanism
- ensure the harness surfaces the truthful live result summary, including:
  - first stop hit
  - second stop hit
  - route completion
  - whether the validation used compatibility or live mode
- keep the existing compatibility path working

## Desired Outcome

At the end of this round, the repo should be in one of these honest states:

1. A user can open the harness and run a truthful live MVSim validation flow without manually stitching together multiple processes and without depending on the global default API port.
2. The live harness path is still blocked, but the exact operator/runtime blocker is explicit and narrow.

What is not acceptable is keeping the live path technically proven but still operationally awkward.

## Out Of Scope

- ROS 2 formal adapter
- simulator redesign
- map-format architecture
- autonomous navigation/path planning
- Isaac Sim
- Orin NX deployment work
- major UI redesign
- TTS/ASR expansion

## Architecture Constraints

- keep `core` platform-agnostic
- do not couple orchestrator/core directly to WSL or MVSim internals
- treat the harness as an operator-facing service layer, not as a place to hide simulator truth
- keep compatibility and live validation modes explicit rather than silently switching behavior
- prefer an isolated port/config solution over mutating unrelated global defaults

## Acceptance Criteria

- the harness can truthfully run or orchestrate the live MVSim validation path, or reports a precise blocker
- the harness clearly indicates whether the current validation ran in compatibility or live mode
- the live validation path no longer depends on manual command choreography for normal operator use
- focused tests still pass
- existing related tests still pass

## Result Requirements

When done, update `coordination/latest_result.md` with:

- what you changed
- exact files changed
- what harness/live-mode strategy was chosen
- how port isolation was handled
- whether the harness can truthfully run the live MVSim path end to end
- whether compatibility mode still works
- exact commands used
- what end-to-end operator fact was actually validated
- whether the round ended in:
  - live_harness_mode_enabled
  - live_harness_mode_partially_enabled
  - live_harness_mode_blocked
- what the next narrow step is after this
- exact validation performed
- branch name
- full `git status --short --branch`
- commit hash
- whether files are staged and/or committed
- blockers, risks, or remaining gaps

If you hit a blocker, do not broaden into ROS, simulator redesign, or map-format work.
Stop at the narrowest real blocker and describe it clearly.
