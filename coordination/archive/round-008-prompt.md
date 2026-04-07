# Current Round Prompt

## Round
Round 008 - Isaac Source Contract And Stub Adapter

## Goal
Define the direct Isaac-side source contract and add a non-SDK stub implementation path, so the repository has a concrete adapter shape for future real Isaac integration without yet depending on Isaac packages.

## Why This Is The Current Priority

Rounds 003 through 007 established the downstream simulator path:
- sim ingress runtime exists
- HTTP transport exists
- publisher-side projection exists
- publisher-side frame transform exists
- reusable simulator publisher bridge runtime exists
- pose-source abstraction exists

The next unresolved gap is the actual source adapter boundary for Isaac.
We still do not have a first-class `Isaac`-named source contract or adapter shape.
Before pulling in SDK dependencies, we should define that source boundary explicitly and validate it with a stub path that behaves like a future live source.

## In Scope

- add an explicit Isaac-oriented simulator source contract or adapter module in the simulator-side publisher layer
- define what a future Isaac-backed source is responsible for, without importing Isaac SDK packages
- add a stub or fake Isaac source implementation that:
  - conforms to the new Isaac-oriented contract
  - can emit richer payloads compatible with the existing publisher bridge runtime
  - is suitable for validation without Isaac installed
- wire the simulator publisher bridge runtime so it can run through this Isaac-oriented source path
- add focused docs describing:
  - the Isaac-side source contract
  - what is stubbed now
  - what a real implementation will need to supply
- add automated tests for the stub Isaac source and bridge integration
- manually validate that the bridge runtime can drive at least one narration through the existing HTTP sim path using the Isaac-oriented stub source

## Out Of Scope

- importing or installing Isaac SDK packages
- direct live Isaac runtime integration
- ROS transport
- server-side API changes
- TTS or ASR
- Orin NX deployment work
- changing the existing HTTP bridge contract
- advanced long-running lifecycle or reconnect management beyond basic documentation

## Architecture Constraints

- keep `core` platform-agnostic
- keep Isaac-specific source semantics in the simulator-side publisher layer only
- do not move Isaac source concerns into the server runtime or orchestrator
- reuse the existing publisher bridge runtime, projection seam, frame-transform seam, and HTTP bridge
- keep this as one coherent bundle only

## Acceptance Criteria

- repository contains an explicit Isaac-oriented source contract or adapter shape
- repository contains a non-SDK stub Isaac source implementation
- the existing publisher bridge runtime can run with that stub source
- the HTTP bridge contract remains unchanged
- automated tests cover the Isaac-oriented stub path
- existing tests still pass
- docs clearly state:
  - the Isaac-oriented source contract
  - what a real Isaac implementation would still need
  - how the stub differs from a future live source
  - what still remains before direct Isaac SDK integration

## Result Requirements

When done, update `coordination/latest_result.md` with:
- what you changed
- exact files changed
- exact validation performed
- the Isaac-oriented source contract introduced
- the stub source used for validation
- the normalized payload shape ultimately sent to the existing HTTP bridge
- branch name
- full `git status --short --branch`
- commit hash
- whether files are staged and/or committed
- blockers, risks, or remaining gaps to direct Isaac integration

If you hit a blocker, do not expand scope into real Isaac SDK setup.
Stop at the narrowest real blocker and describe it clearly.
