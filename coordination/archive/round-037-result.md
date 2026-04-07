# Current Round Result

## Round
Round 037 - Live MVSim Harness Mode And Port-Isolated Validation Baseline

## Summary

- Status: `live_harness_mode_enabled`
- This round turned the already-proven live MVSim path into a first-class harness flow instead of leaving it as manual multi-process choreography.
- The chosen operator strategy was:
  - keep the truthful live bridge and sim-ingress stack unchanged
  - keep compatibility replay available
  - add explicit harness validation-mode selection
  - add a dedicated harness config with isolated local ports
- The harness can now truthfully run:
  - `live_runtime`
  - `compatibility_shim`
- The isolated local operator stack now uses:
  - sim ingress: `http://127.0.0.1:8110`
  - API + `/debug`: `http://127.0.0.1:8001`
- The live harness run truthfully validated:
  - first stop hit
  - second stop hit
  - route completion
- Compatibility mode still works on the same isolated harness stack.

## What I Changed

- Added a dedicated operator config for harness use:
  - `configs/sim_harness.yaml`
- Switched the harness runner default to that isolated config:
  - `scripts/run_mvsim_validation_harness.py`
- Extended the harness API so start/run calls accept an explicit:
  - `validation_mode`
  - `services/mvsim_validation_harness/app.py`
- Reworked the harness runtime so it can:
  - keep track of available/default/selected validation modes
  - start the isolated local stack
  - run compatibility replay on that stack
  - launch WSL MVSim, bridge live pose into the isolated stack, and summarize the truthful live result
  - `services/mvsim_validation_harness/runtime.py`
- Updated the harness page so operators can:
  - choose `live_runtime` vs `compatibility_shim`
  - see the selected mode
  - see live first/second stop truth
  - see route completion truth
  - `services/mvsim_validation_harness/static/index.html`
- Added focused tests for:
  - mode-aware harness requests
  - isolated port config
  - compatibility-mode request handling
  - `tests/test_mvsim_validation_harness.py`
- Updated operator-facing docs:
  - `README.md`
  - `docs/MVSIM_VALIDATION_HARNESS.md`

## Exact Files Changed

- `README.md`
- `configs/sim_harness.yaml`
- `docs/MVSIM_VALIDATION_HARNESS.md`
- `scripts/run_mvsim_validation_harness.py`
- `services/mvsim_validation_harness/app.py`
- `services/mvsim_validation_harness/runtime.py`
- `services/mvsim_validation_harness/static/index.html`
- `tests/test_mvsim_validation_harness.py`
- `coordination/latest_result.md` updated locally after commit only, not staged

## Harness / Live-Mode Strategy Chosen

Chosen strategy:

- a dedicated harness config variant:
  - `configs/sim_harness.yaml`
- explicit harness validation-mode selection:
  - `compatibility_shim`
  - `live_runtime`
- isolated local stack ports for operator validation only:
  - sim ingress on `8110`
  - API server on `8001`

What that means:

- the harness no longer depends on the machine-global `8000` port
- the harness can run the truthful live path without requiring the operator to manually start:
  - sim ingress
  - API proxy
  - live MVSim bridge
- compatibility mode stays explicit instead of being silently replaced by live mode

## How Port Isolation Was Handled

Port isolation was handled with the dedicated harness config:

- `service_endpoints.sim_pose_ingress_server.port = 8110`
- `service_endpoints.api_server.port = 8001`

This keeps the operator path off the machine-global default API port while preserving the existing repo services and contracts.

## Whether The Harness Can Truthfully Run The Live MVSim Path End To End

Yes.

Truthful observed operator facts:

- harness start call returned:
  - `ok: true`
  - `validation_mode: "live_runtime"`
- live harness validation returned:
  - `status: "passed"`
  - `validation_mode: "live_runtime"`
  - `live_validation_summary.live_first_poi_hit_occurred: true`
  - `live_validation_summary.live_second_poi_hit_occurred: true`
  - `sim_ingress_state.route_completed: true`
  - `live_validation_summary.recent_triggered_spot_ids = ["gate", "plaza", "gallery"]`
- harness exposed:
  - `debug_url: "http://127.0.0.1:8001/debug"`

So the operator can now launch the harness and use one harness-owned flow to run the truthful live MVSim path end to end on isolated ports.

## Whether Compatibility Mode Still Works

Yes.

Truthful observed operator facts:

- compatibility harness validation returned:
  - `status: "passed"`
  - `validation_mode: "compatibility_shim"`
  - `sim_ingress_state.route_completed: true`
  - `mvsim_source.source_kind: "mvsim_compatibility_shim"`

## Exact Commands Used

### Focused tests

