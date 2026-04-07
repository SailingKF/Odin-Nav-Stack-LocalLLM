# Current Round Result

## Round
Round 009 - Isaac Live Adapter Import-Safe Skeleton

## Summary

- Status: PASSED
- The repository now contains an import-safe live Isaac adapter skeleton that targets the Isaac-oriented observation contract without requiring Isaac packages to be installed.
- The stub path remains intact and still drives narration through the existing HTTP sim path.
- Availability and missing-dependency behavior are now explicit, test-covered, and config-addressable.

## What I Changed

- Added a dedicated Isaac observation contract module:
  - `services/sim_publisher_bridge/isaac_contract.py`
- Added an import-safe live Isaac adapter skeleton:
  - `services/sim_publisher_bridge/isaac_live.py`
- Extended the Isaac source module with config-driven selection helpers:
  - `build_isaac_observation_source(config)`
  - `build_isaac_pose_source(config)`
  - `describe_isaac_source_selection(config)`
  in:
  - `services/sim_publisher_bridge/isaac_source.py`
- Added a focused live-adapter doc:
  - `docs/ISAAC_LIVE_ADAPTER_SKELETON.md`
- Updated:
  - `docs/ISAAC_SOURCE_CONTRACT.md`
  - `docs/SIM_PUBLISHER_BRIDGE_RUNTIME.md`
  to document the import-safe live path and how it differs from the stub path
- Added `isaac_source` selection config to:
  - `configs/sim.yaml`
- Updated the existing Isaac stub demo runner so it can honor config-based source selection metadata and optional mode override:
  - `scripts/run_isaac_stub_bridge_demo.py`
- Added automated tests for:
  - import safety
  - missing-dependency availability reporting
  - config-driven live-path selection
  - clear runtime failure semantics when live dependencies are missing
  in:
  - `tests/test_isaac_live_adapter.py`

## Exact Files Changed

- `configs/sim.yaml`
- `services/sim_publisher_bridge/isaac_contract.py`
- `services/sim_publisher_bridge/isaac_live.py`
- `services/sim_publisher_bridge/isaac_source.py`
- `scripts/run_isaac_stub_bridge_demo.py`
- `docs/ISAAC_LIVE_ADAPTER_SKELETON.md`
- `docs/ISAAC_SOURCE_CONTRACT.md`
- `docs/SIM_PUBLISHER_BRIDGE_RUNTIME.md`
- `tests/test_isaac_live_adapter.py`
- `coordination/latest_result.md`

## Live-Adapter Skeleton Introduced

New live adapter skeleton:

- `services/sim_publisher_bridge/isaac_live.py`
- `IsaacLiveObservationSource`

Contract it targets:

- `services/sim_publisher_bridge/isaac_contract.py`
- `IsaacObservationSource`

Current constructor inputs:

- `robot_prim_path`
- `frame_id`
- `required_modules`

Current live adapter behavior:

- `availability()` reports dependency readiness
- `iter_observations()` only attempts real Isaac imports after availability passes
- if dependencies are missing, `iter_observations()` raises a clear `RuntimeError`
- if dependencies are present, the skeleton still raises `NotImplementedError` because real live sampling is not filled in yet

## How Availability / Missing Dependency Behavior Works

Availability helper:

- `get_isaac_live_adapter_availability(required_modules=None)`

Current default required modules:

- `omni.isaac.core`
- `omni.isaac.core.utils.stage`

Behavior:

- uses `importlib.util.find_spec(...)`
- catches `ModuleNotFoundError` for dotted packages whose parent package is absent
- returns a structured status object with:
  - `available`
  - `required_modules`
  - `missing_modules`
  - `status`

Observed missing-dependency status on this machine:

```json
{
  "mode": "live",
  "stub_payload_file": null,
  "live": {
    "robot_prim_path": "/World/Robot/base_link",
    "frame_id": "odin/base_link",
    "availability": {
      "available": false,
      "required_modules": [
        "omni.isaac.core",
        "omni.isaac.core.utils.stage"
      ],
      "missing_modules": [
        "omni.isaac.core",
        "omni.isaac.core.utils.stage"
      ],
      "status": "missing_dependencies"
    }
  }
}
```

Observed runtime failure semantics when the live path is selected without Isaac installed:

```text
RuntimeError: Live Isaac adapter is unavailable because required modules are missing: omni.isaac.core, omni.isaac.core.utils.stage
```

This keeps repository use safe:

- importing unrelated modules still works
- importing the live adapter module itself still works
- only actually using the live path surfaces the missing dependency

## Exact Validation Performed

### Automated

- `python -m unittest tests.test_isaac_live_adapter -v`
  - passed
  - `Ran 5 tests ... OK`
- `python -m unittest discover -s tests`
  - passed
  - `Ran 42 tests ... OK`

### Manual Validation

#### 1. Availability Reporting For Live Path

Ran:

```shell
python -c "from services.sim_publisher_bridge.isaac_source import describe_isaac_source_selection; import json; print(json.dumps(describe_isaac_source_selection({'mode':'live','live':{'robot_prim_path':'/World/Robot/base_link','frame_id':'odin/base_link','required_modules':['omni.isaac.core','omni.isaac.core.utils.stage']}}), indent=2))"
```

Observed:

- the module imported successfully
- live-path availability was reported as `missing_dependencies`
- no repository-wide import failure occurred

#### 2. Stub Path Still Works Through Existing HTTP Bridge

Started the existing sim ingress server:

```shell
python scripts/run_sim_pose_ingress_server.py --config configs/sim.yaml --host 127.0.0.1 --port 8100
```

Ran the existing Isaac stub demo with explicit stub selection:

```shell
python scripts/run_isaac_stub_bridge_demo.py --base-url http://127.0.0.1:8100 --mode stub
```

Observed `isaac_source_selection`:

```json
{
  "mode": "stub",
  "stub_payload_file": "content/sim/demo_isaac_stub_pose_stream.yaml",
  "live": {}
}
```

Observed accepted batch:

```json
{
  "ok": true,
  "action": "ingest_pose_batch",
  "accepted_count": 3
}
```

Observed narration evidence after the stub run:

```text
Welcome to the East Gate. This first stop introduces the route and confirms that the guided tour can trigger narration as soon as the robot reaches a POI.
```

This confirms:

- the stub path still works
- the existing publisher bridge runtime still works
- the existing HTTP bridge contract stayed unchanged

## Current Branch

- `main`

## Full Git Status --short --branch

```text
## main...origin/main [ahead 10]
 M docs/DEV_WORKFLOW.md
?? coordination/
```

## Commit Hash

- `6a102ae84cc540dac842c4748839aa000c255bf9`

## Staged / Committed State

- Round 009 code bundle: committed
- `coordination/latest_result.md`: updated locally, not staged
- Unrelated local modification in `docs/DEV_WORKFLOW.md` remains untouched

## Blockers, Risks, Or Remaining Gaps To Direct Live Isaac Integration

- This round intentionally does not install or import real Isaac packages.
- A real live Isaac implementation still needs:
  - SDK-backed observation sampling inside `IsaacLiveObservationSource`
  - lifecycle ownership for simulator callbacks or polling
  - scene-specific calibration from Isaac world coordinates into the configured 2D tour plane
  - decisions on how timestamps and orientation should affect downstream behavior beyond metadata
