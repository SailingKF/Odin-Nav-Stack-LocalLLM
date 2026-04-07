# Current Round Prompt

## Round
Round 015 - Playback Completion Signal Baseline

## Goal
Introduce a narrow completion-reporting seam for the playback backend, so service-backed playback completion can be observed from backend-side handle state instead of relying only on estimated duration in the lifecycle manager.

## Why This Is The Current Priority

Rounds 010 through 014 established:
- an audio output boundary
- a TTS service boundary
- a service-backed mock synthesis path
- queue and interruption semantics
- a prepared/start/interruption lifecycle
- an explicit artifact playback backend seam

The next unresolved architecture risk is playback completion ownership.

Right now the system can clearly express:
- synthesis ownership
- playback start ownership
- playback interruption ownership

But service-backed completion is still largely modeled by estimated duration inside the lifecycle manager.
That is acceptable for a development baseline, but it is not the right long-term contract for a real player.

Before introducing any real engine or device integration, we should first define:
- how the playback backend reports handle completion state
- how the audio lifecycle manager consumes that signal
- how runtime state distinguishes estimated fallback completion from backend-reported completion

## In Scope

- introduce a narrow playback-completion reporting seam for artifact playback backends
- keep that seam out of `core`
- let the service-backed audio path consult backend-side handle state when deciding whether an active playback has completed
- preserve a development-safe fallback for modes that still only have estimated duration
- add a mock artifact player behavior that can report:
  - active
  - completed
  - interrupted
- expose enough runtime or session metadata to confirm:
  - whether completion came from backend-side reporting or estimated fallback
  - the latest known playback-handle status
  - recent completion-related lifecycle transitions
- update focused docs so ownership is now clearly separated across:
  - synthesis
  - playback start / interrupt
  - playback completion reporting
- add automated tests covering:
  - service-backed playback completion through backend-side reporting
  - queue rollover after backend-reported completion
  - no regression to existing queue/interruption behavior

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
- do not make orchestrator own playback backend state polling
- keep synthesis concerns in `services/tts_service`
- keep playback-backend state and completion concerns on the audio-output / adapter side
- preserve current narrator, gateway, API, and sim-path behavior
- keep this as one coherent bundle only
- do not expand into choosing a specific playback engine

## Acceptance Criteria

- repository contains an explicit playback completion reporting seam for artifact playback backends
- service-backed mode can expose backend-reported handle completion state
- lifecycle manager can advance queue state using backend-side completion reporting for service-backed playback
- runtime or session output makes it clear whether completion was backend-reported or estimated fallback
- existing queue/interruption behavior still passes
- focused completion tests pass
- docs clearly state current ownership of synthesis vs playback start/interrupt vs completion reporting

## Result Requirements

When done, update `coordination/latest_result.md` with:
- what you changed
- exact files changed
- exact validation performed
- what completion-reporting contract you introduced
- how service-backed completion is now determined
- what fallback remains for modes without backend-side completion
- how completion-source metadata is exposed in runtime or session output
- branch name
- full `git status --short --branch`
- commit hash
- whether files are staged and/or committed
- blockers, risks, or remaining gaps before real engine or device-backed playback

If you hit a blocker, do not expand scope into choosing or installing a real audio engine.
Stop at the narrowest real blocker and describe it clearly.
