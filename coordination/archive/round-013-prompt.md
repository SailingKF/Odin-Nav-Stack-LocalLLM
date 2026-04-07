# Current Round Prompt

## Round
Round 013 - Prepared Playback And Start Stop Hook Baseline

## Goal
Refactor the development audio-output runtime so playback requests can be accepted and prepared without immediately starting delegate-side playback, and so the active playback has an explicit start / interrupt hook path compatible with future real backend or device control.

## Why This Is The Current Priority

Rounds 010 through 012 established:
- an audio output boundary
- a TTS service boundary
- a service-backed mock synthesis path
- a queue and interruption policy

The next unresolved architecture risk is that the current development implementation still collapses:
- request acceptance
- delegate-side synthesis or playback side effects
- playback start

into one step.

That is acceptable for a mock baseline, but it will block a future real spoken-output path because:
- queued playback items should not start real playback while waiting
- interruption needs an explicit stop / interrupt hook for the active playback
- synthesis preparation and playback activation should be separable

## In Scope

- introduce a narrow development-safe two-phase playback lifecycle on the audio-output side, such as:
  - request accepted or prepared
  - playback started
  - playback interrupted or stopped
  - playback completed
- keep this new seam out of `core`; it may be an internal audio-output abstraction or helper contract
- ensure queued narration does not trigger actual delegate playback start side effects until it becomes active
- ensure answer interruption goes through an explicit interrupt or stop hook path for the active playback item
- preserve current `mock`, `silent`, and `tts_service` development modes
- keep `tts_service` responsible for synthesis only; do not move device playback ownership into it
- expose enough runtime or session state to confirm whether a playback item is:
  - accepted or prepared
  - started
  - interrupted
  - completed
- add focused docs describing:
  - the chosen two-phase lifecycle
  - where preparation ends and playback start begins
  - what still remains before real device or engine-backed playback
- add automated tests that specifically prove:
  - queued playback does not trigger start-side effects early
  - interrupting an active playback invokes the interrupt or stop path
  - service-backed mode still works under the new lifecycle

## Out Of Scope

- selecting or installing a real TTS engine
- real OS or device audio playback
- streaming audio transport
- ASR
- Android native audio integration
- queue persistence or recovery
- async worker or process orchestration beyond what is minimally needed for the dev-safe baseline

## Architecture Constraints

- keep `core` platform-agnostic
- do not make orchestrator own playback queueing or device control
- keep synthesis concerns in `services/tts_service`
- keep playback lifecycle and device-control seams on the audio-output side
- preserve current narrator, gateway, API, and sim-path behavior
- keep this as one coherent bundle only
- do not expand into choosing a specific engine or runtime

## Acceptance Criteria

- repository contains an explicit separation between playback preparation or acceptance and playback start
- queued playback items do not trigger start-side effects before activation
- active playback interruption goes through an explicit hook path
- runtime or session state can distinguish prepared vs started vs interrupted or completed items
- overlapping playback tests still pass and new lifecycle tests pass
- existing tests still pass
- docs clearly state what changed in the playback lifecycle model and what still remains before real backend or device integration

## Result Requirements

When done, update `coordination/latest_result.md` with:
- what you changed
- exact files changed
- exact validation performed
- what two-phase lifecycle or hook contract you introduced
- how you ensured queued items do not start playback early
- how interruption or stop is modeled in the dev baseline
- how lifecycle state is exposed in runtime or session output
- branch name
- full `git status --short --branch`
- commit hash
- whether files are staged and/or committed
- blockers, risks, or remaining gaps before real device or audio backend integration

If you hit a blocker, do not expand scope into installing or selecting a real TTS engine.
Stop at the narrowest real blocker and describe it clearly.
