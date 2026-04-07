# Current Round Prompt

## Round
Round 011 - TTS Service Contract And Mock Synthesis Baseline

## Goal
Add a service-layer TTS contract plus a mock synthesis backend and a service-backed audio output path, so the project can move from pure playback requests toward a realistic speech-synthesis architecture without yet choosing a real TTS engine.

## Why This Is The Current Priority

Round 010 established the audio output boundary and proved narration plus answers can flow through an explicit audio path.
The next unresolved risk is service architecture for real speech generation.
Right now audio playback can be requested, but there is still no TTS service boundary, no synthesis contract, and no service-backed path that could later swap in a real engine.

We should solve that now while keeping engine choice deferred.

## In Scope

- add a dedicated `tts_service` layer under `services/`
- define a minimal TTS request/response contract suitable for future real synthesis
- add a mock TTS backend for development and tests
- make the mock TTS backend return deterministic synthesis metadata and a lightweight artifact contract
- add a service-backed audio output implementation that calls the TTS service instead of directly acting as a mock playback sink
- keep the existing mock/silent audio path available for development fallback
- add explicit config for selecting:
  - direct mock audio output
  - silent audio output
  - service-backed TTS audio output
- expose enough state or session information to confirm:
  - synthesis was requested
  - which backend was used
  - what artifact metadata was returned
- add focused docs describing:
  - the TTS service contract
  - the mock synthesis behavior
  - how this differs from real TTS integration
- add automated tests for the TTS service and the service-backed audio path
- manually validate that at least one narration and one follow-up answer can go through the service-backed TTS path

## Out Of Scope

- selecting or installing a real TTS engine
- ASR
- microphone input
- Android native audio output
- advanced streaming audio transport
- waveform quality tuning
- Orin NX tuning
- simulator-side architecture changes unless required for regression safety

## Architecture Constraints

- keep `core` platform-agnostic
- keep concrete TTS backend details out of `core`
- keep orchestrator dependent only on the audio output boundary, not the TTS service directly
- use the service layer for synthesis concerns
- preserve existing narrator, gateway, API, and sim-path behavior
- keep this as one coherent bundle only

## Acceptance Criteria

- repository contains a clear TTS service contract
- repository contains a mock TTS backend
- repository contains a service-backed audio output path
- narration and follow-up answers can traverse the service-backed TTS path
- existing direct mock/silent audio paths still work
- automated tests cover the new TTS service path
- existing tests still pass
- docs clearly state:
  - the TTS service request/response shape
  - the mock synthesis behavior
  - what still remains before real TTS integration

## Result Requirements

When done, update `coordination/latest_result.md` with:
- what you changed
- exact files changed
- exact validation performed
- the TTS service contract introduced
- the mock synthesis behavior used for validation
- how synthesis activity is exposed in state or session output
- branch name
- full `git status --short --branch`
- commit hash
- whether files are staged and/or committed
- blockers, risks, or remaining gaps to real TTS integration

If you hit a blocker, do not expand scope into choosing or installing a real TTS engine.
Stop at the narrowest real blocker and describe it clearly.
