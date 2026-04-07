# Current Round Prompt

## Round
Round 019 - Edge Capability Profile And Config Validation Baseline

## Goal
Introduce an explicit deployment capability/profile layer for `dev`, `sim`, and `edge` modes, plus focused config validation, so the project can express what each environment is expected to support before we attempt real Orin NX or hardware-backed integration.

## Why This Is The Current Priority

Rounds 010 through 018 established:
- an audio output boundary
- a TTS service boundary
- a service-backed mock synthesis path
- queue / interruption / completion / failure semantics
- audio observability surfaces
- persisted audio lifecycle summaries

That audio track is now mature enough for the current phase.

The next unresolved architecture risk is edge readiness clarity.

Right now the repo has:
- `configs/dev.yaml`
- `configs/sim.yaml`
- `configs/edge.yaml`

But it still does not clearly and centrally express:
- which subsystems are expected or optional in each mode
- which config combinations are valid or obviously invalid
- what “edge-ready enough for the next step” actually means at runtime

Before we touch real Orin NX deployment or real hardware adapters, we should define this explicitly.

## In Scope

- introduce a narrow deployment capability/profile layer for:
  - `dev`
  - `sim`
  - `edge`
- keep this layer out of `core` business logic
- define a concise capability summary for things such as:
  - pose source expectations
  - local LLM expectation
  - audio mode expectation
  - recording expectation
  - whether mock-only components are still active
  - whether the current config should be considered edge-ready, dev-only, or sim-only
- add focused config validation for obvious misconfigurations, for example:
  - incompatible pose provider vs deployment profile
  - unsupported audio/output combos for a target profile
  - mock-only settings in edge profile that should be reported as degraded or placeholder
- expose a compact readiness/capability summary in API-visible state or health surfaces
- update docs to describe:
  - the three deployment profiles
  - what each profile currently supports
  - which current edge settings are still placeholder/mock
- add tests covering:
  - profile derivation
  - config validation behavior
  - API-visible capability/readiness summary

## Out Of Scope

- actual Orin NX deployment
- ROS/Odin hardware integration
- real audio device playback
- real TTS engine selection
- systemd/service packaging
- containerization work
- ASR

## Architecture Constraints

- keep `core` platform-agnostic
- keep deployment/profile logic outside business orchestration
- do not hardcode scattered environment checks across unrelated modules
- prefer one narrow reusable profile/validation seam
- preserve current dev, sim, API, narrator, and audio behavior
- keep this as one coherent bundle only

## Acceptance Criteria

- repository contains an explicit deployment capability/profile layer
- obvious config mismatches are validated or clearly surfaced
- API-visible state or health includes a concise capability/readiness summary
- docs clearly explain what `dev`, `sim`, and `edge` currently mean in this repo
- existing tests still pass
- focused new tests for profile/validation behavior pass

## Result Requirements

When done, update `coordination/latest_result.md` with:
- what you changed
- exact files changed
- exact validation performed
- what capability/profile surface you introduced
- what config validation rules you added
- how API-visible readiness/capability exposure changed
- which current edge settings are still placeholder/mock after this round
- branch name
- full `git status --short --branch`
- commit hash
- whether files are staged and/or committed
- blockers, risks, or remaining gaps before real Orin NX or hardware-backed deployment

If you hit a blocker, do not expand scope into real hardware integration or packaging work.
Stop at the narrowest real blocker and describe it clearly.
