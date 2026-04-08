# Current Round Result

## Round
Round 044 - Report-Only Map Fallback And Latest Spot Persistence Baseline

## Summary

- Status: `report_only_map_fallback_enabled`
- This round tightened the persisted fallback behind the existing harness validation map.
- The chosen strategy was:
  - keep the map view in the harness layer
  - persist only minimal latest-stop fallback state into validation reports
  - let the map recover latest spot identity and pose from the latest report when live API state is gone
- No new service or broader reporting system was introduced.

## What I Changed

- Added a compact latest-stop fallback to persisted validation reports:
  - `latest_spot_id`
  - `latest_spot_name` when directly available at validation time
  - `services/mvsim_validation_harness/reporting.py`
- Tightened report generation so latest-stop fallback is derived from the smallest truthful sources already present:
  - `api_latest_session.latest_spot_id`
  - `latest_narrated_spot_id`
  - `latest_triggered_spot_id`
  - `live_validation_summary.validated_spot_id`
  - recent narrated / triggered spot ids as final fallback
  - `services/mvsim_validation_harness/reporting.py`
- Updated the map payload builder so it can now:
  - use `latest_report.latest_spot_id`
  - resolve `latest_spot_name` from the current POI file when only the id is persisted
  - continue to prefer live API state when available
  - `services/mvsim_validation_harness/map_view.py`
- Updated the harness page so operators can still see latest-stop summary after the stack has stopped:
  - summary panel now falls back to persisted latest spot
  - validation panel now includes `Persisted Latest Spot`
  - latest report panel now shows latest spot id/name
  - `services/mvsim_validation_harness/static/index.html`
- Extended focused tests for:
  - report-derived latest spot fallback
  - report-only map rendering path
  - harness page/status expectations
  - `tests/test_mvsim_validation_reporting.py`
  - `tests/test_mvsim_validation_map_view.py`
  - `tests/test_mvsim_validation_harness.py`
- Updated docs:
  - `README.md`
  - `docs/MVSIM_VALIDATION_HARNESS.md`

## Exact Files Changed

- `README.md`
- `docs/MVSIM_VALIDATION_HARNESS.md`
- `services/mvsim_validation_harness/map_view.py`
- `services/mvsim_validation_harness/reporting.py`
- `services/mvsim_validation_harness/static/index.html`
- `tests/test_mvsim_validation_harness.py`
- `tests/test_mvsim_validation_map_view.py`
- `tests/test_mvsim_validation_reporting.py`
- `coordination/latest_result.md` updated locally after commit only, not staged

## What Persisted Fallback Fields Were Added

The report now persists these compact latest-stop fallback fields:

- `latest_spot_id`
- `latest_spot_name`

The persisted report already had:

- `latest_pose`
- `recent_triggered_spot_ids`
- `recent_narrated_spot_ids`

Together these are now enough for the harness map to recover:

- the latest stop identity
- the last pose
- the recent progression state

without needing a live API connection.

## How The Map Now Behaves When API State Is Absent

Current precedence is now:

1. prefer live API state while reachable
2. otherwise use the in-memory `last_validation_result` if still present in the current harness process
3. otherwise use the latest persisted validation report

The most important new behavior is:

- even after the local stack stops and the harness process is restarted, `validation_map_view` can now rebuild from `latest_report` alone

Current report-only fallback behavior:

- pose comes from `latest_report.latest_pose`
- progression comes from:
  - `latest_report.recent_triggered_spot_ids`
  - `latest_report.recent_narrated_spot_ids`
- latest stop identity comes from:
  - `latest_report.latest_spot_id`
  - `latest_report.latest_spot_name`
  - if only the id exists, the harness resolves the name from the repo POI file

## Whether Latest Spot Identity Is Preserved Truthfully

Yes.

This round now preserves latest stop identity truthfully in the report-only path.

Real observed persisted report after validation:

- `latest_report_spot_id = "gallery"`
- `latest_report_spot_name = "History Gallery"`

Real observed report-only map state after restarting the harness process and keeping the API stack down:

- `second_map_pose_source = "latest_report"`
- `second_map_progress_source = "latest_report"`
- `second_latest_spot_id = "gallery"`
- `second_latest_spot_name = "History Gallery"`

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

### Real validation run with stop

