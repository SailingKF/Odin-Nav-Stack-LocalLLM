# Current Round Result

## Round
Round 020 - Edge Preflight And Dependency Probe Baseline

## Summary

- Status: PASSED
- The repository now contains an explicit deployment preflight/probe layer alongside the deployment profile summary.
- API-visible health/state now expose a concise `deployment_preflight` surface.
- Preflight now distinguishes:
  - `ok`
  - `unreachable`
  - `missing`
  - `unverified_external`
  - `not_applicable`
- Current edge readiness is now described with both:
  - config/profile intent
  - startup-time best-effort probe outcomes

## What I Changed

- Added a focused preflight/probe module in:
  - `services/deployment_profile/preflight.py`
- Exported it through:
  - `services/deployment_profile/__init__.py`
- Wired preflight into runtime-facing services:
  - `services/api_server/runtime.py`
  - `services/sim_pose_ingress/runtime.py`
- Added focused tests in:
  - `tests/test_deployment_preflight.py`
- Extended API tests in:
  - `tests/test_api_server.py`
- Updated docs:
  - `README.md`
  - `docs/DEPLOYMENT.md`
  - `docs/DEPLOYMENT_PROFILE_CONTRACT.md`
  - `docs/DEPLOYMENT_PREFLIGHT_CONTRACT.md`

## Exact Files Changed

- `README.md`
- `docs/DEPLOYMENT.md`
- `docs/DEPLOYMENT_PROFILE_CONTRACT.md`
- `docs/DEPLOYMENT_PREFLIGHT_CONTRACT.md`
- `services/api_server/runtime.py`
- `services/deployment_profile/__init__.py`
- `services/deployment_profile/preflight.py`
- `services/sim_pose_ingress/runtime.py`
- `tests/test_api_server.py`
- `tests/test_deployment_preflight.py`
- `coordination/latest_result.md`

## What Preflight/Probe Surface I Introduced

New API-visible surface:

- `deployment_preflight`

Current top-level fields:

- `profile_name`
- `summary_status`
- `http_timeout_sec`
- `counts`
- `checks`

Each check now carries a compact shape such as:

- `name`
- `status`
- `kind`
- `path` or `url`
- `detail`
- optional `http_status`

## What Checks/Probes Are Now Performed

### Local File / Directory Checks

- `route_file`
- `poi_file`
- `session_log_dir`

These verify:

- configured route file exists
- configured POI file exists
- session log directory can be created and written

### Safe Local HTTP Probes

When applicable:

- `llm_gateway`
  - probes `llm_gateway_url + /health`
- `ollama_runtime`
  - probes `llm_base_url + /api/tags`

Probe properties:

- best-effort
- short-timeout
- safe on a dev machine
- non-blocking to runtime construction

### External / Unverified Dependency Labels

Current external/unverified markers include:

- `hardware_pose_dependency`
  - for `pose_provider_type: odin_ros`
- `isaac_live_dependency`
  - for sim ingress with `isaac_source.mode: live`
- `audio_device_dependency`
  - for non-mock audio paths

These are intentionally marked as:

- `unverified_external`

because this round does not attempt real hardware/audio/simulator integration.

## How API-Visible Readiness Exposure Changed

`MockTourApiRuntime` now exposes:

- `deployment_profile`
- `deployment_preflight`

in:

- `health()`
- `state()`

`SimPoseIngressRuntime` now exposes:

- `deployment_profile`
- `deployment_preflight`

in:

- `health()`
- `state()`

This means API consumers can now see both:

- what the config claims to be
- what can actually be checked at startup right now

## Exact Validation Performed

### Automated

- `python -m unittest tests.test_deployment_preflight -v`
  - passed
  - `Ran 4 tests ... OK`
- `python -m unittest tests.test_api_server -v`
  - passed
  - `Ran 6 tests ... OK`
- `python -m unittest discover -s tests`
  - passed
  - `Ran 71 tests ... OK`

### Manual

Ran inline runtime checks against:

- `configs/dev.yaml`
- `configs/edge.yaml`

Observed actual current preflight results:

For `dev.yaml`:

- `route_file: ok`
- `poi_file: ok`
- `session_log_dir: ok`
- `llm_gateway: unreachable`
- `ollama_runtime: ok`
- `external_pose_dependency: not_applicable`
- `audio_device_dependency: unverified_external`
- overall `summary_status: unreachable`

For `edge.yaml`:

- `route_file: ok`
- `poi_file: ok`
- `session_log_dir: ok`
- `llm_gateway: unreachable`
- `ollama_runtime: ok`
- `hardware_pose_dependency: unverified_external`
- `audio_device_dependency: not_applicable`
- overall `summary_status: unreachable`

This confirms the new preflight layer is surfacing real local conditions instead of only config intent.

## Which Current Edge Dependencies Remain External/Unverified After This Round

Current `configs/edge.yaml` still has dependencies that cannot be proven by this baseline:

- `hardware_pose_dependency`
  - `pose_provider_type: odin_ros`
  - still `unverified_external`

Current edge config also still depends on a local gateway process being up:

- `llm_gateway`
  - currently `unreachable` on this machine at probe time

Current edge config currently does not require a real audio device path because:

- `audio_output_type: mock`

so:

- `audio_device_dependency: not_applicable`

Ollama itself is currently reachable:

- `ollama_runtime: ok`

## Current Branch

- `main`

## Full Git Status --short --branch

```text
## main...origin/main [ahead 21]
 M docs/DEV_WORKFLOW.md
?? coordination/
```

## Commit Hash

- `cd62e67424a757da3cd44ee893b04f3999db325a`

## Staged / Committed State

- Round 020 code bundle: committed
- `coordination/latest_result.md`: updated locally after commit, not staged
- Unrelated local modification in `docs/DEV_WORKFLOW.md` remains untouched

## Blockers, Risks, Or Remaining Gaps Before Real Orin NX Or Hardware-Backed Deployment

- Current preflight is intentionally shallow and safe; it does not prove end-to-end hardware readiness.
- Reachability checks only confirm that a local HTTP dependency responds, not that it is semantically correct for deployment.
- Real Orin NX readiness still requires:
  - real `odin_ros` pose integration
  - real non-mock audio/output path
  - live hardware and device validation
- Current edge path still depends on starting the local `llm_gateway` process before preflight can report it as reachable.
