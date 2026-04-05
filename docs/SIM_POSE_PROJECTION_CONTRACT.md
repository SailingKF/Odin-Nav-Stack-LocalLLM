# Simulation Pose Projection Contract

## Purpose

This document defines the publisher-side projection seam that converts richer simulator-style payloads into planar raw coordinates before the existing frame-transform seam runs.

The final HTTP bridge contract remains unchanged:
- `x`
- `y`
- optional `label`

## Where This Logic Lives

Projection module:
- `adapters/sim/projection.py`

Projection-aware publisher utility:
- `scripts/post_sim_projected_pose_stream.py`

Existing transform seam:
- `adapters/sim/frame_transform.py`

Existing HTTP bridge:
- `services/sim_pose_ingress/app.py`

## Richer Raw Payload Shape Used In This Round

```json
{
  "label": "gate_approach_richer",
  "position": {
    "x": 0.7,
    "y": 1.8,
    "z": 0.0
  },
  "orientation": {
    "yaw_rad": 0.0
  }
}
```

Required richer fields used in this round:
- `position.x`
- `position.y`

Optional richer fields captured for future-proofing:
- `position.z`
- `orientation.yaw_rad`
- `label`

## Projection Configuration Semantics

Current configuration lives in:
- `configs/sim.yaml`

Shape:

```yaml
publisher_pose_projection:
  projected_x_field: sim_x
  projected_y_field: sim_y
  planar_x_source_path: position.x
  planar_y_source_path: position.y
  planar_z_source_path: position.z
  yaw_source_path: orientation.yaw_rad
  label_field: label
```

Semantics:
- `projected_x_field`, `projected_y_field`
  - names of the intermediate planar payload fields produced by projection
- `planar_x_source_path`, `planar_y_source_path`
  - dotted paths into the richer simulator payload
- `planar_z_source_path`
  - optional extra position field retained for traceability
- `yaw_source_path`
  - optional orientation field retained for traceability
- `label_field`
  - label copied into the projected payload when present

## Relationship Between Projection And Frame Transform

Step 1. Projection:
- richer payload
- produces an intermediate planar payload such as:

```json
{
  "sim_x": 0.7,
  "sim_y": 1.8,
  "label": "gate_approach_richer",
  "source_position_z": 0.0,
  "source_yaw": 0.0
}
```

Step 2. Existing frame transform:
- consumes `sim_x` and `sim_y`
- outputs the final normalized bridge payload such as:

```json
{
  "x": -1.8,
  "y": -0.7,
  "label": "gate_approach_richer"
}
```

Projection chooses which richer fields define the 2D plane.
Frame transform then aligns that 2D plane to the tour map coordinates.

## Normalized Payload Sent To The HTTP Bridge

The HTTP bridge still receives only:

```json
{
  "x": -1.8,
  "y": -0.7,
  "label": "gate_approach_richer"
}
```

## What Still Remains Before Direct Isaac SDK Hookup

- actual Isaac SDK data extraction
- final choice of which 3D simulator plane should map to the tour’s 2D map plane
- confirmation of axis conventions between Isaac and the tour map
- richer orientation usage if the project later needs heading-aware behavior
- timing, replay, and lifecycle behavior beyond this baseline
