# Current Round Prompt

## Round
Round 036 - Live Second POI Progression And Minimal Multi-Stop Motion Baseline

## Goal
Now that a truthful first live MVSim-driven POI hit and first narration event have been validated, extend the live path just enough to produce a truthful second live POI hit and, ideally, a second live-triggered narration event.

## Why This Is The Current Priority

The project has now closed these live-MVSim uncertainties:

- MVSim runs inside WSL
- the minimal world launches
- live pose is extractable from MVSim
- live pose reaches the Windows-side `sim_pose_ingress`
- the first current POI can be hit truthfully
- the first live-triggered narration event can occur truthfully

The next real product question is:

- can the live simulator path progress beyond the first stop and produce a truthful second stop event without broadening into a full simulator redesign

This round should stay narrow:

- prefer minimal truthful motion/progression over broad simulator changes
- validate the second current POI if possible
- only claim multi-stop success for facts that are actually observed

## In Scope

- analyze the current live MVSim world/runtime behavior after the first stop
- choose the narrowest truthful strategy for second-stop progression, such as:
  - a minimal deterministic world motion path
  - a minimal controlled movement step already supported by MVSim
  - a small repo-local validation-world adjustment that enables progression from `East Gate` to `Central Plaza`
- keep the strategy explicit in docs/config
- validate through the existing Windows-side stack whether:
  - a truthful second live POI hit occurred
  - a truthful second live narration event occurred
- if a small additional step yields truthful third-stop hit or full route completion, that is acceptable, but not required
- update operator-facing summaries or harness surfaces if needed so the observed live progression truth is easy to read

## Desired Outcome

At the end of this round, the repo should be in one of these honest states:

1. A truthful second live POI hit occurred, and ideally a second narration event occurred.
2. A truthful second live POI hit did not occur, but the exact remaining motion/progression blocker is explicit.

What is not acceptable is implying "full live simulation" if only the first stop has actually been validated.

## Out Of Scope

- broad simulator redesign
- ROS 2 formal adapter
- general map-format or occupancy-map architecture
- autonomous navigation/path planning
- Isaac Sim
- Orin NX deployment work
- major UI redesign
- TTS/ASR expansion

## Architecture Constraints

- keep `core` platform-agnostic
- do not couple orchestrator/core directly to WSL or MVSim internals
- prefer the narrowest truthful motion/progression change over broad world/content refactors
- if adding live-validation-specific world behavior or assets, keep them explicit and isolated
- reuse existing live bridge, sim-ingress, API proxy, and validation surfaces where possible
- do not fake continuous motion with non-truthful summaries

## Acceptance Criteria

- the round either achieves a truthful second live POI hit or reports a precise remaining blocker
- if a second live narration event occurs, that fact is explicitly documented
- exact commands and observed outputs are documented
- operator/docs surfaces reflect the new truth about live multi-stop readiness
- focused tests still pass
- existing related tests still pass

## Result Requirements

When done, update `coordination/latest_result.md` with:

- what you changed
- exact files changed
- what motion/progression strategy was chosen
- whether a truthful second live POI hit occurred
- whether a truthful second live narration event occurred
- whether full live route completion occurred
- exact commands used
- what end-to-end live fact was actually validated
- whether the round ended in:
  - live_second_poi_enabled
  - live_second_poi_without_narration
  - live_second_progression_blocked
- what the next narrow step is after this
- exact validation performed
- branch name
- full `git status --short --branch`
- commit hash
- whether files are staged and/or committed
- blockers, risks, or remaining gaps

If you hit a blocker, do not expand scope into ROS, simulator redesign, or map-format work.
Stop at the narrowest real blocker and describe it clearly.
