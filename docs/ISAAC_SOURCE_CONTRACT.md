# Isaac Source Contract

## Purpose

This document defines the Isaac-oriented source boundary for the simulator-side publisher layer without importing Isaac SDK packages.

The goal is to make future direct Isaac integration an adapter problem, not a rewrite of:

- `core`
- the publisher bridge runtime
- the sim ingress HTTP bridge

## Contract Shape

Isaac-oriented contract:

- `services/sim_publisher_bridge/isaac_contract.py`
- `IsaacObservationSource`

The contract exposes:

- `iter_observations()`

Each observation is expected to represent one simulator-side robot pose sample with Isaac-style source metadata, for example:

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

Required source responsibilities for a future real Isaac implementation:

- read pose samples from Isaac runtime objects or callbacks
- emit one observation per sample through `iter_observations()`
- include planar translation values needed by the existing projection seam
- optionally include metadata like `prim_path`, `frame_id`, and `sim_time_sec`

## Stub Path Added In This Round

Stub implementation pieces:

- `IterableIsaacObservationSource`
- `YamlFileIsaacObservationSource`
- `IsaacStubPoseSource`
- `IsaacLiveObservationSource` is not part of the stub path, but it now targets the same contract through an import-safe live skeleton

The first two expose Isaac-oriented observations.
`IsaacStubPoseSource` then adapts those observations into the existing richer payload shape expected by `SimulatorPublisherBridgeRuntime`.

That richer payload shape remains:

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

This keeps the downstream seams unchanged:

- projection
- frame transform
- HTTP posting

## How The Stub Differs From A Future Live Isaac Source

Current stub behavior:

- payloads come from YAML or in-memory iterables
- no Isaac package imports
- no callback lifecycle or live simulator loop
- no reconnect or long-running state handling

Future real Isaac behavior will still need:

- direct reads from live simulator APIs
- ownership of sampling lifecycle
- scene-specific mapping from Isaac world coordinates into the configured tour plane
- stronger timing semantics if simulator replay or streaming cadence matters
- filling in the current live skeleton in `services/sim_publisher_bridge/isaac_live.py`

## Validation Path

This round validated the Isaac-oriented source path by running:

- `scripts/run_isaac_stub_bridge_demo.py`

That path uses:

- `YamlFileIsaacObservationSource`
- `IsaacStubPoseSource`
- existing projection config
- existing frame-transform config
- existing HTTP sim ingress bridge

No changes were required in:

- `core`
- orchestrator
- server-side sim ingress APIs

## Live Skeleton Added Later

The repository now also contains an import-safe live adapter skeleton:

- `services/sim_publisher_bridge/isaac_live.py`

That path:

- targets the same `IsaacObservationSource` contract
- reports dependency availability without importing Isaac during normal repository use
- raises clear runtime errors when Isaac packages are unavailable
- still leaves actual live simulator sampling as future work
