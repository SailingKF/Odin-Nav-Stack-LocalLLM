# Current Round Result

## Round
Round 039 - Harness Live Vs Compatibility Comparison Summary Baseline

## Summary

- Status: `harness_comparison_summary_enabled`
- This round added a compact latest live-vs-compatibility comparison surface on top of the persisted harness report artifacts.
- The chosen strategy was:
  - compare persisted report artifacts only
  - compare the latest available `live_runtime` report against the latest available `compatibility_shim` report
  - keep the comparison concise and operator-focused
- The harness can now return that comparison without rerunning validation.
- Missing-report cases are explicit and readable.

## What I Changed

- Extended the report layer with a compact latest-mode comparison builder:
  - `services/mvsim_validation_harness/reporting.py`
- Added store support for reading the latest report by validation mode:
  - `services/mvsim_validation_harness/reporting.py`
- Exposed the latest comparison through the harness runtime status:
  - `services/mvsim_validation_harness/runtime.py`
- Added a dedicated comparison API surface:
  - `GET /reports/compare`
  - `services/mvsim_validation_harness/app.py`
- Added a compact comparison card to the harness page:
  - `services/mvsim_validation_harness/static/index.html`
- Added focused comparison tests:
  - `tests/test_mvsim_validation_reporting.py`
  - `tests/test_mvsim_validation_harness.py`
- Updated operator docs:
  - `docs/MVSIM_VALIDATION_REPORTS.md`
  - `docs/MVSIM_VALIDATION_HARNESS.md`
  - `README.md`

## Exact Files Changed

- `README.md`
- `docs/MVSIM_VALIDATION_HARNESS.md`
- `docs/MVSIM_VALIDATION_REPORTS.md`
- `services/mvsim_validation_harness/app.py`
- `services/mvsim_validation_harness/reporting.py`
- `services/mvsim_validation_harness/runtime.py`
- `services/mvsim_validation_harness/static/index.html`
- `tests/test_mvsim_validation_harness.py`
- `tests/test_mvsim_validation_reporting.py`
- `coordination/latest_result.md` updated locally after commit only, not staged

## Comparison Strategy Chosen

Chosen strategy:

- read the latest available persisted `live_runtime` report
- read the latest available persisted `compatibility_shim` report
- build one compact comparison summary from those two reports only

What that means:

- no rerun of either validation path
- no use of raw event logs
- no generic historical analytics system
- live and compatibility truths remain explicit and separate

## What Fields Are Compared

Current high-signal compared fields include:

- pass/fail
- route completion
- first live POI hit truth
- second live POI hit truth
- recent triggered spots
- recent narrated spots
- latest spot name
- compact report identity fields through:
  - report id
  - created_at
  - config_name
  - report_path

The comparison also returns:

- `status`
- `comparison_available`
- `missing_modes`
- compact report views for:
  - `live_runtime_report`
  - `compatibility_shim_report`
- `differences`

## Whether The Harness Can Now Compare Latest Live And Compatibility Runs

Yes.

Truthful observed facts from the real smoke:

- `GET /reports/compare` returned:
  - `status = "ready"`
  - `missing_modes = []`
- the returned comparison pointed to:
  - latest live report id:
    - `20260406T125557Z-live_runtime`
  - latest compatibility report id:
    - `20260406T125602Z-compatibility_shim`
- the comparison also truthfully showed:
  - `triggered_spots_equal = true`
  - `narrated_spots_equal = true`
  - `latest_spot_name_equal = true`

## How Missing-Report Cases Are Represented

Missing-report cases are explicit through:

- `status: "missing_reports"`
- `comparison_available: false`
- `missing_modes`

Examples:

- if no recent live report exists:
  - `missing_modes = ["live_runtime"]`
- if no recent compatibility report exists:
  - `missing_modes = ["compatibility_shim"]`

This behavior is covered by focused tests.

## Exact Commands Used

### Focused tests

