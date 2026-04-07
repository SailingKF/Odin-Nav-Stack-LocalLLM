# Current Round Prompt

## Round
Round 009 - Isaac Live Adapter Import-Safe Skeleton

## Goal
Add an import-safe live Isaac adapter skeleton that fits the new `IsaacObservationSource` contract, so the repository is ready for real Isaac package hookup without breaking environments where Isaac is not installed.

## Why This Is The Current Priority

Round 008 closed the contract-definition gap:
- an explicit Isaac-oriented source contract now exists
- a stub path validates the end-to-end shape without SDK packages

The next main risk is dependency hygiene.
If we jump straight to real Isaac imports later, we risk breaking normal development environments.
Before live integration, we should create an import-safe adapter skeleton with explicit availability checks, configuration gates, and clear failure semantics.

## In Scope

- add a live Isaac adapter skeleton in the simulator-side publisher layer that targets `IsaacObservationSource`
- keep it import-safe:
  - normal repository use must still work when Isaac packages are absent
  - importing unrelated modules should not fail just because Isaac is unavailable
- add explicit availability / dependency-check helpers for the live Isaac path
- add a config switch or documented configuration convention for selecting:
  - stub Isaac source path
  - future live Isaac source path
- make sure the simulator publisher bridge runtime can be wired to the live-adapter skeleton interface without requiring Isaac to be installed
- add focused docs describing:
  - how the import-safe live adapter skeleton works
  - what happens when Isaac packages are unavailable
  - what a future real implementation still needs to fill in
- add automated tests for:
  - import safety
  - availability reporting
  - config-selection or wiring behavior

## Out Of Scope

- installing Isaac packages
- direct live simulator sampling
- ROS transport
- server-side API changes
- TTS or ASR
- Orin NX deployment work
- changing the HTTP bridge contract
- full long-running lifecycle handling for a live Isaac session

## Architecture Constraints

- keep `core` platform-agnostic
- keep Isaac-specific live-adapter logic in the simulator-side publisher layer only
- do not move Isaac live-adapter concerns into the server runtime or orchestrator
- preserve the current stub path
- preserve the existing publisher bridge runtime, projection seam, frame-transform seam, and HTTP bridge
- keep this as one coherent bundle only

## Acceptance Criteria

- repository contains an import-safe live Isaac adapter skeleton that targets `IsaacObservationSource`
- repository remains usable when Isaac packages are not installed
- repository contains clear availability or dependency-check behavior for the live Isaac path
- stub path still works
- automated tests cover import safety and live-path availability behavior
- existing tests still pass
- docs clearly state:
  - the live Isaac adapter skeleton shape
  - how availability is detected or reported
  - how this differs from the stub path
  - what still remains before direct live Isaac integration

## Result Requirements

When done, update `coordination/latest_result.md` with:
- what you changed
- exact files changed
- exact validation performed
- the live-adapter skeleton introduced
- how availability / missing dependency behavior works
- branch name
- full `git status --short --branch`
- commit hash
- whether files are staged and/or committed
- blockers, risks, or remaining gaps to direct live Isaac integration

If you hit a blocker, do not expand scope into installing or running real Isaac packages.
Stop at the narrowest real blocker and describe it clearly.
