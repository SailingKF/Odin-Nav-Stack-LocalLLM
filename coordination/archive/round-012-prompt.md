# Current Round Prompt

## Round
Round 012 - Audio Queue And Interruption Semantics Baseline

## Goal
Add a minimal queue and interruption policy around the existing audio output / TTS path, so spoken narration has a clear lifecycle when new playback requests arrive before previous playback is considered complete.

## Why This Is The Current Priority

Rounds 010 and 011 established:
- an audio output boundary
- a TTS service boundary
- a service-backed mock synthesis path

The next unresolved architecture risk is playback lifecycle semantics.
Before choosing a real TTS engine, we need to decide how the system behaves when narration and answers overlap or arrive in quick succession.
That decision should happen at the architecture level now, not be left implicit inside a future backend.

## In Scope

- define a minimal audio queue / interruption policy for the current project
- extend the audio output boundary only as needed to support that policy
- add a development-safe implementation that can model:
  - queued playback
  - active playback state
  - interruption or replacement behavior
- preserve the existing mock and service-backed development paths while routing them through the new lifecycle semantics where appropriate
- expose enough runtime or session state to confirm:
  - whether playback was queued
  - whether playback started
  - whether playback was interrupted or replaced
  - what the currently active playback item is
- add focused docs describing:
  - the queue / interruption policy chosen in this round
  - why that policy was chosen
  - what remains before real backend playback control
- add automated tests for overlapping playback scenarios
- manually validate at least one overlap-style scenario, such as:
  - narration starts, then a follow-up answer request arrives
  - a second narration request replaces or queues behind the first according to policy

## Out Of Scope

- selecting or installing a real TTS engine
- real device playback control
- waveform streaming
- ASR
- Android native audio integration
- Orin NX tuning
- simulator-side architecture changes unless required for regression safety

## Architecture Constraints

- keep `core` platform-agnostic
- do not bind orchestrator directly to a concrete backend queue implementation
- keep synthesis concerns in `tts_service`
- keep playback lifecycle concerns in the audio-output side of the architecture
- preserve current narrator, gateway, API, and sim-path behavior
- keep this as one coherent bundle only

## Acceptance Criteria

- repository contains an explicit queue / interruption policy for audio playback
- repository contains a development implementation that models that policy
- playback lifecycle state is observable in runtime state or session output
- overlapping playback scenarios are covered by tests
- existing tests still pass
- docs clearly state:
  - the chosen queue / interruption semantics
  - the development behavior
  - what still remains before real backend playback control

## Result Requirements

When done, update `coordination/latest_result.md` with:
- what you changed
- exact files changed
- exact validation performed
- the queue / interruption policy introduced
- how overlapping playback was handled in validation
- how playback lifecycle state is exposed in state or session output
- branch name
- full `git status --short --branch`
- commit hash
- whether files are staged and/or committed
- blockers, risks, or remaining gaps to real TTS playback control

If you hit a blocker, do not expand scope into choosing or installing a real TTS engine.
Stop at the narrowest real blocker and describe it clearly.
