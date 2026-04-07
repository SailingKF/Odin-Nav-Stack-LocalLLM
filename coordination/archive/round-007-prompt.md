# Current Round Prompt

## Round
Round 007 - Simulator Publisher Bridge Runtime Skeleton

## Goal
Turn the current publisher-side demo scripts into a reusable simulator-side bridge runtime with a clean pose-source abstraction, so a future Isaac implementation has an obvious place to plug in without changing the HTTP bridge or server/runtime core.

## Why This Is The Current Priority

Rounds 003 through 006 established the full downstream path:
- external pose ingress runtime exists
- HTTP transport exists
- publisher-side frame transform exists
- publisher-side richer-payload projection exists

The next remaining architecture gap before direct Isaac SDK work is process shape on the simulator side.
Right now the publisher path is still script-oriented.
Before direct Isaac integration, we should package that logic into a reusable bridge runtime with an explicit pose-source abstraction.

## In Scope

- add a simulator-side publisher bridge runtime in a non-core location
- define a clean pose-source abstraction for simulator-side inputs
- provide at least one concrete baseline source implementation that does not require Isaac SDK, such as:
  - file-backed richer-payload source
  - iterable/demo source
- have the publisher bridge runtime own this end-to-end flow:
  - read richer simulator payloads from a source
  - project them
  - frame-transform them
  - post normalized poses to the existing HTTP bridge
- keep the existing HTTP bridge contract unchanged
- keep existing one-off demo behavior working, either directly or through the new runtime
- add focused docs showing where a future Isaac source implementation would plug in
- add automated tests for the source abstraction and publisher bridge runtime behavior
- manually validate that the new bridge runtime can drive at least one narration through the existing HTTP sim path

## Out Of Scope

- direct Isaac Sim SDK integration
- ROS transport
- new server-side APIs beyond what already exists
- TTS or ASR
- Orin NX deployment work
- orientation-aware runtime behavior
- timestamp replay or advanced scheduler logic
- frontend changes

## Architecture Constraints

- keep `core` platform-agnostic
- keep simulator-source, projection, transform, and posting logic outside `core`
- do not move simulator-specific source semantics into the orchestrator or HTTP bridge server
- the new runtime should compose existing projection/transform/posting pieces rather than duplicating them
- keep this as one coherent bundle only

## Acceptance Criteria

- repository contains a reusable simulator-side publisher bridge runtime
- repository contains a clear pose-source abstraction for future Isaac-side integration
- the HTTP bridge contract remains unchanged
- the new publisher bridge runtime can drive at least one POI trigger and narration through the existing HTTP sim path
- automated tests cover the source abstraction and bridge flow
- existing tests still pass
- docs clearly state:
  - the new simulator-side runtime shape
  - the pose-source abstraction
  - how a future Isaac source implementation would plug in
  - what still remains before direct Isaac SDK integration

## Result Requirements

When done, update `coordination/latest_result.md` with:
- what you changed
- exact files changed
- exact validation performed
- the pose-source abstraction introduced
- the concrete baseline source used for validation
- the normalized payload shape ultimately sent to the existing HTTP bridge
- branch name
- full `git status --short --branch`
- commit hash
- whether files are staged and/or committed
- blockers, risks, or remaining gaps to direct Isaac integration

If you hit a blocker, do not expand scope into direct Isaac SDK work.
Stop at the narrowest real blocker and describe it clearly.
