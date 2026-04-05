# Simulator Publisher Bridge Runtime

## Purpose

This document defines the reusable simulator-side publisher bridge runtime introduced after the projection and transform seams were established.

The goal is to keep future Isaac-specific work isolated to the simulator side without changing:
- `core`
- the sim-ingress server runtime
- the HTTP bridge contract

## Runtime Shape

Runtime:
- `services/sim_publisher_bridge/runtime.py`

Key responsibilities:
1. read richer simulator payloads from a source
2. project them into planar raw coordinates
3. frame-transform them into normalized map-frame `x` and `y`
4. post them to the existing HTTP sim-ingress bridge
5. wait for the downstream tour run to settle

## Pose-Source Abstraction

Source interface:
- `services/sim_publisher_bridge/source.py`
- `SimulatorPoseSource`

Baseline source implementations:
- `IterableSimulatorPoseSource`
- `YamlFileRicherPoseSource`

This is the plug-in point for a future Isaac implementation.
An Isaac source should only need to implement `iter_payloads()` and emit richer simulator-side pose payloads.

Isaac-oriented stub contract introduced later:
- `services/sim_publisher_bridge/isaac_source.py`
- `IsaacObservationSource`
- `IsaacStubPoseSource`

That Isaac-oriented layer is the named adapter boundary for future direct Isaac work.
It keeps Isaac-specific source semantics outside the generic publisher runtime while still adapting into the same richer payload contract.

## Existing Publisher-Side Seams It Composes

Projection:
- `adapters/sim/projection.py`

Frame transform:
- `adapters/sim/frame_transform.py`

HTTP posting:
- `services/sim_publisher_bridge/http_client.py`

## Baseline Demo Entry Point

Demo runner:
- `scripts/run_sim_publisher_bridge_demo.py`

This demo uses:
- `YamlFileRicherPoseSource`
- existing projection config from `configs/sim.yaml`
- existing frame-transform config from `configs/sim.yaml`
- existing HTTP sim-ingress bridge

## Where A Future Isaac Source Plugs In

Future Isaac-side work should add a new source implementation under the same publisher-side layer, for example:
- `IsaacSimulatorPoseSource`

That source should:
- read richer simulator payloads from Isaac
- emit them through `iter_payloads()`

With the explicit Isaac-oriented contract now present, a real implementation can also be shaped as:
- an `IsaacObservationSource` implementation that reads live Isaac observations
- wrapped by `IsaacStubPoseSource`-style adaptation into richer publisher payloads

Everything downstream can stay the same:
- projection
- frame transform
- HTTP posting

## What Still Remains Before Direct Isaac SDK Integration

- the actual Isaac-side source implementation
- final decisions on scene/frame mapping
- any richer orientation or timing semantics beyond this baseline
