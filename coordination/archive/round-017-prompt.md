# Current Round Prompt

## Round
Round 017 - Audio Observability Surface Baseline

## Goal
Expose the current audio playback lifecycle, completion, and failure semantics through cleaner session summaries, API-visible summary fields, and the existing `/debug` H5 control surface, so operators can quickly understand what the audio system is doing without reading raw runtime internals.

## Why This Is The Current Priority

Rounds 010 through 016 established:
- an audio output boundary
- a TTS service boundary
- a service-backed mock synthesis path
- queue and interruption semantics
- prepared / start / interrupt lifecycle hooks
- an artifact playback backend seam
- backend-reported completion
- playback failure reporting and degraded continuation

The next unresolved product and architecture risk is observability.

Right now the audio stack has meaningful internal semantics, but operator-facing visibility is still uneven:
- `audio_playback_state` is rich but low-level
- session summaries still center mostly on latest playback request metadata
- the `/debug` page does not clearly surface audio lifecycle, failure, or degraded-continuation state

Before we introduce any real engine or device-backed playback, we should make sure:
- API consumers can read a concise audio summary
- session summaries preserve the most important audio outcomes
- the H5 debug surface shows enough information to debug playback behavior from a phone

## In Scope

- add a concise audio observability summary on top of the existing low-level runtime state
- keep `core` platform-agnostic
- improve session summary surfaces so they expose key audio outcomes, not just the last playback request
- expose a focused API-visible audio summary that highlights:
  - active playback status
  - queued count
  - latest completion source
  - latest failure source / status
  - whether degraded continuation was applied
- update the existing `/debug` H5 page to display a focused audio panel using the current API surface
- keep the existing debug page thin and framework-free
- preserve the raw `audio_playback_state` for deeper inspection; add a cleaner summary layer rather than replacing it
- add tests covering:
  - session summary exposure of key audio lifecycle outcomes
  - API state/session exposure of the new summary fields
  - `/debug` page rendering of the new audio summary labels or sections

## Out Of Scope

- selecting or installing a real TTS engine
- real OS or device audio playback
- ASR
- Android native app work
- websockets or live push transport
- major frontend redesign
- retry policy redesign
- async worker/process orchestration

## Architecture Constraints

- keep `core` platform-agnostic
- do not move presentation logic into `core`
- keep synthesis / playback backend / lifecycle ownership unchanged
- add observability surfaces in session, API, and static debug UI layers only as needed
- preserve current narrator, gateway, sim-path, and API behavior
- keep this as one coherent bundle only

## Acceptance Criteria

- repository exposes a concise audio summary alongside the existing raw playback state
- latest session summary includes meaningful audio lifecycle outcome fields
- `/state` and/or `/session/latest` make audio lifecycle outcome fields easy to consume
- `/debug` page visibly surfaces audio status, queue/failure/completion summary information
- existing tests still pass
- focused new observability tests pass
- docs clearly explain what the new summary surfaces show and what still requires raw state inspection

## Result Requirements

When done, update `coordination/latest_result.md` with:
- what you changed
- exact files changed
- exact validation performed
- what audio summary surfaces you introduced
- how session summary exposure changed
- how API-visible audio observability changed
- how `/debug` exposes the new audio information
- branch name
- full `git status --short --branch`
- commit hash
- whether files are staged and/or committed
- blockers, risks, or remaining observability gaps before real engine or device-backed playback

If you hit a blocker, do not expand scope into real playback engine integration or frontend rewrites.
Stop at the narrowest real blocker and describe it clearly.
