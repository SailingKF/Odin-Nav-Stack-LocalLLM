# Current Round Result

## Round
Round 007 - Simulator Publisher Bridge Runtime Skeleton

## Summary

- Status: PASSED
- The repository now contains a reusable simulator-side publisher bridge runtime that composes the existing projection, frame transform, and HTTP ingress seams.
- A clean pose-source abstraction now exists outside `core`, with both iterable and YAML-backed richer-payload sources for non-Isaac validation.
- Manual validation confirmed the new bridge runtime can drive narration through the unchanged HTTP sim bridge contract.

## What I Changed

- Added a simulator-side publisher bridge package:
  - `services/sim_publisher_bridge/__init__.py`
  - `services/sim_publisher_bridge/source.py`
  - `services/sim_publisher_bridge/http_client.py`
  - `services/sim_publisher_bridge/runtime.py`
- Added a reusable demo entrypoint:
  - `scripts/run_sim_publisher_bridge_demo.py`
- Added focused docs for the new runtime shape:
  - `docs/SIM_PUBLISHER_BRIDGE_RUNTIME.md`
- Added automated tests covering:
  - pose-source abstraction behavior
  - end-to-end bridge runtime behavior against the existing HTTP bridge app
  - file-backed richer-payload loading
  in:
  - `tests/test_sim_publisher_bridge.py`

## Exact Files Changed

- `services/sim_publisher_bridge/__init__.py`
- `services/sim_publisher_bridge/source.py`
- `services/sim_publisher_bridge/http_client.py`
- `services/sim_publisher_bridge/runtime.py`
- `scripts/run_sim_publisher_bridge_demo.py`
- `docs/SIM_PUBLISHER_BRIDGE_RUNTIME.md`
- `tests/test_sim_publisher_bridge.py`
- `coordination/latest_result.md`

## Pose-Source Abstraction Introduced

New simulator-side pose-source abstraction:

- `SimulatorPoseSource`
  - exposes `iter_payloads()`
  - returns richer simulator payload dictionaries
  - stays outside `core`
  - is the explicit future seam for direct Isaac-side data extraction

Concrete baseline implementations added:

- `IterableSimulatorPoseSource`
  - lightweight in-memory/demo source
- `YamlFileRicherPoseSource`
  - file-backed richer-payload source for validation without Isaac SDK

## Concrete Baseline Source Used For Validation

Manual validation used:

- `YamlFileRicherPoseSource`
- richer payload file:
  - `content/sim/demo_richer_pose_stream.yaml`

Example richer payload shape read from the source:

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

## Normalized Payload Shape Ultimately Sent To The Existing HTTP Bridge

The downstream HTTP bridge contract remained unchanged.
The bridge runtime ultimately posted normalized payloads shaped like:

```json
{
  "x": -1.8,
  "y": -0.7,
  "label": "gate_approach_richer"
}
```

Bridge contract fields still observed:

- required: `x`, `y`
- optional: `label`

## Exact Validation Performed

### Automated

- `python -m unittest tests.test_sim_publisher_bridge -v`
  - passed
  - `Ran 3 tests ... OK`
- `python -m unittest discover -s tests`
  - passed
  - `Ran 33 tests ... OK`

### Manual HTTP Validation

Started the existing sim ingress HTTP bridge:

```shell
python scripts/run_sim_pose_ingress_server.py --config configs/sim.yaml --host 127.0.0.1 --port 8100
```

Ran the new simulator-side bridge runtime demo:

```shell
python scripts/run_sim_publisher_bridge_demo.py --base-url http://127.0.0.1:8100
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

Richer payload sample:

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

Projected sample:

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

Normalized sample:

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

Bridge health observed during validation:

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

Bridge runtime accepted the posted batch:

```json
{
  "ok": true,
  "action": "ingest_pose_batch",
  "accepted_count": 6
}
```

Latest session evidence after the run:

```json
{
  "session_id": "mock_tour_20260405T030105Z",
  "event_count": 21,
  "latest_event_type": "session_finished",
  "latest_narration_text": "This central plaza is the mid-route checkpoint in the demo tour. It helps us verify that state transitions and narration continue cleanly after the first stop."
}
```

### Narration Trigger Confirmed Through The Existing HTTP Sim Path

Observed narration evidence after the bridge runtime run:

```text
This central plaza is the mid-route checkpoint in the demo tour. It helps us verify that state transitions and narration continue cleanly after the first stop.
```

This confirms:

- richer simulator payloads were read from a source abstraction
- projection stayed publisher-side
- frame transform stayed publisher-side
- normalized payloads were posted to the unchanged HTTP bridge contract
- the downstream tour stack still triggered narration

## Current Branch

- `main`

## Full Git Status --short --branch

```text
## main...origin/main [ahead 8]
 M docs/DEV_WORKFLOW.md
?? coordination/
```

## Commit Hash

- `d47e8462e55c276237fda85bd5759814c72d6c8f`

## Staged / Committed State

- Round 007 code bundle: committed
- `coordination/latest_result.md`: updated locally, not staged
- Unrelated local modification in `docs/DEV_WORKFLOW.md` remains untouched

## Blockers, Risks, Or Remaining Gaps To Direct Isaac Integration

- This round adds the process shape for simulator-side publishing but does not integrate the Isaac SDK itself.
- A real Isaac implementation still needs:
  - an actual Isaac-backed `SimulatorPoseSource`
  - lifecycle and threading decisions for live simulator feeds
  - scene-specific frame/projection calibration against the real simulation world
  - error handling for long-running streams and reconnect behavior
  - any future use of orientation beyond traceability metadata
