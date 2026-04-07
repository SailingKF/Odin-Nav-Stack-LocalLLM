# Current Round Prompt

## Round
Round 035 - Live Route Alignment And First Narration Trigger Baseline

## Goal
Now that a truthful live pose bridge exists from WSL MVSim into the current Windows-side `sim_pose_ingress`, align the minimal world/runtime path with the current route/POI contract closely enough to produce the first truthful live POI hit and the first live-triggered narration event.

## Why This Is The Current Priority

The current main unknown is no longer runtime availability or pose extraction.

Those are now sufficiently closed:

- MVSim runs in WSL
- the world launches
- live pose is extractable
- live pose reaches the current `sim_pose_ingress`

The next real product question is:

- can a real live simulator progression now trigger a real POI and produce a narration event in the current stack

This round should stay narrow:

- align the live path to hit one POI truthfully
- validate one live narration event
- do not broaden into full route completion unless it falls out naturally with small additional work

## In Scope

- analyze the mismatch between:
  - current live MVSim start pose / motion behavior
  - current route/POI coordinates
- choose the narrowest truthful alignment strategy, such as:
  - adjusting the minimal world initial pose
  - adjusting the minimal world geometry/pose progression
  - adding a minimal controlled movement step in MVSim if already naturally supported
  - or introducing a sim-profile-specific route/POI asset that is explicitly for live MVSim validation
- keep the alignment strategy explicit and honest in docs/config
- validate at least one live POI hit and one live-triggered narration event through the existing Windows-side stack
- if a tiny amount of extra work enables a second POI or short live route progression, that is acceptable
- update operator/docs surfaces so they can show or summarize:
  - live pose bridge working
  - first POI hit
  - narration triggered

## Desired Outcome

At the end of this round, the repo should be in one of these honest states:

1. A real live MVSim-driven pose progression triggers at least one current POI and produces one narration event.
2. Live pose reaches the stack, but a precise remaining alignment blocker is explicitly identified.

What is not acceptable is staying at "last_pose updates" without trying to close the next product-level event boundary.

## Out Of Scope

- full route completion if it requires broader redesign
- ROS 2 formal adapter
- simulator redesign
- map-format or occupancy-map architecture
- autonomous navigation/path planning
- Isaac Sim
- Orin NX packaging
- major UI redesign
- TTS/ASR expansion

## Architecture Constraints

- keep `core` platform-agnostic
- do not couple orchestrator/core directly to WSL or MVSim internals
- prefer the narrowest truthful alignment change over broad world/content refactors
- if introducing sim-specific POI/route assets, keep them explicit and isolated
- reuse existing live bridge, sim-ingress, and validation surfaces where possible
- keep the bundle coherent and event-focused

## Acceptance Criteria

- the round either achieves a truthful first live POI hit and narration event, or reports a precise remaining blocker
- exact commands and observed outputs are documented
- operator/docs surfaces reflect the new truth about live progression readiness
- focused tests still pass
- existing related tests still pass

## Result Requirements

When done, update `coordination/latest_result.md` with:

- what you changed
- exact files changed
- what alignment strategy was chosen
- whether a live POI hit occurred
- whether a live narration event occurred
- exact commands used
- what end-to-end live fact was actually validated
- whether the round ended in:
  - live_first_narration_enabled
  - live_poi_hit_without_narration
  - live_alignment_blocked
- what the next narrow step is after this
- exact validation performed
- branch name
- full `git status --short --branch`
- commit hash
- whether files are staged and/or committed
- blockers, risks, or remaining gaps

If you hit a blocker, do not expand scope into ROS, simulator redesign, or map-format work.
Stop at the narrowest real blocker and describe it clearly.
