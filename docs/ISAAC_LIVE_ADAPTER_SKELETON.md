# Isaac Live Adapter Skeleton

## Purpose

This document defines the import-safe live Isaac adapter skeleton for the simulator-side publisher layer.

The goal is to prepare the repository for future real Isaac integration without breaking environments where Isaac packages are not installed.

## Live Adapter Shape

Live adapter skeleton:

- `services/sim_publisher_bridge/isaac_live.py`
- `IsaacLiveObservationSource`

Contract it targets:

- `services/sim_publisher_bridge/isaac_contract.py`
- `IsaacObservationSource`

The live adapter skeleton accepts:

- `robot_prim_path`
- `frame_id`
- `required_modules`

It exposes:

- `availability()`
- `iter_observations()`

## Import-Safe Behavior

Import safety is preserved by keeping Isaac dependency checks lazy and local to the live path.

Current behavior:

- importing unrelated repository modules does not import Isaac packages
- importing `isaac_live.py` does not require Isaac packages to be installed
- dependency detection uses `importlib.util.find_spec(...)`
- actual Isaac imports only happen inside `iter_observations()` after availability passes

If required Isaac modules are missing:

- `availability()` reports:
  - `available: false`
  - `status: "missing_dependencies"`
  - the exact missing module names
- calling `iter_observations()` raises a clear `RuntimeError`

If required Isaac modules are present:

- the skeleton is allowed to attempt imports
- it still raises `NotImplementedError` because live sampling logic is intentionally not filled in yet

## Configuration Convention

Current configuration convention lives in:

- `configs/sim.yaml`

Relevant section:

```yaml
isaac_source:
  mode: stub
  stub_payload_file: content/sim/demo_isaac_stub_pose_stream.yaml
  live:
    robot_prim_path: /World/Robot/base_link
    frame_id: odin/base_link
    required_modules:
      - omni.isaac.core
      - omni.isaac.core.utils.stage
```

Selection behavior:

- `mode: stub`
  - uses YAML-backed stub observations
- `mode: live`
  - wires the bridge runtime to `IsaacLiveObservationSource`
  - remains import-safe even when Isaac is unavailable

## Wiring Path

The live/stub selection helper lives in:

- `services/sim_publisher_bridge/isaac_source.py`

Helper functions:

- `build_isaac_observation_source(config)`
- `build_isaac_pose_source(config)`
- `describe_isaac_source_selection(config)`

This keeps the rest of the publisher bridge unchanged:

- projection
- frame transform
- HTTP posting

## What Still Remains Before Direct Live Isaac Integration

- actual SDK-backed observation sampling
- scene/runtime lifecycle ownership
- mapping from simulator world coordinates into the configured tour plane
- decisions on how timestamps and orientation should affect downstream behavior
