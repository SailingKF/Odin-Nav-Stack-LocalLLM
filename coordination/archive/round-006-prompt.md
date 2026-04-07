# Current Round Prompt

## Round
Round 006 - Isaac-Style Pose Projection Contract

## Goal
Add a publisher-side projection seam for richer simulator pose payloads so the project can convert Isaac-style 3D-ish pose data into the existing 2D tour-map HTTP contract without changing the server side.

## Why This Is The Current Priority

Round 005 closed the simple 2D frame-transform gap:
- raw simulator-style 2D payloads can now be normalized publisher-side
- the HTTP bridge contract stayed stable

The next remaining integration risk is payload shape realism.
Real Isaac outputs are unlikely to arrive as only `sim_x` and `sim_y`.
Before direct Isaac SDK work, we should define a small, testable projection contract for richer simulator pose payloads that still ends at the same normalized 2D bridge payload.

## In Scope

- add a publisher-side projection module for richer simulator pose payloads under a non-core location such as `adapters/sim/`
- support a minimal raw payload shape that is closer to real simulator output, for example nested position fields like:
  - `position.x`
  - `position.y`
  - `position.z`
  - optional orientation or yaw fields if useful for future-proofing
- define a configurable projection from that richer payload into planar coordinates before the existing frame transform and HTTP posting steps
- keep the existing HTTP bridge contract unchanged:
  - normalized `x`
  - normalized `y`
  - optional `label`
- add a demo richer raw-pose payload file
- update or add a publisher-side client utility that:
  - loads richer simulator-style payloads
  - projects them into planar coordinates
  - applies the existing frame transform if needed
  - posts normalized poses to the existing HTTP bridge
- document the projection contract and explicitly state what assumptions are still placeholders before real Isaac hookup
- add automated tests for projection behavior and normalized output shape
- manually validate that projected richer simulator-style poses can still trigger at least one narration through the existing HTTP bridge

## Out Of Scope

- direct Isaac Sim SDK integration
- ROS transport
- full orientation semantics in the tour runtime
- timestamp replay logic
- streaming protocol changes
- TTS or ASR
- Orin NX deployment work
- refactoring the existing sim-ingress HTTP service

## Architecture Constraints

- keep `core` platform-agnostic
- keep projection and transform logic publisher-side
- keep the HTTP bridge contract stable and unchanged
- do not move richer simulator payload semantics into the orchestrator or server runtime
- keep this as one coherent bundle only

## Acceptance Criteria

- repository contains a clear publisher-side projection layer for richer simulator pose payloads
- richer payloads can be converted into the same normalized HTTP bridge contract already in use
- at least one POI trigger and narration occur after projection through the existing HTTP sim path
- automated tests cover projection behavior
- existing tests still pass
- docs clearly state:
  - richer raw payload shape used in this round
  - projection configuration semantics
  - relationship between projection and the existing frame-transform seam
  - normalized payload shape finally sent to the HTTP bridge
  - what still remains before direct Isaac SDK hookup

## Result Requirements

When done, update `coordination/latest_result.md` with:
- what you changed
- exact files changed
- exact validation performed
- the richer raw payload shape used
- the projection configuration used
- the normalized payload shape sent to the HTTP bridge
- branch name
- full `git status --short --branch`
- commit hash
- whether files are staged and/or committed
- blockers, risks, or remaining gaps to direct Isaac integration

If you hit a blocker, do not expand scope into direct Isaac SDK work.
Stop at the narrowest real blocker and describe it clearly.
