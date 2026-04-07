# Current Round Result

## Round
Round 038 - Harness Validation Report Artifact And Run History Baseline

## Summary

- Status: `harness_report_artifacts_enabled`
- This round made each harness validation run leave behind a durable, operator-readable JSON report.
- The chosen strategy was:
  - keep report persistence inside the harness service layer
  - use simple file-backed JSON artifacts
  - reuse existing harness/session truth instead of inventing a new state machine
- The harness can now:
  - persist one report per validation run
  - return the latest report without rerunning validation
  - return a small recent-history list
- Both:
  - `live_runtime`
  - `compatibility_shim`
  now produce truthful, distinguishable report artifacts.

## What I Changed

- Added a lightweight report contract and file-backed store:
  - `services/mvsim_validation_harness/reporting.py`
- Extended the harness runtime so each validation result is turned into a persisted report artifact:
  - `services/mvsim_validation_harness/runtime.py`
- Exposed report read surfaces through the harness API:
  - `GET /reports/latest`
  - `GET /reports/recent`
  - `services/mvsim_validation_harness/app.py`
- Updated the harness page to show:
  - latest report summary
  - short recent-run history
  - `services/mvsim_validation_harness/static/index.html`
- Added focused tests for:
  - report shape
  - report persistence/readback
  - report endpoints on the harness page path
  - `tests/test_mvsim_validation_reporting.py`
  - `tests/test_mvsim_validation_harness.py`
- Added focused docs and updated operator docs:
  - `docs/MVSIM_VALIDATION_REPORTS.md`
  - `docs/MVSIM_VALIDATION_HARNESS.md`
  - `README.md`

## Exact Files Changed

- `README.md`
- `docs/MVSIM_VALIDATION_HARNESS.md`
- `docs/MVSIM_VALIDATION_REPORTS.md`
- `services/mvsim_validation_harness/app.py`
- `services/mvsim_validation_harness/runtime.py`
- `services/mvsim_validation_harness/static/index.html`
- `services/mvsim_validation_harness/reporting.py`
- `tests/test_mvsim_validation_harness.py`
- `tests/test_mvsim_validation_reporting.py`
- `coordination/latest_result.md` updated locally after commit only, not staged

## Validation-Report Strategy Chosen

Chosen strategy:

- one JSON report per completed harness validation run
- file-backed storage under the existing harness runtime directory
- latest + recent read surfaces exposed directly by the harness

What that means:

- no database
- no generic telemetry warehouse
- no replay required to inspect the most recent run
- compatibility and live runs remain explicitly distinguishable

## Where Report Artifacts Are Stored

Reports are stored under:

- `session_logs/mvsim_validation_harness/reports/`

Real report artifact examples created during this round:

- `C:\Users\saili\Desktop\odin_nav_stack_local_llm_docs\session_logs\mvsim_validation_harness\reports\20260406T124346Z-live_runtime.json`
- `C:\Users\saili\Desktop\odin_nav_stack_local_llm_docs\session_logs\mvsim_validation_harness\reports\20260406T124351Z-compatibility_shim.json`

## What The Report Includes

Current report fields include at least:

- `report_id`
- `created_at`
- `status`
- `validation_mode`
- `mvsim_mode`
- `config_path`
- `config_name`
- `harness_url`
- `debug_url`
- `passed`
- `session_id`
- `latest_spot_name`
- `latest_narration_text`
- `route_completed`
- `live_first_poi_hit_occurred`
- `live_second_poi_hit_occurred`
- `live_second_narration_occurred`
- `recent_triggered_spot_ids`
- `recent_narrated_spot_ids`
- `mvsim_source_kind`
- `proxy_target`
- `service_targets`
- `detail`
- `report_path`

## Whether Both Live And Compatibility Runs Produce Truthful Artifacts

Yes.

Truthful observed facts from the real smoke:

- live run report:
  - `report_id = "20260406T124346Z-live_runtime"`
  - `validation_mode = "live_runtime"`
  - `passed = true`
- compatibility run report:
  - `report_id = "20260406T124351Z-compatibility_shim"`
  - `validation_mode = "compatibility_shim"`
  - `passed = true`
