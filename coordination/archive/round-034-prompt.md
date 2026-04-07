# Current Round Prompt

## Round
Round 034 - MVSim Live Pose Surface Discovery And Minimal Bridge Baseline

## Goal
Now that a real MVSim runtime and world launch exist in Ubuntu/WSL, identify the smallest reliable live pose output surface from the running MVSim process and establish the first minimal bridge path into the existing Windows-side `sim_pose_ingress` flow.

## Why This Is The Current Priority

The base runtime question is now closed enough for the next step:

- MVSim runs inside WSL
- the repo-local world launches
- the current remaining gap is no longer installation

The next real unknown is:

- how do we extract live pose from the running Linux-side MVSim process in the narrowest reliable way
- and how do we route that live pose into the current Windows-side tour-validation stack without broadening into ROS or simulator redesign

This round should stay narrow and honest:

- first discover the live pose surface
- then prove a minimal bridge
- not yet “full live guided tour completion” unless that falls out naturally with small additional work

## In Scope

- inspect the running Linux-side MVSim runtime for the smallest viable live pose output surface
  - CLI topic inspection
  - runtime messaging surface
  - published pose topic/telemetry
  - any other minimal built-in mechanism
- document the actual live pose/output contract observed from the current world/runtime
- add a narrow bridge path that can consume that live pose surface and transform it into the existing `sim_pose_ingress`-compatible shape
- it is acceptable if the first bridge runs from:
  - WSL to Windows
  - or Windows calling into WSL
  as long as it is explicit and reproducible
- reuse existing projection/transform/HTTP ingress seams where practical
- prove at least one truthful end-to-end fact:
  - a live pose sample from the real running MVSim world reaches the current sim-ingress path
- if a tiny amount of extra work enables a short live-driven route progression, that is acceptable
- update operator/docs surfaces so they distinguish:
  - runtime available
  - live pose surface discovered
  - live bridge working or blocked

## Desired Outcome

At the end of this round, the repo should be in one of these honest states:

1. A real live pose surface from MVSim has been identified and at least minimally bridged into the current sim-ingress flow.
2. MVSim runtime is healthy, but live pose extraction or cross-boundary bridging is blocked by a precise technical issue that is now explicitly identified.

What is not acceptable is staying at “runtime launches” without investigating the next actual integration seam.

## Out Of Scope

- ROS 2 formal adapter
- broad simulator redesign
- map-format or occupancy-map design
- autonomous navigation/path planning
- Isaac Sim
- Orin NX packaging
- major UI redesign
- TTS/ASR expansion

## Architecture Constraints

- keep `core` platform-agnostic
- do not couple orchestrator/core directly to WSL or MVSim-specific internals
- keep simulator-specific logic in adapters/services/scripts/docs
- reuse current sim-ingress, publisher, projection, and validation-harness seams where possible
- prefer one narrow truthful live bridge over a large abstraction rewrite
- keep the bundle coherent and integration-focused

## Acceptance Criteria

- the round identifies a real live pose/output surface from the WSL MVSim runtime
- that surface is documented concretely
- a minimal bridge into the current sim-ingress path exists, or a precise blocker is reported
- exact commands and observed outputs are documented
- operator/docs surfaces reflect the new truth about live bridge readiness
- focused tests still pass
- existing related tests still pass

## Result Requirements

When done, update `coordination/latest_result.md` with:

- what you changed
- exact files changed
- what live pose/output surface was discovered
- exact commands used to inspect or consume that surface
- whether a minimal live bridge into `sim_pose_ingress` now works
- what end-to-end live fact was actually validated
- whether the round ended in:
  - live_pose_bridge_enabled
  - live_pose_surface_found_but_bridge_blocked
  - live_pose_surface_blocked
- what the next narrow step is after this
- exact validation performed
- branch name
- full `git status --short --branch`
- commit hash
- whether files are staged and/or committed
- blockers, risks, or remaining gaps

If you hit a blocker, do not expand scope into ROS, simulator redesign, or map-format work.
Stop at the narrowest real blocker and describe it clearly.
