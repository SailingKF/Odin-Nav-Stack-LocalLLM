# MVSim Minimal Integration

## Purpose

This document defines the narrow MVSim-oriented simulator integration surface introduced for PC-side end-to-end validation.

The goal is not to embed a full MVSim product runtime in this repository yet.
The goal is to prove that an external planar simulator path can drive:

- the existing sim pose-ingress HTTP contract
- the current tour/orchestrator flow
- the current session/narration pipeline
- the current `/debug`-backed operator surfaces

without depending on Isaac.

## What This Round Uses

Current integration shape:

- a real external HTTP pose-ingress path
- a thin MVSim-oriented compatibility shim on the simulator side
- a sim-aware API proxy mode for `/debug`

## What Is Real Versus Compatibility Scaffolding

### Real in this round

- real posting into the existing external sim-ingress HTTP contract:
  - `/runtime/start`
  - `/poses/batch`
  - `/stream/finish`
- real downstream tour execution:
  - POI triggers
  - narration flow
  - session logging
  - state and latest-session inspection
- real `/debug` observation path through the API server when it runs with `configs/sim.yaml`

### Compatibility shim in this round

- `services/sim_publisher_bridge/mvsim_source.py`
- `content/sim/demo_mvsim_pose_stream.yaml`

This shim models MVSim-style planar vehicle observations:

- `pose2d`
- `velocity2d`
- `vehicle`
- `sim_time_sec`

and converts them into the richer publisher payload shape already consumed by the existing projection/transform/HTTP bridge.

This means:

- the simulator-side semantics are MVSim-oriented
- the HTTP validation path is real
- but this round does **not** claim a direct live MVSim process integration

## Implementation Location

MVSim-oriented source/seam:

- `services/sim_publisher_bridge/mvsim_source.py`

Runnable demo entry point:

- `scripts/run_mvsim_compat_bridge_demo.py`

Sample observation stream:

- `content/sim/demo_mvsim_pose_stream.yaml`

API proxy mode used by `/debug` in sim profile:

- `services/api_server/runtime.py`

## Current PC Validation Flow

### Terminal 1

```text
python scripts/run_sim_pose_ingress_server.py --config configs/sim.yaml --host 127.0.0.1 --port 8100
```

### Terminal 2

```text
python scripts/run_api_server.py --config configs/sim.yaml --host 127.0.0.1 --port 8000
```

### Terminal 3

```text
python scripts/run_mvsim_compat_bridge_demo.py --config configs/sim.yaml --base-url http://127.0.0.1:8100
```

### Optional browser check

Open:

- `http://127.0.0.1:8000/debug`

Keep the default API base URL because the sim-profile API server now proxies to the running sim-ingress runtime.

## What The Demo Verifies

Current demo verifies:

- simulator-side planar observation playback
- HTTP bridge start
- batch pose ingest
- stream finish
- POI triggering across the full demo route
- final session summary
- `/debug`-compatible API state/session surfaces
- follow-up question handling after sim-driven narration

## What Still Remains Before Map-Format Or ROS Work

- direct live MVSim runtime/process adapter, if we later need it
- explicit scene/map binding between simulator worlds and tour maps
- richer timing/clock semantics
- ROS-side simulator formalization
- map-format or occupancy-map integration

This round intentionally stops before all of those.