- latest report endpoint then returned the compatibility run as the newest completed artifact
- recent report history showed both run types in order

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
python scripts/run_mvsim_validation_harness.py --config configs/sim_harness.yaml --host 127.0.0.1 --port 8302
```

Run the isolated local stack and validations:

```text
POST http://127.0.0.1:8302/services/start
{"validation_mode":"live_runtime"}

POST http://127.0.0.1:8302/validation/run
{"validation_mode":"live_runtime","question":"What does this final stop prove?"}

POST http://127.0.0.1:8302/validation/run
{"validation_mode":"compatibility_shim","question":"What does this final stop prove?"}
```

Read persisted reports without rerunning validation:

```text
GET http://127.0.0.1:8302/reports/latest
GET http://127.0.0.1:8302/reports/recent
```

Stop the isolated stack:

```text
POST http://127.0.0.1:8302/services/stop
```

## What Operator Fact Was Actually Validated

The truthful operator fact validated in this round is:

- after a harness validation run finishes, the operator can inspect a durable report artifact later
- the operator does not need to replay the whole session to see:
  - which mode ran
  - whether it passed
  - whether route completion occurred
  - whether first/second live stop truth occurred
  - which spots were triggered/narrated
- this works for both:
  - truthful live MVSim validation
  - compatibility replay validation

## Whether The Round Ended In `harness_report_artifacts_enabled`, `harness_report_artifacts_partially_enabled`, Or `harness_report_artifacts_blocked`

This round ended in:

- `harness_report_artifacts_enabled`

## What The Next Narrow Step Is After This

The next narrow step is:

1. decide whether to add a very small export/share flow for the latest harness report
2. if needed later, add a compact per-run diff/comparison helper between the latest live and compatibility reports
3. keep the report layer concise and file-backed instead of broadening into generic analytics

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
  - `Ran 120 tests ... OK`

### Real harness operator smoke

- launched:
  - `python scripts/run_mvsim_validation_harness.py --config configs/sim_harness.yaml --host 127.0.0.1 --port 8302`
- observed from live validation result:
  - `validation_report.report_id = "20260406T124346Z-live_runtime"`
  - `validation_report.validation_mode = "live_runtime"`
  - `validation_report.passed = true`
- observed from compatibility validation result:
  - `validation_report.report_id = "20260406T124351Z-compatibility_shim"`
  - `validation_report.validation_mode = "compatibility_shim"`
  - `validation_report.passed = true`
- observed from `GET /reports/latest`:
  - `latest_report.report_id = "20260406T124351Z-compatibility_shim"`
  - `latest_report.validation_mode = "compatibility_shim"`
  - `latest_report.route_completed = true`
- observed from `GET /reports/recent`:
  - recent modes included:
    - `compatibility_shim`
    - `live_runtime`
  - recent IDs included:
    - `20260406T124351Z-compatibility_shim`
    - `20260406T124346Z-live_runtime`
- observed from `/services/stop`:
  - stopped:
    - `sim_pose_ingress_server`
    - `api_server`

## Current Branch

- `main`

## Full `git status --short --branch`

```text
## main...origin/main [ahead 40]
 M docs/DEV_WORKFLOW.md
?? coordination/
?? tmp_mvsim_harness_smoke/
?? tmp_mvsim_live_bridge_smoke/
?? tmp_mvsim_runtime_attempt/
```

## Commit Hash

- `25aebfdbe47bff943da212afbac524f5c3c06cc3`

## Whether Files Are Staged And/Or Committed

- repo code/doc bundle for Round 038:
  - committed
- currently staged:
  - no
- `coordination/latest_result.md`:
  - updated locally after commit only
  - not staged
  - not committed

## Blockers, Risks, Or Remaining Gaps

- the report layer is intentionally concise and does not persist every internal event
- latest/recent history is file-backed and small by design, not a long-term analytics system
- the live report truth still depends on the same validated prerequisites:
  - WSL MVSim availability
  - isolated live-validation world
  - isolated forward-motion validation lane
- `docs/DEV_WORKFLOW.md` still has a separate pre-existing local modification outside this round
- temp smoke directories remain untracked and were intentionally not included in the commit
