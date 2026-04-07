# Current Round Prompt

## Round
Round 005 - Simulation Frame Transform And Publisher Baseline

## Goal
Add a minimal publisher-side transform layer that converts simulator-frame pose data into the existing map-frame HTTP pose-ingress contract, so the next Isaac bridge step has a clean place to live.

## Why This Is The Current Priority

Round 004 closed the transport gap:
- the sim-ingress runtime is reachable over HTTP
- an external process can already push poses across a process boundary

The next remaining integration risk is frame alignment.
Right now the HTTP bridge expects already-normalized map-frame `x` and `y`.
Before we touch Isaac SDK specifics, we should create a small, testable publisher-side transform seam for converting raw simulator coordinates into that contract.

## In Scope

- add a minimal simulation-frame to map-frame transform module under `adapters/sim/` or another clearly appropriate non-core location
- keep the HTTP bridge contract stable: the server should still receive normalized map-frame `x`, `y`, and optional `label`
- support a small, explicit transform configuration suitable for early sim work, such as:
  - axis flip and/or axis swap
  - scale
  - x/y offset
- add a publisher-side client utility that can:
  - load raw simulator-style pose payloads
  - apply the configured transform
  - post normalized poses to the existing HTTP bridge
- add a demo raw-pose payload file distinct from the already-normalized demo stream
- document the transform contract and where Isaac-specific logic should eventually live
- add automated tests for transform behavior and publisher-side normalization
- manually validate that transformed raw simulator-style poses can still trigger at least one narration through the existing HTTP bridge

## Out Of Scope

- direct Isaac Sim SDK integration
- ROS transport
- 3D pose handling beyond the minimal 2D projection needed for this project baseline
- timestamp replay logic
- websockets or streaming protocol changes
- TTS or ASR
- Orin NX deployment work
- frontend changes
- broad refactors of the sim-ingress HTTP service

## Architecture Constraints

- keep `core` platform-agnostic
- keep frame-conversion logic outside `core`
- keep the HTTP bridge contract stable and simple
- publisher-side normalization should be the place where future Isaac specifics plug in
- do not move transform concerns into the orchestrator
- keep this as one coherent bundle only

## Acceptance Criteria

- repository contains a clear publisher-side transform layer for raw simulator coordinates
- the existing sim-ingress HTTP contract remains unchanged
- a raw simulator-style pose sequence can be transformed and posted to the HTTP bridge
- at least one POI trigger and narration occur after transformation through the existing HTTP sim path
- automated tests cover transform behavior
- existing tests still pass
- docs clearly state:
  - raw simulator payload shape used in this round
  - transform configuration semantics
  - normalized payload shape sent to the HTTP bridge
  - what still remains before a real Isaac Sim bridge

## Result Requirements

When done, update `coordination/latest_result.md` with:
- what you changed
- exact files changed
- exact validation performed
- the raw payload shape used
- the transform configuration used
- the normalized payload shape sent to the HTTP bridge
- branch name
- full `git status --short --branch`
- commit hash
- whether files are staged and/or committed
- blockers, risks, or remaining gaps to real Isaac Sim integration

If you hit a blocker, do not expand scope into direct Isaac SDK work.
Stop at the narrowest real blocker and describe it clearly.
