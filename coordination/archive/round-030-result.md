# Current Round Result

## Round
Round 030 - MVSim Guided Validation Harness Baseline

## Summary

- Status: PASSED
- The repository now contains a narrow operator-facing MVSim validation harness that replaces the previous multi-terminal, multi-REST-call PC validation flow with a single local page and a small local control surface.
- This round stayed intentionally narrow:
  - PC-only
  - local/dev-only process launch
  - no live MVSim runtime dependency
  - no new packaging or supervisor layer
- The harness can now do both:
  - attach to already running local services
  - launch the repo-owned local sim stack itself for validation

## What I Changed

- Added a dedicated MVSim validation harness runtime:
  - `services/mvsim_validation_harness/runtime.py`
- Added a small FastAPI harness app:
  - `services/mvsim_validation_harness/app.py`
- Added a static operator page:
  - `services/mvsim_validation_harness/static/index.html`
- Added a runnable entrypoint:
  - `scripts/run_mvsim_validation_harness.py`
- Added focused docs:
  - `docs/MVSIM_VALIDATION_HARNESS.md`
- Added focused tests:
  - `tests/test_mvsim_validation_harness.py`
- Added runtime package export:
  - `services/mvsim_validation_harness/__init__.py`

## Exact Files Changed

- `docs/MVSIM_VALIDATION_HARNESS.md`
- `scripts/run_mvsim_validation_harness.py`
- `services/mvsim_validation_harness/__init__.py`
- `services/mvsim_validation_harness/app.py`
- `services/mvsim_validation_harness/runtime.py`
- `services/mvsim_validation_harness/static/index.html`
- `tests/test_mvsim_validation_harness.py`
- `coordination/latest_result.md` updated locally after commit only, not staged

## What The Harness Actually Does

The new harness is a thin local operator layer over the existing Round 029 MVSim compatibility path.

It exposes:

- `GET /health`
- `GET /status`
- `POST /services/start`
- `POST /services/stop`
- `POST /validation/run`
- `GET /debug-link`
- local page at:
  - `/harness`

The page presents:

- sim-ingress reachability
- sim-profile API reachability
- `/debug` availability
- bridge/demo validation status
- route completion
- latest POI / latest narration
- latest session id
- follow-up question result

## How A Human Uses It

### Easiest path

```text
python scripts/run_mvsim_validation_harness.py --config configs/sim.yaml --open-browser
```

Then open:

```text
http://127.0.0.1:8300/harness
```

On the page:

1. Click `Start / Attach Local Stack`
2. Click `Run MVSim Validation`
3. Optionally click `Open /debug`

### What it launches locally

When local services are not already available, the harness launches:

- `python scripts/run_sim_pose_ingress_server.py --config configs/sim.yaml --host 127.0.0.1 --port 8100`
- `python scripts/run_api_server.py --config configs/sim.yaml --host 127.0.0.1 --port 8000`

### What it reuses

Validation reuses the existing MVSim compatibility path:

- `services/sim_publisher_bridge/mvsim_source.py`
- `content/sim/demo_mvsim_pose_stream.yaml`
- existing sim-ingress HTTP path
- existing sim-profile API proxy path

## Important Real-World Fixes Needed During This Round

This round initially failed in real CLI execution for two non-test-only reasons.

### Fix 1: Relative config path startup bug

The new runtime originally assumed `config_path` was already absolute and attempted:

- `self._config_path.relative_to(self._repo_root)`

When launched through:

```text
python scripts/run_mvsim_validation_harness.py --config configs/sim.yaml
```

that raised a real startup error because `configs/sim.yaml` was relative.

I fixed this by normalizing relative config paths against `repo_root` inside:

- `services/mvsim_validation_harness/runtime.py`

and added coverage for that startup shape in:

- `tests/test_mvsim_validation_harness.py`

### Fix 2: Health endpoint self-timeout

The initial harness `/health` and `/status` path synchronously probed downstream services using long default timeouts, so the harness page could appear to hang when the local stack had not yet been started.

I fixed this by separating:

- fast probe timeout for operator status surfaces
- longer request timeout for actual validation work

This keeps:

- `/health`
- `/status`

responsive even when upstream services are currently unavailable.

## What Exact Operator Problems It Now Surfaces