```text
python -m unittest tests.test_mvsim_validation_reporting -v
python -m unittest tests.test_mvsim_validation_harness -v
python -m unittest tests.test_api_server -v
```

### Full regression

```text
python -m unittest discover -s tests
```

### Real harness operator validation

Start the harness:

```text
python scripts/run_mvsim_validation_harness.py --config configs/sim_harness.yaml --host 127.0.0.1 --port 8303
```

Run live and compatibility validations:

```text
POST http://127.0.0.1:8303/services/start
{"validation_mode":"live_runtime"}

POST http://127.0.0.1:8303/validation/run
{"validation_mode":"live_runtime","question":"What does this final stop prove?"}

POST http://127.0.0.1:8303/validation/run
{"validation_mode":"compatibility_shim","question":"What does this final stop prove?"}
```

Read the comparison without rerunning validation:

```text
GET http://127.0.0.1:8303/reports/compare
```

## What Operator Fact Was Actually Validated

The truthful operator fact validated in this round is:

- once the harness has persisted at least one live report and one compatibility report, the operator can ask the harness for a concise latest live-vs-compatibility summary
- that summary is built from persisted report artifacts only
- the operator does not need to rerun either validation path to inspect the comparison

## Whether The Round Ended In `harness_comparison_summary_enabled`, `harness_comparison_summary_partially_enabled`, Or `harness_comparison_summary_blocked`

This round ended in:

- `harness_comparison_summary_enabled`

## What The Next Narrow Step Is After This

The next narrow step is:

1. if useful later, add a tiny "comparison changed vs previous pair" signal without broadening into history analytics
2. optionally expose a one-click export of the latest comparison summary
3. keep future comparison logic report-driven and compact

## Exact Validation Performed

### Focused unit validation

- `python -m unittest tests.test_mvsim_validation_reporting -v`
  - passed
- `python -m unittest tests.test_mvsim_validation_harness -v`
  - passed
- `python -m unittest tests.test_api_server -v`
  - passed

### Full regression validation

- `python -m unittest discover -s tests`
  - passed
  - `Ran 122 tests ... OK`

### Real harness operator smoke

- launched:
  - `python scripts/run_mvsim_validation_harness.py --config configs/sim_harness.yaml --host 127.0.0.1 --port 8303`
- observed before rerunning any path in that harness process:
  - `GET /reports/compare`
  - `status = "ready"`
  - `missing_modes = []`
- observed after creating a fresh live + compatibility pair:
  - live report id:
    - `20260406T125557Z-live_runtime`
  - compatibility report id:
    - `20260406T125602Z-compatibility_shim`
- observed from `GET /reports/compare`:
  - `status = "ready"`
  - `after_live_report_id = "20260406T125557Z-live_runtime"`
  - `after_compat_report_id = "20260406T125602Z-compatibility_shim"`
  - `after_triggered_equal = true`
  - `after_narrated_equal = true`
  - `after_latest_spot_equal = true`

## Current Branch

- `main`

## Full `git status --short --branch`

```text
## main...origin/main [ahead 41]
 M docs/DEV_WORKFLOW.md
?? coordination/
?? tmp_mvsim_harness_smoke/
?? tmp_mvsim_live_bridge_smoke/
?? tmp_mvsim_runtime_attempt/
```

## Commit Hash

- `044572ff19a8e5a6cac77c64c9e0e74c65fe1268`

## Whether Files Are Staged And/Or Committed

- repo code/doc bundle for Round 039:
  - committed
- currently staged:
  - no
- `coordination/latest_result.md`:
  - updated locally after commit only
  - not staged
  - not committed

## Blockers, Risks, Or Remaining Gaps

- the comparison is intentionally compact and only compares the latest available pair
- it is not a generic historical analytics surface
- truth still depends on the correctness of the persisted report artifacts from earlier runs
- `docs/DEV_WORKFLOW.md` still has a separate pre-existing local modification outside this round
- temp smoke directories remain untracked and were intentionally not included in the commit
