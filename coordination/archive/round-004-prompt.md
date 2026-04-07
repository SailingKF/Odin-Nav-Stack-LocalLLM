# Current Round Prompt

## Round
Round 004 - Simulation Pose Ingress HTTP Bridge

## Goal
Expose the new simulation pose-ingress runtime through a lightweight HTTP service so an external simulator-side publisher can drive the tour stack across a process boundary.

## Why This Is The Current Priority

Round 003 proved that:
- external poses can drive the tour loop
- the new seam lives outside `core`
- `configs/sim.yaml` now points to a meaningful sim baseline

The next remaining gap before practical Isaac Sim hookup is transport.
Right now pose ingestion works only in-process through a Python runtime seam.
Before we touch real Isaac SDK details, we should prove that an external process can push pose payloads over a narrow service boundary.

## In Scope

- add a lightweight FastAPI service for `SimPoseIngressRuntime`
- expose only the minimal endpoints needed for machine-to-machine sim ingestion, such as:
  - health
  - start
  - ingest one pose
  - ingest a batch of poses
  - finish stream
  - state
  - latest session
- keep the request payload aligned with the existing sim pose-ingress contract
- add a runnable script to start the new HTTP service
- add a small demo client or script that posts the existing demo pose stream over HTTP
- document the HTTP contract clearly
- add endpoint-level automated tests
- manually validate that an HTTP-posted pose sequence triggers at least one narration through the sim path

## Out Of Scope

- direct Isaac Sim SDK integration
- ROS transport
- websockets or streaming protocols
- authentication or production hardening
- operator-facing H5 UI changes
- TTS or ASR
- Orin NX deployment work
- frame-conversion logic beyond minimal documentation of the gap
- broad refactors across existing API services

## Architecture Constraints

- keep `core` platform-agnostic
- keep simulator transport logic outside `core`
- do not merge this round into a large unified runtime refactor
- the current mock API path must keep working
- the current in-process sim-ingress runtime should remain usable
- HTTP should be a thin transport layer over the existing sim-ingress runtime, not a second orchestration system
- do one coherent bundle only

## Acceptance Criteria

- an external process can start the sim-ingress runtime and push pose payloads over HTTP
- the HTTP payload format matches the documented sim-ingress contract
- at least one POI trigger and narration occur through the HTTP-driven sim path
- automated tests cover the new endpoints
- existing tests still pass
- docs clearly state:
  - the HTTP endpoints
  - the request payloads
  - how this relates to the existing in-process sim-ingress runtime
  - what still remains before real Isaac Sim integration

## Result Requirements

When done, update `coordination/latest_result.md` with:
- what you changed
- exact files changed
- exact validation performed
- the exact HTTP endpoints and payloads used for validation
- branch name
- full `git status --short --branch`
- commit hash
- whether files are staged and/or committed
- blockers, risks, or remaining gaps to full Isaac Sim integration

If you hit a blocker, do not expand scope into direct Isaac SDK work.
Stop at the narrowest real blocker and describe it clearly.
