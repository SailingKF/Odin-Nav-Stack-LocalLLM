# Current Round Prompt

## Round
Round 018 - Audio Lifecycle Session Persistence Baseline

## Goal
Persist key audio playback lifecycle outcomes into session logs and session summaries, so historical sessions retain meaningful audio start / interruption / completion / failure information even after the live runtime is gone.

## Why This Is The Current Priority

Rounds 010 through 017 established:
- an audio output boundary
- a TTS service boundary
- a service-backed mock synthesis path
- queue and interruption semantics
- prepared / start / interrupt lifecycle hooks
- an artifact playback backend seam
- backend-reported completion
- playback failure reporting and degraded continuation
- operator-friendly audio summaries in API and `/debug`

The next unresolved product and architecture risk is persistence parity.

Right now:
- live runtime state has the richest audio lifecycle visibility
- persisted session summaries are better than before, but still thinner than live runtime

That means operators can understand audio behavior during a live run, but historical session inspection still loses too much of the playback lifecycle story.

Before real engine or device-backed playback, we should make sure:
- key audio lifecycle outcomes are actually persisted into session logs
- historical session summaries can report more than just the last playback request
- we do this without turning session logs into a dump of raw internal state on every refresh

## In Scope

- persist key audio lifecycle events into session logs
- keep this persistence focused and low-noise; do not dump the full raw playback state on every poll
- define a minimal set of audio lifecycle events worth persisting, such as:
  - playback started
  - playback interrupted
  - playback completed
  - playback failed
- ensure persisted events carry enough metadata to support historical diagnosis of:
  - completion source
  - failure source / status
  - degraded continuation application
  - queue advancement when relevant
- improve session summary surfaces so stored historical sessions can expose:
  - a concise latest audio outcome summary
  - a small recent-audio-events view or equivalent compact historical surface
- preserve the existing raw live `audio_playback_state` behavior
- add tests covering:
  - persisted session logs now include key audio lifecycle events
  - stored `read_latest_session_summary(...)` exposes meaningful historical audio outcome information
  - no regression to existing API/session/audio behavior

## Out Of Scope

- selecting or installing a real TTS engine
- real OS or device audio playback
- ASR
- Android native app work
- websocket/live push transport
- full session replay UI
- major frontend redesign
- async worker/process orchestration

## Architecture Constraints

- keep `core` platform-agnostic
- keep playback ownership unchanged
- do not move playback backend logic into session store
- avoid heavy polling-side duplication or log spam
- prefer a narrow, explicit sync/persistence seam for audio lifecycle events
- preserve current narrator, gateway, sim-path, and API behavior
- keep this as one coherent bundle only

## Acceptance Criteria

- repository persists key audio lifecycle events into session logs
- historical latest-session summaries expose more meaningful audio lifecycle outcome data than before
- stored session summaries no longer depend solely on the latest playback request to explain recent audio behavior
- existing tests still pass
- focused persistence tests pass
- docs clearly explain which audio lifecycle events are persisted and which details still require live runtime inspection

## Result Requirements

When done, update `coordination/latest_result.md` with:
- what you changed
- exact files changed
- exact validation performed
- which audio lifecycle events are now persisted
- how persisted session summary exposure changed
- what compact historical audio surface you introduced
- how you avoided raw-state log spam
- branch name
- full `git status --short --branch`
- commit hash
- whether files are staged and/or committed
- blockers, risks, or remaining gaps before real engine or device-backed playback

If you hit a blocker, do not expand scope into replay tooling or real playback engine integration.
Stop at the narrowest real blocker and describe it clearly.
