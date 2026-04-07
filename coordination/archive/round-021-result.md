# Current Round Result

## Round
Round 021 - Deployment Launch Plan And Startup Contract Baseline

## Summary

- Status: PASSED
- The repository now contains an explicit launch-plan/startup-contract layer for `dev`, `sim`, and `edge`.
- Startup expectations are now machine-readable enough to distinguish:
  - repo-owned internal services
  - external/manual dependencies
  - optional services
- API-visible runtime health/state now expose a `deployment_launch_plan` surface.
- Operators can also inspect the current plan directly through a lightweight script.

## What I Changed

- Added a focused launch-plan module in:
  - `services/deployment_profile/launch_plan.py`
- Exported it through:
  - `services/deployment_profile/__init__.py`
- Wired launch-plan exposure into runtime-facing services:
  - `services/api_server/runtime.py`
  - `services/sim_pose_ingress/runtime.py`
- Added an operator-facing script:
  - `scripts/print_launch_plan.py`
- Added focused tests in:
  - `tests/test_deployment_launch_plan.py`
- Extended API tests in:
  - `tests/test_api_server.py`
- Updated docs:
  - `README.md`
  - `docs/DEPLOYMENT.md`
  - `docs/DEPLOYMENT_LAUNCH_PLAN_CONTRACT.md`

## Exact Files Changed

- `README.md`
- `docs/DEPLOYMENT.md`
- `docs/DEPLOYMENT_LAUNCH_PLAN_CONTRACT.md`
- `scripts/print_launch_plan.py`
- `services/api_server/runtime.py`
- `services/deployment_profile/__init__.py`
- `services/deployment_profile/launch_plan.py`
- `services/sim_pose_ingress/runtime.py`
- `tests/test_api_server.py`
- `tests/test_deployment_launch_plan.py`
- `coordination/latest_result.md`

## What Launch-Plan/Startup-Contract Surface I Introduced

New runtime-visible surface:

- `deployment_launch_plan`

Current top-level fields:

- `profile_name`
- `automation_level`
- `steps`
- `step_count`
- `required_step_count`
- `categories`

Current automation level:

- `manual_guided`

Each step now includes:

- `step_id`
- `order`
- `category`
- `required`
- `name`
- `startup_hint`
- `readiness_gates`
- `detail`

Current step categories:

- `internal_service`
- `external_dependency`
- `optional_service`

## How Dev/Sim/Edge Startup Expectations Are Now Represented

### Dev

Current `dev` launch plan represents:

- external Ollama runtime first when the config uses `ollama`
- repo-owned `llm_gateway`
- repo-owned `api_server`
- optional debug-browser step

### Sim

Current `sim` launch plan represents:

- stub or live simulator source choice
- repo-owned `sim_pose_ingress_server`
- optional publisher bridge
- optional API/debug server

### Edge

Current `edge` launch plan represents:

- external hardware pose dependency
- external Ollama runtime when configured
- repo-owned `llm_gateway`
- repo-owned `api_server`
- future audio-device step that remains optional/manual while edge audio is still mock

This gives one reusable place to read:

- what starts first
- what is repo-owned
- what remains external/manual
- which readiness gates matter before later steps

## What Current Steps Remain Manual/External For Edge

Current `edge` launch plan still treats these as external/manual:

- `hardware_pose_dependency`
- `ollama_runtime`

Current edge audio step is still represented as optional because:

- `audio_output_type: mock`

So true edge audio bring-up remains manual/future work rather than a required repo-owned startup step.

## How Operators Can Inspect The Launch Plan Now

### API Surfaces

Operators can inspect:

- `deployment_launch_plan`

through:

- API `health`
- API `state`

### Script Entry Point

Operators can also run:

```text
python scripts/print_launch_plan.py --config configs/dev.yaml
python scripts/print_launch_plan.py --config configs/edge.yaml
```

### Manual Sample

Actual current output for:

- `python scripts/print_launch_plan.py --config configs/edge.yaml`

showed these ordered steps:

1. `hardware_pose_dependency`
2. `ollama_runtime`
3. `llm_gateway`
4. `api_server`
5. `audio_device_dependency`

and categories:

- `external_dependency`
- `internal_service`
- `optional_service`

## Exact Validation Performed

### Automated

- `python -m unittest tests.test_deployment_launch_plan -v`
  - passed
  - `Ran 3 tests ... OK`
- `python -m unittest tests.test_api_server -v`
  - passed
  - `Ran 6 tests ... OK`
- `python -m unittest discover -s tests`
  - passed
  - `Ran 74 tests ... OK`

### Manual

Ran:

- `python scripts/print_launch_plan.py --config configs/edge.yaml`

Confirmed:

- the script works as a direct operator-facing entry point
- the edge plan is emitted as machine-readable JSON
- startup order is explicit
- repo-owned and external/manual steps are clearly distinguished

## Current Branch

- `main`

## Full Git Status --short --branch

```text
## main...origin/main [ahead 22]
 M docs/DEV_WORKFLOW.md
?? coordination/
```

## Commit Hash

- `ed258a8d838df0a8deb06c0b99a6c2a66f3d6a56`

## Staged / Committed State

- Round 021 code bundle: committed
- `coordination/latest_result.md`: updated locally after commit, not staged
- Unrelated local modification in `docs/DEV_WORKFLOW.md` remains untouched

## Blockers, Risks, Or Remaining Gaps Before Real Orin NX Or Hardware-Backed Deployment

- The launch plan is descriptive, not supervisory.
- It does not yet:
  - start processes automatically
  - monitor them
  - restart them
  - package them as services
- True edge bring-up still depends on:
  - real hardware pose integration
  - real audio device path
  - real process supervision/packaging choices later
- The current plan is intentionally narrow so startup knowledge is centralized without turning this round into a full launcher framework.
