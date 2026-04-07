# Current Round Prompt

## Round
Round 014 - Artifact Player Backend Baseline

## Goal
Introduce a narrow playback-backend seam for the service-backed audio path, so synthesized TTS artifacts are started and interrupted through an explicit player contract instead of being treated as implicitly playable inside the current dev delegate.

## Why This Is The Current Priority

Rounds 010 through 013 established:
- an audio output boundary
- a TTS service boundary
- a service-backed mock synthesis path
- queue and interruption semantics
- a prepared/start/interruption lifecycle

The next unresolved architecture risk is that the service-backed path still has no distinct playback backend boundary after synthesis.

Right now the project can:
- synthesize a mock TTS artifact
- model playback lifecycle

But it still cannot cleanly express:
- which component owns playback of a synthesized artifact
- what start/interrupt hooks exist at the playback-engine side
- how future real device or engine playback will plug in without re-entangling synthesis and playback

## In Scope

- introduce a narrow development-safe playback backend contract for synthesized artifacts
- keep that seam out of `core`
- ensure the service-backed audio path uses this playback backend when a prepared TTS artifact becomes active
- ensure interruption of an active service-backed playback goes through the playback backend hook, not only the delegate shell
- add a mock artifact player backend that:
  - accepts synthesized artifact metadata
  - models playback start
  - models interruption or stop
  - returns observable playback-handle metadata suitable for runtime inspection
- preserve current `mock`, `silent`, and `tts_service` modes
- keep `tts_service` responsible for synthesis only
- expose enough runtime or session state to confirm:
  - which playback backend handled the active item
  - whether a playback handle was created
  - whether interrupt or stop was invoked on that handle
- update focused docs so the current architecture clearly separates:
  - synthesis
  - playback backend ownership
  - audio-output lifecycle management
- add automated tests covering:
  - service-backed playback start through the new backend seam
  - service-backed interruption through the new backend seam
  - continued compatibility of queue semantics

## Out Of Scope

- selecting or installing a real TTS engine
- real OS or device audio playback
- waveform streaming
- ASR
- Android native audio integration
- queue persistence or crash recovery
- process-level worker orchestration unless minimally required for the dev-safe baseline

## Architecture Constraints

- keep `core` platform-agnostic
- do not make orchestrator own playback backend logic
- keep synthesis concerns in `services/tts_service`
- keep playback-engine concerns on the audio-output / adapter side
- do not collapse synthesis and playback back into one step
- preserve current narrator, gateway, API, and sim-path behavior
- keep this as one coherent bundle only

## Acceptance Criteria

- repository contains an explicit playback backend seam for synthesized artifacts
- service-backed mode starts playback through that seam
- service-backed interruption goes through that seam
- runtime or session output exposes enough metadata to identify playback backend activity
- queue/interruption tests still pass
- focused new tests for the service-backed playback backend path pass
- docs clearly state what owns synthesis vs playback in the current architecture

## Result Requirements

When done, update `coordination/latest_result.md` with:
- what you changed
- exact files changed
- exact validation performed
- what playback backend contract you introduced
- how service-backed start is routed through it
- how interruption is routed through it
- how backend/handle state is exposed in runtime or session output
- branch name
- full `git status --short --branch`
- commit hash
- whether files are staged and/or committed
- blockers, risks, or remaining gaps before real engine or device-backed playback

If you hit a blocker, do not expand scope into choosing or installing a real audio engine.
Stop at the narrowest real blocker and describe it clearly.
