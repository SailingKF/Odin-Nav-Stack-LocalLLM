# Simulation Pose HTTP Bridge

## Purpose

This document defines the lightweight HTTP transport layer that sits on top of the in-process simulation pose-ingress runtime.

The goal is to let an external simulator-side publisher drive the tour stack across a process boundary without changing `core`.

## Relationship To The Existing Sim Runtime

In-process baseline from Round 003:
- `services/sim_pose_ingress/runtime.py`

HTTP bridge from this round:
- `services/sim_pose_ingress/app.py`

The HTTP service is intentionally thin:
- it creates or receives a `SimPoseIngressRuntime`
- it forwards request payloads into the existing runtime
- it does not create a second orchestration system

## Endpoints

### `GET /health`

Returns bridge/runtime health and the pose-ingress contract summary.

### `POST /runtime/start`

Starts the sim runtime and the background tour loop.

Request body:

```json
{}
```

### `POST /poses`

Pushes one pose payload into the active sim stream.

Request body:

```json
{
  "x": 4.4,
  "y": 1.0,
  "label": "plaza_trigger_edge"
}
```

### `POST /poses/batch`

Pushes multiple pose payloads into the active sim stream.

Request body:

```json
{
  "poses": [
    {
      "x": -0.6,
      "y": 0.0,
      "label": "gate_trigger_edge"
    },
    {
      "x": 0.0,
      "y": 0.0,
      "label": "gate_inside"
    }
  ]
}
```

### `POST /stream/finish`

Closes the current pose stream so the orchestrator loop can finish cleanly.

Request body:

```json
{}
```

### `GET /state`

Returns the current runtime/orchestrator state.

### `GET /session/latest`

Returns the latest session summary.

## Payload Contract

The HTTP payload matches the existing simulation pose-ingress contract:

- required:
  - `x`
  - `y`
- optional:
  - `label`

Current semantics:
- 2D map-frame coordinates
- `label` is only for debugging

If a simulator publishes raw frame coordinates instead of normalized map-frame coordinates:
- normalize them on the publisher side first
- then send the resulting `x`, `y`, and optional `label` to this HTTP bridge
- see `docs/SIM_FRAME_TRANSFORM_CONTRACT.md`

If a simulator publishes a richer payload with nested position/orientation fields:
- project it into planar raw coordinates first
- then run the existing frame transform
- then send the resulting normalized payload to this HTTP bridge
- see `docs/SIM_POSE_PROJECTION_CONTRACT.md`

## Demo Usage

Start the bridge:

```shell
python scripts/run_sim_pose_ingress_server.py
```

Post the demo stream:

```shell
python scripts/post_sim_pose_stream.py
```

Post a raw simulator-style stream through the publisher transform layer:

```shell
python scripts/post_sim_raw_pose_stream.py
```

## What Still Remains Before Real Isaac Sim Integration

- actual simulator-side transport or publisher process
- coordinate-frame alignment from Isaac Sim output into tour map coordinates
- any timestamp or replay semantics beyond the current minimal payload
- longer-lived session and reconnect behavior
