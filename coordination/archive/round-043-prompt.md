# Current Round Prompt

## Round
Round 043 - Lightweight 2D Validation Map View Baseline

## Goal
Now that the PC-side validation flow is repeatable and exportable, add a lightweight 2D validation map view so an operator can see route POIs, current robot position, and recent progression visually instead of inferring everything from text summaries alone.

## Why This Is The Current Priority

The current validation tooling is already strong:

- the harness can run truthful live validation
- it can run compatibility replay
- it persists report artifacts
- it can compare live vs compatibility runs
- it can export the latest comparison in JSON and human-readable form

The next most valuable gap is visual comprehension:

- today the operator mostly reads text panels, status fields, and reports
- the project still lacks a minimal top-down visual validation surface for route/POI progression
- this is a better next step than continuing to stack more report/export utilities

This round should stay narrow:

- add a simple 2D validation map
- use existing route/POI/pose data only
- do not broaden into a general map-format or GIS system

## In Scope

- define a lightweight 2D map view contract using existing repo assets and existing runtime state
- show at least:
  - current route POIs
  - current/last pose
  - which POIs have been triggered or narrated recently
  - which validation mode is active
- prefer a simple schematic rendering:
  - SVG, canvas, or lightweight DOM rendering are all acceptable
- place it in the current operator-facing surface where it is most useful:
  - preferably the MVSim validation harness page
  - optionally also reusable from `/debug` if that falls out naturally without extra scope
- keep scaling/coordinate mapping explicit and small
- update docs and focused tests

## Desired Outcome

At the end of this round, the repo should be in one of these honest states:

1. The operator can open the harness and see a lightweight 2D validation map with truthful POI and pose state.
2. The map view is partially implemented but the exact remaining blocker is explicit.

What is not acceptable is introducing a heavy map architecture, generic scene engine, or occupancy-map framework.

## Out Of Scope

- general map-format architecture
- ROS 2 formal adapter
- simulator redesign
- autonomous navigation/path planning
- Isaac Sim
- Orin NX deployment work
- large UI redesign
- TTS/ASR expansion
- GIS tooling or tile systems

## Architecture Constraints

- keep `core` platform-agnostic
- keep rendering logic in the operator-facing service/UI layer
- reuse existing route, POI, and runtime state instead of inventing a parallel world model
- prefer a simple top-down schematic over realism
- keep coordinate normalization explicit and local to the view layer

## Acceptance Criteria

- the harness can show a lightweight 2D validation map without rerunning validation
- POIs and current/last pose are represented truthfully
- recent trigger/narration state is visually distinguishable
- focused tests still pass
- existing related tests still pass

## Result Requirements

When done, update `coordination/latest_result.md` with:

- what you changed
- exact files changed
- what 2D map rendering strategy was chosen
- what data sources drive the map
- whether the map reflects truthful POI and pose state
- how coordinate normalization/scaling is handled
- exact commands used
- what operator fact was actually validated
- whether the round ended in:
  - validation_map_view_enabled
  - validation_map_view_partially_enabled
  - validation_map_view_blocked
- what the next narrow step is after this
- exact validation performed
- branch name
- full `git status --short --branch`
- commit hash
- whether files are staged and/or committed
- blockers, risks, or remaining gaps

If you hit a blocker, do not broaden into ROS, simulator redesign, or map-format work.
Stop at the narrowest real blocker and describe it clearly.
