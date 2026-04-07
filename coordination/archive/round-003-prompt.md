# Current Round Prompt

## Round
Round 003 - Isaac-Ready Simulation Pose Ingress Baseline

## Goal
Prepare the project for Isaac Sim integration by creating a minimal, testable simulation pose-ingress boundary that can drive the existing tour loop without changing core business logic.

## Why This Is The Current Priority

Stages 4 and 5 are now closed enough for forward motion:
- the real local-LLM path works on the dev machine
- prompt/content grounding has a usable baseline

The next major risk is simulation migration.
Right now the runnable path still depends on `MockPoseProvider` generating an internal trajectory.
Before touching real Isaac runtime details, we should prove that the app can accept an external pose stream through a stable adapter boundary.

## In Scope

- add a simulation-oriented pose provider under `adapters/` that can consume externally supplied poses instead of generating them internally
- keep the provider interface compatible with existing `core/interfaces/pose_provider.py`
- add the minimal service/runtime wiring needed so a sim-oriented path can feed poses into the orchestrator
- use `configs/sim.yaml` as the target config for this round
- define and document the pose-ingress contract that a future Isaac Sim publisher will use
- add tests for the new provider and runtime wiring
- manually validate that an externally supplied pose sequence can trigger at least one real narration through the existing tour stack

## Out Of Scope

- direct Isaac Sim SDK integration if it requires heavyweight environment setup
- ROS integration
- TTS or ASR
- native Android app work
- Orin NX deployment work
- video recording changes
- new LLM features
- broad API redesign
- frontend redesign
- broad refactors across `core`, `adapters`, and `services`

## Architecture Constraints

- `core` must remain platform-agnostic
- Isaac-specific semantics must not leak into `core`
- adapter code owns external pose ingestion
- service/runtime code may expose a narrow ingestion seam, but the orchestrator should remain unaware of Isaac details
- the existing mock path must keep working
- do one coherent bundle only

## Acceptance Criteria

- the repository contains a clear simulation pose-ingress path suitable for future Isaac Sim connection
- `configs/sim.yaml` is meaningfully wired for this path
- an externally supplied pose sequence can drive the tour logic without relying on `MockPoseProvider.from_route_pois(...)`
- at least one POI trigger and narration occur through the new sim-oriented path
- automated tests cover the new provider or wiring
- existing tests still pass
- the result clearly documents:
  - the pose-ingress contract
  - how this differs from the current mock trajectory generator
  - what remains before full Isaac Sim integration

## Result Requirements

When done, update `coordination/latest_result.md` with:
- what you changed
- exact files changed
- exact validation performed
- the exact pose-ingress interface or payload used for validation
- branch name
- full `git status --short --branch`
- commit hash
- whether files are staged and/or committed
- blockers, risks, or remaining gaps to full Isaac Sim integration

If you hit a blocker, do not expand scope into full Isaac runtime setup.
Stop at the narrowest real blocker and describe it clearly.
