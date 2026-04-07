# Current Round Prompt

## Round
Round 016 - Playback Failure And Degraded Continuation Baseline

## Goal
Introduce a narrow playback-failure reporting seam for the playback backend and define the minimal degraded-continuation policy the audio lifecycle manager should use when playback start or active playback fails.

## Why This Is The Current Priority

Rounds 010 through 015 established:
- an audio output boundary
- a TTS service boundary
- a service-backed mock synthesis path
- queue and interruption semantics
- a prepared/start/interruption lifecycle
- an explicit artifact playback backend seam
- backend-reported completion for service-backed playback

The next unresolved architecture risk is failure semantics.

Right now the system can express:
- synthesis ownership
- playback start ownership
- playback interruption ownership
- playback completion ownership

But it still lacks a clear architecture answer for:
- what happens if playback start fails
- what happens if an active playback backend later reports failure instead of completion
- whether the audio lifecycle manager should stall, drop, or continue the queue after a playback failure

Before any real engine or device integration, we should make this policy explicit and test it.

## In Scope

- introduce a narrow playback-failure reporting seam for artifact playback backends
- keep that seam out of `core`
- allow the service-backed path to surface backend-reported failed handle state
- define and implement one explicit degraded-continuation policy for this project, such as:
  - failed playback item is marked failed
  - failure is recorded in lifecycle state and session-visible metadata
  - queue is allowed to continue rather than stalling the whole audio path
- preserve development-safe fallback behavior for non-service-backed modes
- add a mock artifact player behavior that can simulate:
  - start failure
  - active playback failure after start
- expose enough runtime or session metadata to confirm:
  - failure source
  - failure status
  - whether the queue advanced under degraded continuation
  - latest handle state or failure observation
- update focused docs so ownership is clearly separated across:
  - synthesis
  - playback start / interrupt / completion
  - playback failure reporting
  - degraded continuation policy
- add automated tests covering:
  - service-backed start failure handling
  - service-backed active playback failure handling
  - queue continuation after failure according to the chosen policy
  - no regression to existing queue/interruption/completion behavior

## Out Of Scope

- selecting or installing a real TTS engine
- real OS or device audio playback
- waveform streaming
- ASR
- Android native audio integration
- queue persistence or crash recovery
- full async worker/process orchestration beyond what is minimally required for a dev-safe baseline

## Architecture Constraints

- keep `core` platform-agnostic
- do not make orchestrator own playback backend error handling
- keep synthesis concerns in `services/tts_service`
- keep playback-backend failure and degraded-continuation concerns on the audio-output / adapter side
- preserve current narrator, gateway, API, and sim-path behavior
- keep this as one coherent bundle only
- do not expand into choosing a specific playback engine

## Acceptance Criteria

- repository contains an explicit playback failure reporting seam for artifact playback backends
- service-backed mode can expose backend-reported playback failure state
- the lifecycle manager applies one explicit degraded-continuation policy after failure
- runtime or session output makes failure source and continuation behavior observable
- existing queue/interruption/completion behavior still passes
- focused failure tests pass
- docs clearly state the chosen failure policy and remaining gaps before real engine or device-backed playback

## Result Requirements

When done, update `coordination/latest_result.md` with:
- what you changed
- exact files changed
- exact validation performed
- what playback-failure contract you introduced
- what degraded-continuation policy you chose
- how start failure is handled
- how active playback failure is handled
- how failure metadata is exposed in runtime or session output
- branch name
- full `git status --short --branch`
- commit hash
- whether files are staged and/or committed
- blockers, risks, or remaining gaps before real engine or device-backed playback

If you hit a blocker, do not expand scope into choosing or installing a real audio engine.
Stop at the narrowest real blocker and describe it clearly.