The harness now reports these common operator states explicitly:

- `healthy`
  - service is reachable and responding as expected
- `unreachable`
  - expected upstream is not responding
- `port_conflict`
  - target port is occupied but the expected health endpoint did not respond

These statuses are surfaced in:

- harness JSON endpoints
- the `/harness` static page

## Exact Validation Performed

### Automated

- `python -m unittest tests.test_mvsim_validation_harness -v`
  - passed
  - `Ran 4 tests ... OK`
- `python -m unittest tests.test_mvsim_integration -v`
  - passed
  - `Ran 3 tests ... OK`
- `python -m unittest tests.test_api_server -v`
  - passed
  - `Ran 6 tests ... OK`
- `python -m unittest discover -s tests`
  - passed
  - `Ran 103 tests ... OK`

### Manual

Ran:

```text
python scripts/run_mvsim_validation_harness.py --config configs/sim.yaml --host 127.0.0.1 --port 8300
```

Then exercised:

```text
GET  http://127.0.0.1:8300/health
POST http://127.0.0.1:8300/services/start
POST http://127.0.0.1:8300/validation/run
GET  http://127.0.0.1:8300/status
POST http://127.0.0.1:8300/services/stop
```

## Exact Real Results Observed

### Initial health before stack launch

- `health.status`
  - `ok`
- `service_checks.sim_pose_ingress.status`
  - `unreachable`
- `service_checks.api_server.status`
  - `unreachable`
- `service_checks.debug_page.status`
  - `unreachable`

This is the expected pre-launch operator state.

### After `POST /services/start`

- `start.ok`
  - `true`
- sim pose ingress
  - `status: healthy`
  - `attached_mode: launched_by_harness`
- api server
  - `status: healthy`
  - `attached_mode: launched_by_harness`
- debug page
  - `status: healthy`
  - `attached_mode: attach_existing`

### After `POST /validation/run`

- `validation.status`
  - `passed`
- `route_completed`
  - `true`
- `latest_narration_text`
  - `The History Gallery is the final stop in the demo tour. It shows that the guide flow can finish a multi-POI route without duplicate triggers.`
- `latest_session_id`
  - `mock_tour_20260406T032240Z`
- `followup_ok`
  - `true`
- `followup_answer`
  - `It proves that the route can finish cleanly after several narrations without duplicate triggers.`
- `debug_url`
  - `http://127.0.0.1:8000/debug`

### Validation snapshot after run

- `overall_status`
  - `passed`
- `route_completed`
  - `true`
- `latest_spot_name`
  - `History Gallery`
- `latest_session_id`
  - `mock_tour_20260406T032240Z`
- `followup_question_ok`
  - `true`
- `debug_available`
  - `true`

### After `POST /services/stop`

- `ok`
  - `true`
- `stopped_services`
  - `sim_pose_ingress_server`
  - `api_server`

## What This Means For The Operator Flow Now

Compared with Round 029, a human no longer needs to manually:

- open multiple terminals
- separately remember startup order
- remember the sim-ingress and API URLs
- manually issue validation REST calls
- manually cross-check route/session/question state

Instead, one harness page now centralizes:

- reachability
- startup/attach
- validation execution
- result summary
- debug-page handoff

## Current Branch

- `main`

## Full Git Status --short --branch

```text
## main...origin/main [ahead 31]
 M docs/DEV_WORKFLOW.md
?? coordination/
```

## Commit Hash

- `63afdea3f4cf0890c1f4d5253f16aba1af028525`

## Staged / Committed State

- Round 030 code bundle: committed
- `coordination/latest_result.md`: updated locally after commit, not staged
- Unrelated local modification in `docs/DEV_WORKFLOW.md` remains untouched
- `coordination/` remains outside this commit, per handoff rule

## Blockers, Risks, Or Remaining Gaps

- This remains a PC/dev validation harness, not a packaging/supervisor solution.
- It still uses the Round 029 MVSim compatibility shim, not a live MVSim runtime adapter.
- The current UI is intentionally narrow and operator-facing, not a general simulator dashboard.
- `latest_spot_name` came through most clearly in the aggregated `validation_snapshot`; the raw `api_latest_session.latest_spot_name` field was `null` in the manual run, so the harness summary currently provides the better operator-facing surface.