```text
python scripts/run_mvsim_validation_harness.py --config configs/sim_harness.yaml --host 127.0.0.1 --port 8313
POST http://127.0.0.1:8313/services/start
POST http://127.0.0.1:8313/validation/run
POST http://127.0.0.1:8313/services/stop
GET  http://127.0.0.1:8313/status
```

### Stricter report-only restart validation

First process:

```text
python scripts/run_mvsim_validation_harness.py --config configs/sim_harness.yaml --host 127.0.0.1 --port 8314
POST http://127.0.0.1:8314/services/start
POST http://127.0.0.1:8314/validation/run
POST http://127.0.0.1:8314/services/stop
```

Then stop that harness process entirely.

Second fresh process:

```text
python scripts/run_mvsim_validation_harness.py --config configs/sim_harness.yaml --host 127.0.0.1 --port 8315
GET http://127.0.0.1:8315/status
```

This second process was the key proof that the fallback is now report-only rather than in-memory only.

## What Operator Fact Was Actually Validated

The truthful operator fact validated this round is:

- after a validation run completes, the local stack can be stopped and the harness can even be restarted, and the operator still gets a truthful latest-stop summary plus a usable 2D validation map from persisted artifacts alone

What was actually observed in the stricter restart validation:

- first harness process:
  - validation passed
  - route completed
  - services stopped
- second fresh harness process:
  - `validation_map_view.status = "ready"`
  - `validation_map_view.data_sources.pose_source = "latest_report"`
  - `validation_map_view.data_sources.progress_source = "latest_report"`
  - `validation_map_view.latest_spot_id = "gallery"`
  - `validation_map_view.latest_spot_name = "History Gallery"`
  - `validation_map_view.pose.world = { "x": 9.5, "y": -0.5, "label": "gallery_inside" }`

## Whether The Round Ended In `report_only_map_fallback_enabled`, `report_only_map_fallback_partially_enabled`, Or `report_only_map_fallback_blocked`

This round ended in:

- `report_only_map_fallback_enabled`

## What The Next Narrow Step Is After This

The next narrow step is:

1. add one compact persisted field describing whether the latest spot was last triggered vs last narrated, if that distinction becomes operator-important
2. keep the fallback narrow and resist turning the report into a broader analytics/event model
3. only consider `/debug` reuse if it can share the same map payload without duplicating logic

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
  - `Ran 132 tests ... OK`

### Real smoke: stop local stack, keep harness alive

- validation mode:
  - `compatibility_shim`
- observed:
  - `validation_status = "passed"`
  - `route_completed = true`
  - services stopped:
    - `sim_pose_ingress_server`
    - `api_server`
  - post-stop map still had:
    - `latest_spot_id_after_stop = "gallery"`
    - `latest_spot_name_after_stop = "History Gallery"`

### Real smoke: stop local stack and restart harness process

- first harness process:
  - validation passed
  - route completed
  - services stopped
- second fresh harness process:
  - `second_map_status = "ready"`
  - `second_map_pose_source = "latest_report"`
  - `second_map_progress_source = "latest_report"`
  - `second_latest_spot_id = "gallery"`
  - `second_latest_spot_name = "History Gallery"`
  - `second_latest_pose = { "x": 9.5, "y": -0.5, "label": "gallery_inside" }`

## Current Branch

- `main`

## Full `git status --short --branch`

```text
## main...origin/main [ahead 46]
 M docs/DEV_WORKFLOW.md
?? coordination/
?? tmp_mvsim_harness_smoke/
?? tmp_mvsim_live_bridge_smoke/
?? tmp_mvsim_runtime_attempt/
```

## Commit Hash

- `21f372d64a20ba968dce2c8fcb705c403049e97e`

## Whether Files Are Staged And/Or Committed

- repo code/doc bundle for Round 044:
  - committed
- currently staged:
  - no
- `coordination/latest_result.md`:
  - updated locally
  - not staged
  - not committed

## Blockers, Risks, Or Remaining Gaps

- the persisted fallback is intentionally narrow and does not preserve a fuller “why this was the latest stop” event history
- if both persisted `latest_spot_name` and route/POI asset resolution fail, the operator may still only see the latest stop id
- the map can now survive API absence, but it still assumes the current route/POI content files remain aligned with the validation asset identity described by the report
- `docs/DEV_WORKFLOW.md` still has a separate pre-existing local modification outside this round
- temp smoke directories remain untracked and were intentionally not included in the commit
