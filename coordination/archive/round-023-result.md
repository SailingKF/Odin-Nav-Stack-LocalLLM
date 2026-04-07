# Current Round Result

## Round
Round 023 - Deployment Command Manifest And Guided Bring-Up Sheet Baseline

## Summary

- Status: PASSED
- The repository now contains an explicit deployment command-manifest layer for `dev`, `sim`, and `edge`.
- Repo-owned bring-up commands are now derived from one reusable service-layer seam instead of being scattered across docs and startup hints.
- Existing runtime/API surfaces now expose `deployment_command_manifest`.
- Operators can now print a guided bring-up sheet that combines:
  - launch order
  - readiness state
  - repo-owned command mapping
  - manual/external steps with no repo command

## What I Changed

- Added a focused command-manifest module in:
  - `services/deployment_profile/command_manifest.py`
- Exported it through:
  - `services/deployment_profile/__init__.py`
- Wired command-manifest exposure into runtime-facing services:
  - `services/api_server/runtime.py`
  - `services/sim_pose_ingress/runtime.py`
- Extended the API server entrypoint so config-specific bring-up commands are explicit:
  - `scripts/run_api_server.py`
- Added an operator-facing guided bring-up script:
  - `scripts/print_bringup_sheet.py`
- Added focused command-manifest tests in:
  - `tests/test_deployment_command_manifest.py`
- Extended API/runtime tests in:
  - `tests/test_api_server.py`
- Updated docs:
  - `README.md`
  - `docs/DEPLOYMENT.md`
  - `docs/DEPLOYMENT_LAUNCH_PLAN_CONTRACT.md`
  - `docs/DEPLOYMENT_COMMAND_MANIFEST_CONTRACT.md`

## Exact Files Changed

- `README.md`
- `docs/DEPLOYMENT.md`
- `docs/DEPLOYMENT_LAUNCH_PLAN_CONTRACT.md`
- `docs/DEPLOYMENT_COMMAND_MANIFEST_CONTRACT.md`
- `scripts/run_api_server.py`
- `scripts/print_bringup_sheet.py`
- `services/api_server/runtime.py`
- `services/deployment_profile/__init__.py`
- `services/deployment_profile/command_manifest.py`
- `services/sim_pose_ingress/runtime.py`
- `tests/test_api_server.py`
- `tests/test_deployment_command_manifest.py`
- `coordination/latest_result.md` updated locally after commit only, not staged

## What Deployment Command-Manifest Or Bring-Up-Guide Surface I Introduced

New runtime-visible surface:

- `deployment_command_manifest`

Current top-level fields:

- `profile_name`
- `automation_level`
- `config_path`
- `commands`
- `steps`
- `command_count`
- `repo_command_step_count`
- `manual_step_count`

Each repo-owned command currently exposes:

- `command_id`
- `step_id`
- `order`
- `profile_name`
- `command_kind`
- `entrypoint_path`
- `argv`
- `display_command`
- `config_path`
- `description`
- `owned_by_repo`

Each launch-plan step is also summarized in the manifest with:

- `step_id`
- `order`
- `name`
- `category`
- `required`
- `action_type`
- `command_available`
- `command_id`
- `operator_action`
- `detail`
- `startup_hint`

Current action types:

- `repo_command`
- `manual_external`
- `manual_optional`

Operator-facing guided bring-up entry point:

- `scripts/print_bringup_sheet.py`

This sheet combines:

- launch plan order
- readiness status
- repo-owned commands when available
- blocking reasons when present

## How Internal Startup Steps Are Now Mapped To Concrete Repo-Owned Commands

The current mapping is derived in one place:

- `services/deployment_profile/command_manifest.py`

It reuses launch-plan `step_id` values and maps known repo-owned steps to explicit script commands.

Current repo-owned mappings:

### dev

- `llm_gateway`
  - `python scripts/run_llm_gateway.py --config configs/dev.yaml`
- `api_server`
  - `python scripts/run_api_server.py --config configs/dev.yaml`

### sim

- `sim_pose_ingress_server`
  - `python scripts/run_sim_pose_ingress_server.py --config configs/sim.yaml`
- `api_server`
  - `python scripts/run_api_server.py --config configs/sim.yaml`

### edge

- `llm_gateway`
  - `python scripts/run_llm_gateway.py --config configs/edge.yaml`
