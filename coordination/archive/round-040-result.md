# Current Round Result

## Round
Round 040 - Validation Asset Identity And Comparison Guardrails Baseline

## Summary

- Status: `comparison_guardrails_enabled`
- This round added a compact validation-asset identity contract to persisted harness reports.
- The latest live-vs-compatibility comparison now explicitly reports whether the two latest reports are:
  - `comparable`
  - `comparable_with_warnings`
  - `not_directly_comparable`
- The comparison no longer silently implies that the latest pair is safe to compare when one side comes from different or incomplete validation assets.

## What I Changed

- Added a compact report-side validation asset identity block:
  - `services/mvsim_validation_harness/reporting.py`
- Added guardrail evaluation logic for latest live-vs-compatibility comparison:
  - `services/mvsim_validation_harness/reporting.py`
- Passed the active validation config into report persistence so report identity is built from the actual validation asset bundle:
  - `services/mvsim_validation_harness/runtime.py`
- Exposed compact comparability and guardrail reasons in the harness page:
  - `services/mvsim_validation_harness/static/index.html`
- Extended focused reporting and harness tests:
  - `tests/test_mvsim_validation_reporting.py`
  - `tests/test_mvsim_validation_harness.py`
- Updated operator-facing docs:
  - `docs/MVSIM_VALIDATION_REPORTS.md`
  - `docs/MVSIM_VALIDATION_HARNESS.md`
  - `README.md`

## Exact Files Changed

- `README.md`
- `docs/MVSIM_VALIDATION_HARNESS.md`
- `docs/MVSIM_VALIDATION_REPORTS.md`
- `services/mvsim_validation_harness/reporting.py`
- `services/mvsim_validation_harness/runtime.py`
- `services/mvsim_validation_harness/static/index.html`
- `tests/test_mvsim_validation_harness.py`
- `tests/test_mvsim_validation_reporting.py`
- `coordination/latest_result.md` updated locally after commit only, not staged

## Validation-Asset Identity Strategy Chosen

Chosen strategy:

- keep the identity block small and operator-facing
- reuse existing config/report information where possible
- separate direct-comparison asset fields from warning-only config context
- keep the comparison in the harness/operator layer only

The identity contract is intentionally concise. It does not mirror the whole validation config.

## What Fields Define Report Identity

Each new report now includes `validation_asset_identity` with:

- `identity_version`
- `validation_mode`
- `mvsim_mode`
- `config_name`
- `config_path`
- `route_file`
- `poi_file`
- `world_file`
- `vehicle_name`
- `alignment_strategy`
- `motion_strategy`
- `target_spot_id`
- `second_target_spot_id`

Direct-comparison required fields are:

- `route_file`
- `poi_file`
- `world_file`
- `vehicle_name`
- `alignment_strategy`
- `motion_strategy`

Warning-only context fields are:

- `config_name`
- `config_path`

## How Comparison Guardrails Now Work

Current comparison builder behavior:

- if either latest mode report is missing:
  - `status = "missing_reports"`
- if both reports exist:
  - compare direct-comparison asset fields
  - compare warning-only config-context fields
  - return:
    - `comparability_status`
    - `guardrail_reasons`
    - `identity_guardrails`

Current comparability outcomes:

- `comparable`
  - all required validation asset fields match
- `comparable_with_warnings`
  - required assets still match, but one or more identity fields are incomplete or only warning-only config fields differ
- `not_directly_comparable`
  - a required asset field differs
  - or one side is missing the `validation_asset_identity` block entirely

## Whether Comparable Vs Non-Comparable Cases Are Explicit

Yes.

This is now explicit at two levels:

- per-report:
  - every new report includes `validation_asset_identity`
- per-comparison:
  - `comparability_status`
  - `guardrail_reasons`
  - compact identity blocks for both compared reports

## Exact Commands Used

### Focused tests

```text
python -m unittest tests.test_mvsim_validation_reporting -v
python -m unittest tests.test_mvsim_validation_harness -v
```

### Full regression

```text
python -m unittest discover -s tests
```

### Real harness operator validation

Start the harness:

```text
python scripts/run_mvsim_validation_harness.py --config configs/sim_harness.yaml --host 127.0.0.1 --port 8304
```

Start or attach the local stack:

```text
POST http://127.0.0.1:8304/services/start
{"validation_mode":"live_runtime"}
```

Run live validation:

