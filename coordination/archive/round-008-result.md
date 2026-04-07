# Current Round Result

## Round
Round 008 - Isaac Source Contract And Stub Adapter

## Summary

- Status: PASSED
- The repository now contains an explicit Isaac-oriented source contract in the simulator-side publisher layer.
- A non-SDK stub implementation path can now emit richer payloads through the existing publisher bridge runtime without changing the HTTP bridge contract.
- Manual validation confirmed the Isaac-oriented stub source can drive narration through the existing HTTP sim path.

## What I Changed

- Added an explicit Isaac-oriented source module:
  - `services/sim_publisher_bridge/isaac_source.py`
- Added a stub observation fixture:
  - `content/sim/demo_isaac_stub_pose_stream.yaml`
- Added a runnable demo for the Isaac-oriented stub path:
  - `scripts/run_isaac_stub_bridge_demo.py`
- Added focused contract documentation:
  - `docs/ISAAC_SOURCE_CONTRACT.md`
- Updated the publisher bridge runtime doc:
  - `docs/SIM_PUBLISHER_BRIDGE_RUNTIME.md`
- Added automated tests for:
  - iterable Isaac observations
  - YAML-backed Isaac observations
  - Isaac stub adaptation into richer payloads
  - end-to-end bridge runtime execution with the Isaac-oriented stub path
  in:
  - `tests/test_isaac_stub_source.py`

## Exact Files Changed

- `services/sim_publisher_bridge/isaac_source.py`
- `content/sim/demo_isaac_stub_pose_stream.yaml`
- `scripts/run_isaac_stub_bridge_demo.py`
- `docs/ISAAC_SOURCE_CONTRACT.md`
- `docs/SIM_PUBLISHER_BRIDGE_RUNTIME.md`
- `tests/test_isaac_stub_source.py`
- `coordination/latest_result.md`

## Isaac-Oriented Source Contract Introduced

New Isaac-oriented contract:

- `IsaacObservationSource`
  - file: `services/sim_publisher_bridge/isaac_source.py`
  - method: `iter_observations()`

This contract represents the simulator-side boundary a future direct Isaac adapter should implement.

Expected observation shape in this round:

```json
{
  "label": "gate_approach_isaac_stub",
  "prim_path": "/World/Robot/base_link",
  "frame_id": "odin/base_link",
  "sim_time_sec": 0.1,
  "translation": {
    "x": 0.7,
    "y": 1.8,
    "z": 0.0
  },
  "orientation": {
    "yaw_rad": 0.0
  }
}
```

Concrete non-SDK implementations added:

- `IterableIsaacObservationSource`
- `YamlFileIsaacObservationSource`

Adapter into the existing publisher runtime:

- `IsaacStubPoseSource`

`IsaacStubPoseSource` converts Isaac-oriented observations into the richer payload shape already used by the reusable publisher bridge runtime.

## Stub Source Used For Validation

Manual validation used:

- `YamlFileIsaacObservationSource`
- wrapped by `IsaacStubPoseSource`
- backed by:
  - `content/sim/demo_isaac_stub_pose_stream.yaml`

Example richer payload emitted by the stub adapter:

```json
{
  "label": "gate_approach_isaac_stub",
  "position": {
    "x": 0.7,
    "y": 1.8,
    "z": 0.0
  },
  "orientation": {
    "yaw_rad": 0.0
  },
  "source_metadata": {
    "prim_path": "/World/Robot/base_link",
    "frame_id": "odin/base_link",
    "sim_time_sec": 0.1
  }
}
```

## Normalized Payload Shape Ultimately Sent To The Existing HTTP Bridge

The HTTP bridge contract remained unchanged.
The final normalized payload shape posted to the bridge was:

```json
{
  "x": -1.8,
  "y": -0.7,
  "label": "gate_approach_isaac_stub"
}
```

Observed bridge contract fields stayed:

- required: `x`, `y`
- optional: `label`

