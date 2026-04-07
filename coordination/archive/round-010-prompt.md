# Current Round Prompt

## Round
Round 010 - Audio Output Interface And Mock Playback Baseline

## Goal
Start the spoken-guide stage by adding a platform-agnostic audio output boundary plus a mock playback implementation, so narration and follow-up answers can flow through an explicit audio path without yet choosing a real TTS backend.

## Why This Is The Current Priority

The simulation-preparation track has reached a good stopping point for now:
- sim ingress runtime exists
- HTTP transport exists
- publisher-side projection and frame transform exist
- simulator publisher bridge runtime exists
- Isaac-oriented source contract, stub path, and import-safe live skeleton all exist

Without a real Isaac environment, continuing to elaborate simulator adapters further has diminishing returns.
The next major product gap is that the system still only handles narration as text.
We should now establish the audio-output boundary required for future TTS and real spoken guidance.

## In Scope

- add a platform-agnostic audio output interface in `core/interfaces/` or an equally appropriate core boundary location
- define a minimal playback contract for narration and answer text
- add at least one mock or no-op audio implementation under `adapters/` that is suitable for development and tests
- wire the current tour flow so narration and follow-up answers can pass through the audio output boundary while preserving existing text state and logs
- add explicit configuration for selecting the audio output mode in development
- expose enough state or session information to confirm whether audio playback was requested
- add focused docs describing:
  - the new audio output boundary
  - how it relates to future TTS work
  - what remains before real spoken playback
- add automated tests for the new audio path
- manually validate that a mock tour run triggers the audio output path for at least one narration and one follow-up answer

## Out Of Scope

- choosing or installing a real TTS engine
- ASR
- microphone input
- waveform generation or audio file synthesis
- Android native audio integration
- Orin NX tuning
- simulator-side changes unless needed for regression safety
- major UI redesign

## Architecture Constraints

- keep `core` platform-agnostic
- keep backend- or device-specific playback details out of `core`
- do not bind the orchestrator directly to a concrete TTS or audio library
- preserve existing narrator, gateway, and sim-path behavior
- keep this as one coherent bundle only

## Acceptance Criteria

- repository contains a clear audio output interface
- repository contains a mock or no-op audio implementation for development
- narration and follow-up answers can flow through the audio output boundary
- existing text-based state and session behavior still work
- automated tests cover the new audio path
- existing tests still pass
- docs clearly state:
  - the audio output contract
  - the development mock behavior
  - what remains before real TTS integration

## Result Requirements

When done, update `coordination/latest_result.md` with:
- what you changed
- exact files changed
- exact validation performed
- the audio output contract introduced
- the mock audio behavior used for validation
- how playback activity is exposed in state or session output
- branch name
- full `git status --short --branch`
- commit hash
- whether files are staged and/or committed
- blockers, risks, or remaining gaps to real TTS integration

If you hit a blocker, do not expand scope into installing or selecting a real TTS engine.
Stop at the narrowest real blocker and describe it clearly.