```text
POST http://127.0.0.1:8304/validation/run
{"validation_mode":"live_runtime","question":"What does this final stop prove?"}
```

Run compatibility validation:

```text
POST http://127.0.0.1:8304/validation/run
{"validation_mode":"compatibility_shim","question":"What does this final stop prove?"}
```

Read the comparison:

```text
GET http://127.0.0.1:8304/reports/compare
```

Read the harness page:

```text
GET http://127.0.0.1:8304/harness
```

## What Operator Fact Was Actually Validated

The truthful operator facts validated in this round are:

1. old or incomplete reports are now explicitly guarded
   - during the first smoke, `/reports/compare` returned:
     - `comparability_status = "not_directly_comparable"`
     - reason:
       - `compatibility_shim report is missing validation_asset_identity`
   - this confirmed the harness no longer silently compares incomplete report generations

2. a fresh live + compatibility pair generated under the same validation asset bundle is now explicitly comparable
   - fresh live report:
     - `20260406T133604Z-live_runtime`
   - fresh compatibility report:
     - `20260406T133622Z-compatibility_shim`
   - `/reports/compare` then returned:
     - `status = "ready"`
     - `comparability_status = "comparable"`
     - `guardrail_reasons = ["required validation assets match across the latest live and compatibility reports"]`

## Whether The Round Ended In `comparison_guardrails_enabled`, `comparison_guardrails_partially_enabled`, Or `comparison_guardrails_blocked`

This round ended in:

- `comparison_guardrails_enabled`

## What The Next Narrow Step Is After This

The next narrow step is:

1. if useful later, expose a tiny per-field identity diff summary on the harness page instead of only compact reason strings
2. optionally add a one-click operator export of the latest comparison result
3. keep future comparison logic report-driven and avoid broadening into historical analytics

## Exact Validation Performed

### Focused unit validation

- `python -m unittest tests.test_mvsim_validation_reporting -v`
  - passed
- `python -m unittest tests.test_mvsim_validation_harness -v`
  - passed

### Full regression validation

- `python -m unittest discover -s tests`
  - passed
  - `Ran 124 tests ... OK`

### Real harness operator smoke

- launched:
  - `python scripts/run_mvsim_validation_harness.py --config configs/sim_harness.yaml --host 127.0.0.1 --port 8304`
- observed harness page:
  - `GET /harness`
  - returned `200`
- first observed guardrail behavior against older incomplete report history:
  - `comparability_status = "not_directly_comparable"`
  - `guardrail_reasons = ["compatibility_shim report is missing validation_asset_identity"]`
- then created a fresh live + compatibility pair on the same harness:
  - live report id:
    - `20260406T133604Z-live_runtime`
  - compatibility report id:
    - `20260406T133622Z-compatibility_shim`
- observed from the fresh `GET /reports/compare`:
  - `status = "ready"`
  - `comparability_status = "comparable"`
  - `triggered_spots_equal = true`
  - `narrated_spots_equal = true`
  - `latest_spot_name_equal = true`
- verified both fresh reports now include:
  - `validation_asset_identity.identity_version = "validation_asset_identity.v1"`
  - same:
    - `route_file`
    - `poi_file`
    - `world_file`
    - `vehicle_name`
    - `alignment_strategy`
    - `motion_strategy`

## Current Branch

- `main`

## Full `git status --short --branch`

```text
## main...origin/main [ahead 42]
 M docs/DEV_WORKFLOW.md
?? coordination/
?? tmp_mvsim_harness_smoke/
?? tmp_mvsim_live_bridge_smoke/
?? tmp_mvsim_runtime_attempt/
```

## Commit Hash

- `496e8af2ca3b3137588ee955f0374c9477dc22a6`

## Whether Files Are Staged And/Or Committed

- repo code/doc bundle for Round 040:
  - committed
- currently staged:
  - no
- `coordination/latest_result.md`:
  - updated locally
  - not staged
  - not committed

## Blockers, Risks, Or Remaining Gaps

- old pre-Round-040 reports remain in `session_logs/mvsim_validation_harness/reports/` and can still appear in latest-vs-latest history until a fresh report pair replaces them
- this is acceptable because the new guardrails now make incomplete identity explicit instead of silently comparing them
- the comparison is still intentionally compact and latest-pair only
- this round does not add historical identity analytics or raw-event diffing
- `docs/DEV_WORKFLOW.md` still has a separate pre-existing local modification outside this round
- temp smoke directories remain untracked and were intentionally not included in the commit