## Exact Validation Performed

### Automated

- `python -m unittest tests.test_isaac_stub_source -v`
  - passed
  - `Ran 4 tests ... OK`
- `python -m unittest discover -s tests`
  - passed
  - `Ran 37 tests ... OK`

### Manual HTTP Validation

Started the existing sim ingress server:

```shell
python scripts/run_sim_pose_ingress_server.py --config configs/sim.yaml --host 127.0.0.1 --port 8100
```

Ran the Isaac-oriented stub demo:

```shell
python scripts/run_isaac_stub_bridge_demo.py --base-url http://127.0.0.1:8100
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

Isaac-stub-adapted richer payload sample:

```json
{
  "richer_payload_sample": [
    {
      "label": "gate_approach_isaac_stub",
      "position": {
        "x": 0.7,
        "y": 1.8,
        "z": 0.0
      },
      "orientation": {
        "yaw_rad": 0.0
      },
      "source_metadata": {
        "prim_path": "/World/Robot/base_link",
        "frame_id": "odin/base_link",
        "sim_time_sec": 0.1
      }
    },
    {
      "label": "gate_trigger_edge_isaac_stub",
      "position": {
        "x": 0.0,
        "y": 0.6,
        "z": 0.0
      },
      "orientation": {
        "yaw_rad": 0.1
      },
      "source_metadata": {
        "prim_path": "/World/Robot/base_link",
        "frame_id": "odin/base_link",
        "sim_time_sec": 0.2
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
      "label": "gate_approach_isaac_stub",
      "source_position_z": 0.0,
      "source_yaw": 0.0
    },
    {
      "sim_x": 0.0,
      "sim_y": 0.6,
      "label": "gate_trigger_edge_isaac_stub",
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
      "label": "gate_approach_isaac_stub"
    },
    {
      "x": -0.6,
      "y": 0.0,
      "label": "gate_trigger_edge_isaac_stub"
    }
  ]
}
```

Bridge health observed:

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

Batch acceptance observed:

```json
{
  "ok": true,
  "action": "ingest_pose_batch",
  "accepted_count": 3
}
```

Latest session evidence after the run:

```json
{
  "session_id": "mock_tour_20260405T031411Z",
  "event_count": 12,
  "latest_event_type": "session_finished",
  "latest_narration_text": "Welcome to the East Gate. This first stop introduces the route and confirms that the guided tour can trigger narration as soon as the robot reaches a POI."
}
```

### Narration Trigger Confirmed Through The Existing HTTP Sim Path

Observed narration evidence after the Isaac-oriented stub run:

```text
Welcome to the East Gate. This first stop introduces the route and confirms that the guided tour can trigger narration as soon as the robot reaches a POI.
```

This confirms:

- the explicit Isaac-oriented source contract can feed the publisher runtime
- the stub adapter can emit richer payloads compatible with the existing runtime
- projection and frame transform remained publisher-side
- the HTTP bridge contract remained unchanged
- the downstream tour stack still triggered narration

## Current Branch

- `main`

## Full Git Status --short --branch

```text
## main...origin/main [ahead 9]
 M docs/DEV_WORKFLOW.md
?? coordination/
```

## Commit Hash

- `04f79b36e062511414e6f9f810c1f766d4507ef3`

## Staged / Committed State

- Round 008 code bundle: committed
- `coordination/latest_result.md`: updated locally, not staged
- Unrelated local modification in `docs/DEV_WORKFLOW.md` remains untouched

## Blockers, Risks, Or Remaining Gaps To Direct Isaac Integration

- This round defines the Isaac-oriented source boundary and a stub path, but does not import or run any Isaac SDK packages.
- A real Isaac implementation still needs:
  - an SDK-backed `IsaacObservationSource`
  - lifecycle management for live simulator sampling
  - scene-specific calibration of simulator world coordinates against the configured 2D tour plane
  - decisions on how timestamps and orientation should influence downstream behavior beyond metadata