- `api_server`
  - `python scripts/run_api_server.py --config configs/edge.yaml`

This round also made one supporting CLI improvement:

- `scripts/run_api_server.py` now accepts `--config`

That keeps API-server commands profile-specific without adding a new launcher framework.

## Which Current Steps Still Remain Manual/External With No Repo Command

Current manual or external steps remain explicit and intentionally have no repo command:

### dev

- `ollama_runtime`
- `debug_browser`

### sim

- `isaac_live_dependency`
- `isaac_stub_source`
- `sim_publisher_bridge`

`sim_publisher_bridge` remains non-commanded in this round because the repo currently exposes it as focused demo/runtime validation scripts rather than a stable always-on operator bring-up service.

### edge

- `hardware_pose_dependency`
- `ollama_runtime`
- `audio_device_dependency`

This keeps the boundary clear:

- repo-owned internal services map to concrete repo commands
- hardware/runtime/browser/manual steps remain visible but do not pretend to be auto-startable by the repo

## How Operators Can Inspect The Command Manifest Or Guided Bring-Up Sheet Now

### API Surfaces

Operators can inspect:

- `deployment_command_manifest`

through:

- API `health`
- API `state`
- sim ingress runtime `health`
- sim ingress runtime `state`

### Script Entry Point

Operators can now run:

```text
python scripts/print_bringup_sheet.py --config configs/dev.yaml
python scripts/print_bringup_sheet.py --config configs/sim.yaml
python scripts/print_bringup_sheet.py --config configs/edge.yaml
```

The output is machine-readable JSON and makes these points explicit in one place:

- ordered step list
- current readiness per step
- whether a repo command exists
- exact command string when it does
- blockers when a step is currently blocked

## Exact Validation Performed

### Automated

- `python -m unittest tests.test_deployment_command_manifest -v`
  - passed
  - `Ran 3 tests ... OK`
- `python -m unittest tests.test_api_server -v`
  - passed
  - `Ran 6 tests ... OK`
- `python -m unittest discover -s tests`
  - passed
  - `Ran 80 tests ... OK`

Focused coverage now includes:

- `dev` manifest mapping `llm_gateway` and `api_server` to repo commands
- `sim` manifest leaving external/live and unmapped optional steps without repo commands
- `edge` guided bring-up sheet combining readiness blockers with repo command display
- runtime/API exposure of `deployment_command_manifest`

### Manual

Ran:

- `python scripts/print_bringup_sheet.py --config configs/edge.yaml`
- `python scripts/print_bringup_sheet.py --config configs/dev.yaml`

Confirmed for `edge`:

- `hardware_pose_dependency` shows `manual_external`
- `llm_gateway` shows `repo_command`
- `api_server` shows `repo_command`
- `audio_device_dependency` shows `manual_optional`
- `overall_status` stays `blocked`
- the current blocker is still explicit:
  - `llm_gateway is unreachable: url error: timed out`

Confirmed for `dev`:

- `llm_gateway` and `api_server` resolve to explicit repo command strings
- `debug_browser` stays optional/manual with no repo command

## Current Branch

- `main`

## Full Git Status --short --branch

```text
## main...origin/main [ahead 24]
 M docs/DEV_WORKFLOW.md
?? coordination/
```

## Commit Hash

- `f6acd507cbbbc632d5004f3c84b8d276ef92d4b6`

## Staged / Committed State

- Round 023 code bundle: committed
- `coordination/latest_result.md`: updated locally after commit, not staged
- Unrelated local modification in `docs/DEV_WORKFLOW.md` remains untouched
- `coordination/` remains outside this commit, per handoff rule

## Blockers, Risks, Or Remaining Gaps Before Real Orin NX Or Hardware-Backed Deployment

- The command manifest is still descriptive; it is not a launcher.
- It does not yet:
  - execute commands
  - supervise running services
  - retry failed services
  - package startup for Orin NX
- Some launch-plan steps still intentionally have no repo command because they are:
  - external runtime dependencies
  - browser/manual operator actions
  - still exposed only as focused validation demos rather than stable bring-up services
- Current `edge` remains not truly field-ready because:
  - hardware pose is still external/manual
  - audio device readiness is still mock/not-applicable
  - `llm_gateway` must actually be up to clear the current blocker
- This round stops at the intended narrow seam: one reusable command manifest plus guided bring-up output, without broadening into automatic startup management.
