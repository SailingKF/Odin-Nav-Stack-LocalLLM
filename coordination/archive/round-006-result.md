# Current Round Result

## Round
Round 006 - Isaac-Style Pose Projection Contract

## Summary

- Status: PASSED
- The repository now contains a publisher-side projection seam for richer simulator-style payloads.
- Richer nested pose payloads can be projected into planar raw coordinates, then passed through the existing frame-transform seam, and finally posted to the unchanged HTTP bridge contract.
- Manual validation confirmed that projected richer payloads still trigger narration through the existing HTTP sim path.

## What I Changed

- Added a publisher-side projection module:
  - `adapters/sim/projection.py`
- Added projection config under `configs/sim.yaml` as `publisher_pose_projection`
- Added a richer simulator demo payload file:
  - `content/sim/demo_richer_pose_stream.yaml`
- Added a projection-aware publisher client:
  - `scripts/post_sim_projected_pose_stream.py`
- Added a focused projection contract doc:
  - `docs/SIM_POSE_PROJECTION_CONTRACT.md`
- Updated:
  - `docs/SIM_FRAME_TRANSFORM_CONTRACT.md`
  - `docs/SIM_POSE_HTTP_BRIDGE.md`
  - `docs/SIM_POSE_INGRESS_CONTRACT.md`
  so the relationship between richer payload projection, planar raw transform, and normalized HTTP posting is explicit
- Added automated projection tests:
  - `tests/test_sim_projection.py`

## Exact Files Changed

- `configs/sim.yaml`
- `adapters/sim/projection.py`
- `content/sim/demo_richer_pose_stream.yaml`
- `scripts/post_sim_projected_pose_stream.py`
- `docs/SIM_POSE_PROJECTION_CONTRACT.md`
- `docs/SIM_FRAME_TRANSFORM_CONTRACT.md`
- `docs/SIM_POSE_HTTP_BRIDGE.md`
- `docs/SIM_POSE_INGRESS_CONTRACT.md`
- `tests/test_sim_projection.py`
- `coordination/latest_result.md`

## Richer Raw Payload Shape Used

Richer raw payload shape used in this round:

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

## Projection Configuration Used

Projection configuration used in validation:

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

This round's projection step produced an intermediate planar payload like:

```json
{
  "sim_x": 0.7,
  "sim_y": 1.8,
  "label": "gate_approach_richer",
  "source_position_z": 0.0,
  "source_yaw": 0.0
}
```

## Normalized Payload Shape Sent To The HTTP Bridge

The HTTP bridge contract remained unchanged.
The final normalized payload shape sent to the bridge was:

```json
{
  "x": -1.8,
  "y": -0.7,
  "label": "gate_approach_richer"
}
```

The bridge still receives only:
- `x`
- `y`
- optional `label`

## Exact Validation Performed

### Automated

- `python -m unittest tests.test_sim_projection -v`
  - passed
  - `Ran 3 tests ... OK`
- `python -m unittest discover -s tests`
  - passed
  - `Ran 30 tests ... OK`

### Manual HTTP Validation

Started the existing bridge:

```shell
python scripts/run_sim_pose_ingress_server.py --config configs/sim.yaml --host 127.0.0.1 --port 8100
```

Ran the projection-aware publisher client:

```shell
python scripts/post_sim_projected_pose_stream.py --base-url http://127.0.0.1:8100
```

### Exact Samples Printed During Validation

Projection config:

```json
{
  "projection_config": {
    "projected_x_field": "sim_x",
    "projected_y_field": "sim_y",
    "planar_x_source_path": "position.x",
    "planar_y_source_path": "position.y",
    "planar_z_source_path": "position.z",
    "yaw_source_path": "orientation.yaw_rad",
    "label_field": "label"
  }
}
```

Transform config:

```json
{
  "transform_config": {
    "raw_x_field": "sim_x",
    "raw_y_field": "sim_y",
    "swap_axes": true,
    "flip_x": true,
    "flip_y": true,
    "scale": 1.0,
    "offset_x": 0.0,
    "offset_y": 0.0
  }
}
```

Richer raw sample:

```json
{
  "richer_payload_sample": [
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
    },
    {
      "label": "gate_trigger_edge_richer",
      "position": {
        "x": 0.0,
        "y": 0.6,
        "z": 0.0
      },
      "orientation": {
        "yaw_rad": 0.1
      }
    }
  ]
}
```

Projected planar sample:

```json
{
  "projected_payload_sample": [
    {
      "sim_x": 0.7,
      "sim_y": 1.8,
      "label": "gate_approach_richer",
      "source_position_z": 0.0,
      "source_yaw": 0.0
    },
    {
      "sim_x": 0.0,
      "sim_y": 0.6,
      "label": "gate_trigger_edge_richer",
      "source_position_z": 0.0,
      "source_yaw": 0.1
    }
  ]
}
```

Normalized bridge sample:

```json
{
  "normalized_payload_sample": [
    {
      "x": -1.8,
      "y": -0.7,
      "label": "gate_approach_richer"
    },
    {
      "x": -0.6,
      "y": 0.0,
      "label": "gate_trigger_edge_richer"
    }
  ]
}
```

### HTTP Validation Outcome

Observed bridge health stayed unchanged:

```json
{
  "status": "ok",
  "service": "sim-pose-ingress-runtime",
  "env_name": "sim",
  "pose_provider_type": "sim_ingress",
  "narrator_type": "mock",
  "ingress_contract": {
    "required_fields": ["x", "y"],
    "optional_fields": ["label"]
  }
}
```

Observed projected publisher run:
- runtime started successfully
- projected + normalized batch of 6 poses was accepted
- session finished cleanly
- `GET /state` and `GET /session/latest` showed triggered narration text

### Narration Trigger Confirmed After Projection

At least one POI trigger and narration occurred after projection through the existing HTTP sim path.

Observed narration evidence after projected upload:

```text
This central plaza is the mid-route checkpoint in the demo tour. It helps us verify that state transitions and narration continue cleanly after the first stop.
```

This confirms:
- richer nested simulator payloads were projected publisher-side
- projected planar payloads were transformed with the existing frame-transform seam
- normalized payloads were posted to the unchanged HTTP bridge
- the tour stack still triggered narration

## Current Branch

- `main`

## Full Git Status --short --branch

```text
## main...origin/main [ahead 7]
 M docs/DEV_WORKFLOW.md
?? coordination/
```

## Commit Hash

- `23763ee6ec399707b1969022f96f9209f5260956`

## Staged / Committed State

- Work for this round: committed
- `coordination/latest_result.md`: updated locally, not staged
- Unrelated local modification still exists in `docs/DEV_WORKFLOW.md` and was intentionally left untouched

## Blockers, Risks, Or Remaining Gaps To Direct Isaac Integration

- This round defines a publisher-side projection contract but does not integrate the Isaac SDK itself.
- Real Isaac integration still needs:
  - actual pose extraction from the simulator runtime
  - a final decision on which 3D plane projects into the tour's 2D map plane
  - validation of axis conventions against the real simulator scene
  - any future use of orientation beyond traceability
  - timing, replay, and lifecycle behavior beyond this baseline
