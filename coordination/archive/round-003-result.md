# Current Round Result

## Round
Round 003 - Isaac-Ready Simulation Pose Ingress Baseline

## Summary

- Status: PASSED
- A minimal simulation-oriented pose-ingress boundary now exists outside `core`.
- The tour loop can be driven by externally supplied poses without relying on `MockPoseProvider.from_route_pois(...)`.
- `configs/sim.yaml` is now wired to a real baseline mode: `pose_provider_type: sim_ingress`.

## What I Changed

- Added `ExternalPoseProvider` in `adapters/sim/external_pose_provider.py`.
  - It implements the existing `PoseProvider` interface.
  - It accepts externally pushed `Pose2D` objects or raw payload dicts.
  - It exposes a closeable stream boundary for ending a sim feed cleanly.
- Added `SimPoseIngressRuntime` in `services/sim_pose_ingress/runtime.py`.
  - It loads route and POI content the same way as existing runtimes.
  - It builds the orchestrator with the new external pose provider.
  - It exposes a narrow ingestion seam:
    - `start()`
    - `ingest_pose(...)`
    - `ingest_pose_payload(...)`
    - `ingest_pose_payloads(...)`
    - `finish_stream()`
    - `state()`
    - `latest_session()`
- Added a demo external pose stream in `content/sim/demo_pose_stream.yaml`.
- Added a runnable validation script: `scripts/run_sim_pose_ingress_demo.py`.
- Added a focused contract doc: `docs/SIM_POSE_INGRESS_CONTRACT.md`.
- Updated `configs/sim.yaml` from the old placeholder `isaac_sim` provider type to the new baseline `sim_ingress`.
- Added automated tests for the new provider and sim runtime wiring.

## Exact Files Changed

- `configs/sim.yaml`
- `adapters/sim/__init__.py`
- `adapters/sim/external_pose_provider.py`
- `services/sim_pose_ingress/__init__.py`
- `services/sim_pose_ingress/runtime.py`
- `content/sim/demo_pose_stream.yaml`
- `scripts/run_sim_pose_ingress_demo.py`
- `docs/SIM_POSE_INGRESS_CONTRACT.md`
- `tests/test_sim_pose_ingress.py`
- `coordination/latest_result.md`

## Exact Validation Performed

### Automated

- `python -m unittest discover -s tests`
  - passed
  - `Ran 21 tests ... OK`

### Manual Runtime Validation

- Ran:
  - `python scripts/run_sim_pose_ingress_demo.py`

- Confirmed:
  - runtime starts with `env=sim`
  - pose provider type is `sim_ingress`
  - poses are ingested externally via payloads
  - `East Gate` narration fired from the new sim path
  - `Central Plaza` narration also fired from the same externally supplied stream

### Exact Pose-Ingress Interface Used For Validation

Payload contract:

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

Optional field:
- `label`

Exact payload sequence used in the demo validation:

```yaml
poses:
  - x: -1.8
    y: -0.7
    label: gate_approach
  - x: -0.6
    y: 0.0
    label: gate_trigger_edge
  - x: 0.0
    y: 0.0
    label: gate_inside
  - x: 1.3
    y: 0.1
    label: gate_depart
  - x: 3.9
    y: 0.8
    label: plaza_trigger_edge
  - x: 5.0
    y: 1.0
    label: plaza_inside
```

### Observable Validation Outcome

- `East Gate` narration through sim ingress:

```text
Welcome to the East Gate. This first stop introduces the route and confirms that the guided tour can trigger narration as soon as the robot reaches a POI.
```

- `Central Plaza` narration through sim ingress:

```text
This central plaza is the mid-route checkpoint in the demo tour. It helps us verify that state transitions and narration continue cleanly after the first stop.
```

## How This Differs From The Current Mock Trajectory Generator

Mock path:
- generates poses internally from route POIs
- uses `MockPoseProvider.from_route_pois(...)`

New sim-ingress path:
- does not generate a route-derived trajectory internally
- accepts externally supplied pose payloads
- keeps external pose ownership inside adapter/service code
- leaves orchestrator and `core` POI logic unchanged

## Current Branch

- `main`

## Full Git Status --short --branch

```text
## main...origin/main [ahead 4]
 M docs/DEV_WORKFLOW.md
?? coordination/
```

## Commit Hash

- `bb072282b806c3b144009e4c2ba9de7538bdae42`

## Staged / Committed State

- Work for this round: committed
- `coordination/latest_result.md`: updated locally, not staged
- Unrelated local modification still exists in `docs/DEV_WORKFLOW.md` and was intentionally left untouched

## Blockers, Risks, Or Remaining Gaps To Full Isaac Sim Integration

- There is still no direct Isaac Sim SDK or transport binding in this repository.
- The new boundary proves external pose ingestion, but not Isaac-specific coordinate conversion.
- Timestamp handling is not part of this baseline payload yet.
- Continuous long-running stream lifecycle and reconnection behavior are still future work.
- If Isaac Sim publishes in a different frame or axis convention, a frame-alignment adapter is still needed before production integration.
