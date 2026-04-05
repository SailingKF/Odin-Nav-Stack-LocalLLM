# Simulation Frame Transform Contract

## Purpose

This document defines the publisher-side transform seam that converts raw simulator-frame 2D poses into the normalized map-frame payload already accepted by the HTTP sim-ingress bridge.

The server contract remains unchanged.
Frame conversion happens before the HTTP request is sent.

## Where This Logic Lives

Publisher-side transform module:
- `adapters/sim/frame_transform.py`

Publisher-side HTTP client:
- `scripts/post_sim_raw_pose_stream.py`

Existing normalized HTTP bridge:
- `services/sim_pose_ingress/app.py`

If the simulator publishes a richer nested payload first:
- project it with `adapters/sim/projection.py`
- then apply this frame transform seam
- see `docs/SIM_POSE_PROJECTION_CONTRACT.md`

## Raw Simulator Payload Shape Used In This Round

```json
{
  "sim_x": 0.7,
  "sim_y": 1.8,
  "label": "gate_approach_raw"
}
```

Required raw fields:
- `sim_x`
- `sim_y`

Optional raw fields:
- `label`

## Transform Configuration Semantics

Current configuration lives in:
- `configs/sim.yaml`

Shape:

```yaml
publisher_frame_transform:
  raw_x_field: sim_x
  raw_y_field: sim_y
  swap_axes: true
  flip_x: true
  flip_y: true
  scale: 1.0
  offset_x: 0.0
  offset_y: 0.0
```

Semantics:
- `raw_x_field`, `raw_y_field`
  - which raw payload fields to read
- `swap_axes`
  - if true, normalized `x` is sourced from raw `y`, and normalized `y` is sourced from raw `x`
- `flip_x`, `flip_y`
  - negate the selected source axis before scaling
- `scale`
  - applied uniformly to both axes
- `offset_x`, `offset_y`
  - added after swap/flip/scale

## Normalized Payload Shape Sent To The HTTP Bridge

```json
{
  "x": -1.8,
  "y": -0.7,
  "label": "gate_approach_raw"
}
```

The bridge still receives only:
- `x`
- `y`
- optional `label`

## Example Mapping Used In This Round

With:
- `swap_axes: true`
- `flip_x: true`
- `flip_y: true`
- `scale: 1.0`
- no offsets

Then:

```text
normalized.x = -raw.sim_y
normalized.y = -raw.sim_x
```

## What Still Remains Before A Real Isaac Bridge

- actual Isaac Sim pose extraction
- 3D-to-2D projection choices for real sim data
- coordinate-frame verification against the tour map
- timestamp or sequencing semantics beyond the minimal payload
- any simulator-side lifecycle or reconnect handling