```text
python -m unittest tests.test_mvsim_validation_harness -v
python -m unittest tests.test_api_server -v
python -m unittest tests.test_mvsim_live_bridge -v
```

### Full regression

```text
python -m unittest discover -s tests
```

### Real harness operator validation

Start the harness on a dedicated port:

```text
python scripts/run_mvsim_validation_harness.py --config configs/sim_harness.yaml --host 127.0.0.1 --port 8301
```

Check harness status:

```text
GET http://127.0.0.1:8301/status
```

Start the isolated local stack through the harness:

```text
POST http://127.0.0.1:8301/services/start
{"validation_mode":"live_runtime"}
```

Run truthful live validation through the harness:

```text
POST http://127.0.0.1:8301/validation/run
{"validation_mode":"live_runtime","question":"What does this final stop prove?"}
```

Run compatibility replay through the same harness:

```text
POST http://127.0.0.1:8301/validation/run
{"validation_mode":"compatibility_shim","question":"What does this final stop prove?"}
```

Stop the isolated local stack:

```text
POST http://127.0.0.1:8301/services/stop
```

## What End-To-End Operator Fact Was Actually Validated

The truthful operator fact validated in this round is:

- a user can start the MVSim validation harness
- the harness can launch its own isolated local stack on non-default ports
- the harness can run the truthful live MVSim bridge path itself
- the harness can surface truthful live validation facts:
  - first stop hit
  - second stop hit
  - route completion
- the same harness instance can still run compatibility replay afterward

This closes the operator-repeatability gap without changing the underlying simulator truth claims.

## Whether The Round Ended In `live_harness_mode_enabled`, `live_harness_mode_partially_enabled`, Or `live_harness_mode_blocked`

This round ended in:

- `live_harness_mode_enabled`

## What The Next Narrow Step Is After This

The next narrow step is:

1. decide whether to keep `configs/sim_harness.yaml` as the canonical PC operator config for MVSim validation
2. if needed later, surface a more concise per-run live summary artifact or export without broadening the harness into a full supervisor
3. keep future simulator realism work separate from this now-repeatable truthful operator baseline

## Exact Validation Performed

### Focused unit validation

- `python -m unittest tests.test_mvsim_validation_harness -v`
  - passed
- `python -m unittest tests.test_api_server -v`
  - passed
- `python -m unittest tests.test_mvsim_live_bridge -v`
  - passed

### Full regression validation

- `python -m unittest discover -s tests`
  - passed
  - `Ran 118 tests ... OK`

### Real harness operator smoke

- launched:
  - `python scripts/run_mvsim_validation_harness.py --config configs/sim_harness.yaml --host 127.0.0.1 --port 8301`
- observed from status:
  - `debug_url = "http://127.0.0.1:8001/debug"`
  - live runtime is available
  - isolated service targets are:
    - `http://127.0.0.1:8110/health`
    - `http://127.0.0.1:8001/health`
- observed from `/services/start`:
  - `ok = true`
  - `validation_mode = "live_runtime"`
- observed from live `/validation/run`:
  - `status = "passed"`
  - `live_first_poi_hit_occurred = true`
  - `live_second_poi_hit_occurred = true`
  - `route_completed = true`
  - `recent_triggered_spot_ids = ["gate", "plaza", "gallery"]`
- observed from compatibility `/validation/run`:
  - `status = "passed"`
  - `validation_mode = "compatibility_shim"`
  - `route_completed = true`
  - `mvsim_source.source_kind = "mvsim_compatibility_shim"`
- observed from `/services/stop`:
  - stopped:
    - `sim_pose_ingress_server`
    - `api_server`

## Current Branch

- `main`

## Full `git status --short --branch`

```text
## main...origin/main [ahead 39]
 M docs/DEV_WORKFLOW.md
?? coordination/
?? tmp_mvsim_harness_smoke/
?? tmp_mvsim_live_bridge_smoke/
?? tmp_mvsim_runtime_attempt/
```

## Commit Hash

- `2098e4d5761dc74574716b2e8484dc4bbd7cc6e5`

## Whether Files Are Staged And/Or Committed

- repo code/doc bundle for Round 037:
  - committed
- currently staged:
  - no
- `coordination/latest_result.md`:
  - updated locally after commit only
  - not staged
  - not committed

## Blockers, Risks, Or Remaining Gaps

- the live operator path is now repeatable, but it still depends on:
  - WSL MVSim availability
  - the explicit isolated validation world
  - the explicit forward-motion validation lane
- this round does not broaden the truth claim into general autonomous simulator navigation
- `docs/DEV_WORKFLOW.md` still has a separate pre-existing local modification outside this round
- temp smoke directories remain untracked and were intentionally not included in the commit
