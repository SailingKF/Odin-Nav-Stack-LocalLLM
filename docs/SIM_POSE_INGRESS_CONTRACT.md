# Simulation Pose Ingress Contract

## Purpose

This document defines the minimal external pose-ingress boundary that a future Isaac Sim publisher can target.

The goal in this round is not to integrate Isaac Sim directly.
The goal is to prove that the tour stack can be driven by an externally supplied pose stream without changing `core`.

## Current Boundary

Adapter:
- `adapters/sim/external_pose_provider.py`

Runtime:
- `services/sim_pose_ingress/runtime.py`

Demo script:
- `scripts/run_sim_pose_ingress_demo.py`

Config:
- `configs/sim.yaml`

## Payload Contract

Each externally supplied pose payload uses this shape:

```json
{
  "x": 4.4,
  "y": 1.0,
  "label": "plaza_trigger_edge"
}
```

Required fields:
- `x`
- `y`

Optional fields:
- `label`

Current semantics:
- positions are 2D map-frame coordinates
- `label` is only for debugging or trace readability
- no Isaac-specific metadata is required at this baseline

## How This Differs From The Mock Trajectory Generator

Current mock path:
- `MockPoseProvider.from_route_pois(...)`
- generates an internal trajectory from the route POIs

Sim ingress baseline:
- receives externally supplied poses
- does not generate a trajectory from route POIs
- lets service/runtime code push poses into the adapter boundary

This keeps the orchestrator unchanged while moving pose ownership outside the mock adapter.

## Runtime Flow

1. Start `SimPoseIngressRuntime`
2. Runtime builds the orchestrator with `ExternalPoseProvider`
3. External code pushes pose payloads into the provider
4. The provider yields them to the orchestrator loop
5. Existing POI trigger logic and narration flow run unchanged

## What A Future Isaac Sim Publisher Needs To Do

A future Isaac Sim bridge only needs to:
- transform sim pose output into this 2D payload shape
- choose the right map-frame alignment
- push poses in temporal order into the runtime seam

At that point, Isaac-specific transport can live in adapter/service code without leaking into `core`.

## Remaining Gaps Before Full Isaac Sim Integration

- map-frame alignment between Isaac Sim coordinates and tour coordinates
- real transport layer for pose publication
- lifecycle handling for continuous sim sessions
- optional timestamp support if replay fidelity becomes important
- eventual API or bridge process for remote sim ingestion if needed
