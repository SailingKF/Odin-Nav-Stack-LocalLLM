# Current Round Result

## Round
Round 043 - Lightweight 2D Validation Map View Baseline

## Summary

- Status: `validation_map_view_enabled`
- This round added a lightweight 2D validation map to the MVSim harness.
- The chosen rendering strategy is:
  - top-down schematic SVG
  - route/POI geometry loaded from the existing repo content files
  - current or last pose overlaid from truthful runtime/report state
  - trigger/narration progression highlighted with simple visual states
- The implementation stayed local to the operator-facing harness layer and did not introduce a general map framework.

## What I Changed

- Added a dedicated harness-side map payload builder:
  - `services/mvsim_validation_harness/map_view.py`
- Extended harness runtime status so it now emits:
  - `validation_map_view`
  - `services/mvsim_validation_harness/runtime.py`
- Added a narrow API-state probe in the harness runtime so the map can prefer current pose without rerunning validation:
  - `services/mvsim_validation_harness/runtime.py`
- Extended persisted validation reports so they now keep:
  - `latest_pose`
  - `services/mvsim_validation_harness/reporting.py`
- Extended the human-readable comparison export so compact report summaries also surface the latest persisted pose:
  - `services/mvsim_validation_harness/reporting.py`
- Added a new `Validation Map` panel to the harness page:
  - route polyline
  - POI markers
  - pose marker
  - compact legend
  - `services/mvsim_validation_harness/static/index.html`
- Added focused tests for:
  - map payload building
  - report latest-pose persistence
  - harness status/page expectations
  - `tests/test_mvsim_validation_map_view.py`
  - `tests/test_mvsim_validation_reporting.py`
  - `tests/test_mvsim_validation_harness.py`
- Updated docs:
  - `README.md`
  - `docs/MVSIM_VALIDATION_HARNESS.md`

## Exact Files Changed

- `README.md`
- `docs/MVSIM_VALIDATION_HARNESS.md`
- `services/mvsim_validation_harness/map_view.py`
- `services/mvsim_validation_harness/reporting.py`
- `services/mvsim_validation_harness/runtime.py`
- `services/mvsim_validation_harness/static/index.html`
- `tests/test_mvsim_validation_map_view.py`
- `tests/test_mvsim_validation_harness.py`
- `tests/test_mvsim_validation_reporting.py`
- `coordination/latest_result.md` updated locally after commit only, not staged

## What 2D Map Rendering Strategy Was Chosen

Chosen strategy:

- render a lightweight top-down SVG directly in the existing `/harness` page
- keep coordinate normalization local to the harness view layer
- load route order and POI positions from the existing repo content files
- use simple visual states only:
  - `pending`
  - `triggered`
  - `narrated`
  - `active`
- use one pose marker for current or last known pose
- avoid any scene engine, simulator-side rendering, GIS, or occupancy-map abstraction

## What Data Sources Drive The Map

The current map payload is built from:

1. route file:
   - `current_route_file`
   - currently `content/routes/demo_route.yaml`
2. POI file:
   - `current_poi_file`
   - currently `content/poi/demo_pois.yaml`
3. progression state:
   - latest persisted harness report when available
   - fallback to `last_validation_result.live_validation_summary`
   - fallback to `last_validation_result.api_latest_session`
4. pose state:
   - prefer current reachable API `/state.last_pose`
   - otherwise use `last_validation_result.api_state.last_pose`
   - otherwise use `last_validation_result.sim_ingress_state.last_pose`
   - otherwise use persisted `latest_report.latest_pose`

## Whether The Map Reflects Truthful POI And Pose State

Yes, within the narrow contract implemented this round.

Truthfulness rules:

- POI geometry comes from the same repo route/POI content used by the current tour flow
- trigger/narration highlighting comes from validation/runtime/report truth, not UI-only memory
- the pose marker is only rendered when a truthful current or persisted pose exists
- if no pose is available, the map reports that explicitly instead of inventing one

Real smoke from this round showed:

- `map_status = "ready"`
- `map_mode = "compatibility_shim"`
- `map_pose_source = "api_state"`
- `map_progress_source = "latest_report"`
- `map_pose = { "x": 9.5, "y": -0.5, "label": "gallery_inside" }`
- `map_triggered = ["gate", "plaza", "gallery"]`
- `map_narrated = ["gate", "plaza", "gallery"]`
- `pose_is_truthful = true`

## How Coordinate Normalization / Scaling Is Handled

Scaling is explicit and local to the harness view payload:

- collect all route POI world coordinates
- include the current/last pose if one exists
- compute padded world bounds
- map those bounds into a fixed SVG view box:
  - width `100`
  - height `64`
  - padding `8`
