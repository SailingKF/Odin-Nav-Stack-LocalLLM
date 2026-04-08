# Current Round Prompt

## Round
Round 044 - Report-Only Map Fallback And Latest Spot Persistence Baseline

## Goal
Now that the harness can render a truthful lightweight 2D validation map, make that map more robust when the live API is no longer reachable. The narrow target is to preserve enough compact route/progression context in persisted validation artifacts so the operator can still open the harness later and understand where the last validated run ended.

## Why This Is The Current Priority

Round 043 closed the first map-view gap:

- the harness can now show route POIs
- it can show a truthful current or last pose
- it can highlight triggered and narrated progression
- it does this without introducing a heavy map engine

But the latest real smoke still exposed a narrow remaining weakness:

- the map worked best while current API state was still reachable
- `validation_map_view.pose_source` was truthful
- but `latest_spot_name` was not yet a stable operator-facing fallback in the report-only path

The next highest-value step is therefore not a more complex map.
It is making the existing map trustworthy even after the stack has stopped.

## In Scope

- persist a compact latest-spot fallback in validation reports or equivalent harness-owned persisted state
- let `validation_map_view` use that persisted fallback when live API state is unavailable
- keep the persisted shape narrow:
  - latest spot id/name
  - any minimal progression fields needed to make the existing map/operator summary truthful
- update the harness summary so operators can still understand the last completed run after services stop
- add focused tests and docs

## Desired Outcome

At the end of this round, the repo should be in one of these honest states:

1. After a validation run completes and the local stack is stopped, the harness still renders a truthful lightweight 2D map and stable latest-spot summary from persisted artifacts alone.
2. The report-only fallback is partially implemented, but the exact remaining blocker is explicit.

## Out Of Scope

- new map engine or richer simulator visualization
- GIS / tile / occupancy-map work
- `/debug` redesign
- ROS 2 formal adapter
- simulator-side UI
- Isaac Sim
- Orin NX deployment work
- broader report analytics
- autonomous navigation/path planning

## Architecture Constraints

- keep this operator-facing and report-facing
- do not push map concerns into `core`
- do not duplicate route/POI truth in a second world model
- persist only the minimum additional state needed for truthful fallback
- prefer improving the existing harness/report seam over adding a new service

## Acceptance Criteria

- after a validation run, the harness can still build `validation_map_view` from persisted artifacts even when the API is no longer reachable
- latest spot identity is truthfully available in that fallback path
- focused tests pass
- existing related harness/report tests still pass

## Result Requirements

When done, update `coordination/latest_result.md` with:

- what you changed
- exact files changed
- what persisted fallback fields were added
- how the map now behaves when API state is absent
- whether latest spot identity is preserved truthfully
- exact commands used
- what operator fact was actually validated
- whether the round ended in:
  - report_only_map_fallback_enabled
  - report_only_map_fallback_partially_enabled
  - report_only_map_fallback_blocked
- what the next narrow step is after this
- exact validation performed
- branch name
- full `git status --short --branch`
- commit hash
- whether files are staged and/or committed
- blockers, risks, or remaining gaps

If you hit a blocker, do not broaden into simulator redesign or general reporting features.
Stop at the narrowest real blocker and describe it clearly.
