# Current Round Result

## Round
Round 005 - Simulation Frame Transform And Publisher Baseline

## Summary

- Status: PASSED
- The repository now contains a publisher-side transform seam for raw simulator coordinates.
- The HTTP bridge contract remains unchanged and still accepts normalized map-frame `x`, `y`, and optional `label`.
- A raw simulator-style pose sequence was transformed and posted over the existing HTTP bridge, and it triggered narration through the sim path.

## What I Changed

- Added a publisher-side transform module in `adapters/sim/frame_transform.py`.
  - supports:
    - `raw_x_field`
    - `raw_y_field`
    - `swap_axes`
    - `flip_x`
    - `flip_y`
    - `scale`
    - `offset_x`
    - `offset_y`
- Added transform configuration under `configs/sim.yaml` as `publisher_frame_transform`.
- Added a distinct raw simulator demo payload file:
  - `content/sim/demo_raw_pose_stream.yaml`
- Added a publisher-side client utility:
  - `scripts/post_sim_raw_pose_stream.py`
  - loads raw simulator payloads
  - applies the configured transform
  - posts normalized poses to the existing HTTP bridge
- Added focused transform documentation:
  - `docs/SIM_FRAME_TRANSFORM_CONTRACT.md`
- Updated:
  - `docs/SIM_POSE_HTTP_BRIDGE.md`
  - `docs/SIM_POSE_INGRESS_CONTRACT.md`
  so the transform seam is clearly connected to the existing sim-ingress HTTP path
- Added automated tests for transform behavior and publisher-side normalization:
  - `tests/test_sim_frame_transform.py`

## Exact Files Changed

- `configs/sim.yaml`
- `adapters/sim/frame_transform.py`
- `content/sim/demo_raw_pose_stream.yaml`
- `scripts/post_sim_raw_pose_stream.py`
- `docs/SIM_FRAME_TRANSFORM_CONTRACT.md`
- `docs/SIM_POSE_HTTP_BRIDGE.md`
- `docs/SIM_POSE_INGRESS_CONTRACT.md`
- `tests/test_sim_frame_transform.py`
- `coordination/latest_result.md`

## Raw Payload Shape Used

Raw simulator payload shape used in this round:

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

Optional raw field:
- `label`

## Transform Configuration Used

Transform configuration used for validation:

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

Effective mapping in this round:

```text
normalized.x = -raw.sim_y
normalized.y = -raw.sim_x
```

## Normalized Payload Shape Sent To The HTTP Bridge

Normalized payload shape sent to the existing bridge remained:

```json
{
  "x": -1.8,
  "y": -0.7,
  "label": "gate_approach_raw"
}
```

The server contract did not change:
- `x`
- `y`
- optional `label`

## Exact Validation Performed

### Automated

- `python -m unittest tests.test_sim_frame_transform -v`
  - passed
  - `Ran 3 tests ... OK`
- `python -m unittest discover -s tests`
  - passed
  - `Ran 27 tests ... OK`

### Manual HTTP Validation

Started the existing bridge:

```shell
python scripts/run_sim_pose_ingress_server.py --config configs/sim.yaml --host 127.0.0.1 --port 8100
```

Ran the publisher-side raw transform client:

```shell
python scripts/post_sim_raw_pose_stream.py --base-url http://127.0.0.1:8100
```

### Exact Raw Sample Printed During Validation

```json
{
  "raw_payload_sample": [
    {
      "sim_x": 0.7,
      "sim_y": 1.8,
      "label": "gate_approach_raw"
    },
    {
      "sim_x": 0.0,
      "sim_y": 0.6,
      "label": "gate_trigger_edge_raw"
    }
  ]
}
```

### Exact Normalized Sample Printed During Validation

```json
{
  "normalized_payload_sample": [
    {
      "x": -1.8,
      "y": -0.7,
      "label": "gate_approach_raw"
    },
    {
      "x": -0.6,
      "y": 0.0,
      "label": "gate_trigger_edge_raw"
    }
  ]
}
```

### HTTP Bridge Validation Result

Observed bridge health:

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

Observed transformed publisher run:
- runtime started successfully
- transformed batch of 6 normalized poses was accepted
- session finished cleanly
- `GET /state` and `GET /session/latest` showed triggered narration text

### Narration Trigger Confirmed After Transformation

At least one POI trigger and narration occurred after transformation through the existing HTTP sim path.

Observed narration evidence after transformed upload:

```text
This central plaza is the mid-route checkpoint in the demo tour. It helps us verify that state transitions and narration continue cleanly after the first stop.
```

This confirms:
- raw simulator-style payloads were transformed publisher-side
- normalized payloads were posted to the unchanged HTTP bridge
- the tour stack still triggered narration

## Current Branch

- `main`

## Full Git Status --short --branch

```text
## main...origin/main [ahead 6]
 M docs/DEV_WORKFLOW.md
?? coordination/
```

## Commit Hash

- `0a9b170682040b5f866349808a28c8e2ccd05eec`

## Staged / Committed State

- Work for this round: committed
- `coordination/latest_result.md`: updated locally, not staged
- Unrelated local modification still exists in `docs/DEV_WORKFLOW.md` and was intentionally left untouched

## Blockers, Risks, Or Remaining Gaps To Real Isaac Sim Integration

- This round only adds a 2D publisher-side normalization seam; it does not integrate with the Isaac SDK.
- Real Isaac work will still need:
  - actual simulator pose extraction
  - frame verification against the map used by the tour
  - a decision on how 3D sim pose projects into the tour's 2D map coordinates
  - any timestamp, sequencing, or reconnect semantics beyond this minimal baseline