- invert the screen Y axis relative to world-positive-up

The payload now exposes:

- `view_box`
- `world_bounds`
- `normalization`

So the rendering layer does not hide how screen coordinates are derived.

## Exact Commands Used

### Focused tests

```text
python -m unittest tests.test_mvsim_validation_map_view -v
python -m unittest tests.test_mvsim_validation_reporting -v
python -m unittest tests.test_mvsim_validation_harness -v
```

### Full regression

```text
python -m unittest discover -s tests
```

### Real harness smoke

Start harness on an isolated port:

```text
python scripts/run_mvsim_validation_harness.py --config configs/sim_harness.yaml --host 127.0.0.1 --port 8312
```

Then drive the current operator flow:

```text
GET  http://127.0.0.1:8312/health
GET  http://127.0.0.1:8312/harness
POST http://127.0.0.1:8312/services/start
POST http://127.0.0.1:8312/validation/run
GET  http://127.0.0.1:8312/status
GET  http://127.0.0.1:8312/reports/latest
POST http://127.0.0.1:8312/services/stop
```

The validation request used:

```json
{
  "validation_mode": "compatibility_shim",
  "question": "What does this final stop prove?"
}
```

## What Operator Fact Was Actually Validated

The real operator fact validated this round is:

- after a harness validation run completes, an operator can refresh `/status` and the harness still has enough truthful route/POI/progression/pose state to render a compact 2D map without rerunning validation immediately

What was actually observed:

- `/harness` returned `200`
- validation completed with:
  - `validation_status = "passed"`
  - `validation_mode = "compatibility_shim"`
  - `route_completed = true`
- latest report persisted as:
  - `20260406T143649Z-compatibility_shim`
- subsequent `/status.validation_map_view` returned:
  - `status = "ready"`
  - `active_validation_mode = "compatibility_shim"`
  - `pose_source = "api_state"`
  - `progress_source = "latest_report"`
  - all three demo POIs in both triggered and narrated progression sets

## Whether The Round Ended In `validation_map_view_enabled`, `validation_map_view_partially_enabled`, Or `validation_map_view_blocked`

This round ended in:

- `validation_map_view_enabled`

## What The Next Narrow Step Is After This

The next narrow step is:

1. persist one compact `latest_spot_id` / `latest_spot_name` fallback path for the map when current API state is gone and only a report remains
2. optionally surface the same map payload in the sim-profile `/debug` page if it falls out cleanly without duplicating logic
3. keep resisting any general map engine or simulator-side UI expansion

## Exact Validation Performed

### Focused unit validation

- `python -m unittest tests.test_mvsim_validation_map_view -v`
  - passed
- `python -m unittest tests.test_mvsim_validation_reporting -v`
  - passed
- `python -m unittest tests.test_mvsim_validation_harness -v`
  - passed

### Full regression validation

- `python -m unittest discover -s tests`
  - passed
  - `Ran 130 tests ... OK`

### Real harness smoke

- launched:
  - `python scripts/run_mvsim_validation_harness.py --config configs/sim_harness.yaml --host 127.0.0.1 --port 8312`
- observed:
  - `GET /health` returned `status = "ok"`
  - `GET /harness` returned `200`
  - `POST /services/start` succeeded
  - `POST /validation/run` returned `status = "passed"`
  - `GET /status` returned a populated `validation_map_view`
  - `GET /reports/latest` returned the new latest report
  - `POST /services/stop` stopped:
    - `sim_pose_ingress_server`
    - `api_server`

## Current Branch

- `main`

## Full `git status --short --branch`

```text
## main...origin/main [ahead 45]
 M docs/DEV_WORKFLOW.md
?? coordination/
?? tmp_mvsim_harness_smoke/
?? tmp_mvsim_live_bridge_smoke/
?? tmp_mvsim_runtime_attempt/
```

## Commit Hash

- `17ffdec730d12e4d1bf283354598917c1f91ac07`

## Whether Files Are Staged And/Or Committed

- repo code/doc bundle for Round 043:
  - committed
- currently staged:
  - no
- `coordination/latest_result.md`:
  - updated locally
  - not staged
  - not committed

## Blockers, Risks, Or Remaining Gaps

- the current smoke proved truthful pose/progression rendering with the API still reachable; if only an older pre-Round-043 report exists, pose fallback may still be absent until a newer report is generated
- the map remains intentionally schematic and not spatially realistic beyond POI/pose relative layout
- current map detail uses latest route/POI content files only; it does not attempt to visualize arbitrary simulator geometry
- `docs/DEV_WORKFLOW.md` still has a separate pre-existing local modification outside this round
- temp smoke directories remain untracked and were intentionally not included in the commit
