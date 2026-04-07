# Current Round Result

## Round
Round 018 - Audio Lifecycle Session Persistence Baseline

## Summary

- Status: PASSED
- Key audio lifecycle outcomes are now persisted into session logs through a narrow callback seam.
- Historical session summaries no longer depend only on `audio_playback_requested`.
- Stored session inspection now exposes both:
  - a richer `audio_summary`
  - a compact `recent_audio_events` surface
- Raw live `audio_playback_state` remains unchanged for deep runtime inspection.

## What I Changed

- Extended the managed audio layer in:
  - `adapters/mock/audio_output.py`
  so lifecycle events can emit a narrow structured callback payload alongside the existing in-memory runtime state
- Upgraded session persistence and summary logic in:
  - `core/session/logger.py`
  with:
  - recent audio lifecycle tracking
  - stronger historical audio summary derivation
  - a reusable `build_audio_lifecycle_session_persister(...)` helper
- Wired that persistence seam into:
  - `services/api_server/runtime.py`
  - `services/sim_pose_ingress/runtime.py`
- Added focused persistence tests in:
  - `tests/test_audio_session_persistence.py`
- Extended API coverage in:
  - `tests/test_api_server.py`
- Updated docs in:
  - `docs/AUDIO_OUTPUT_CONTRACT.md`
  - `docs/AUDIO_PLAYBACK_POLICY.md`

## Exact Files Changed

- `adapters/mock/audio_output.py`
- `core/session/logger.py`
- `docs/AUDIO_OUTPUT_CONTRACT.md`
- `docs/AUDIO_PLAYBACK_POLICY.md`
- `services/api_server/runtime.py`
- `services/sim_pose_ingress/runtime.py`
- `tests/test_api_server.py`
- `tests/test_audio_session_persistence.py`
- `coordination/latest_result.md`

## Which Audio Lifecycle Events Are Now Persisted

Only these key lifecycle outcomes are persisted into the session log:

- `playback_started`
- `playback_interrupted`
- `playback_completed`
- `playback_failed`

The persisted payload now keeps enough metadata for historical diagnosis of:

- playback id
- playback kind
- output type
- completion source
- failure source
- failure status / message
- degraded continuation policy
- queue advancement when relevant
- latest playback handle status when available

## How Persisted Session Summary Exposure Changed

Stored session summaries now expose more than just the latest playback request.

They now include:

- `audio_summary`
- `recent_audio_events`

`audio_summary` now prefers persisted lifecycle outcomes when available, so a stored session can explain:

- whether the latest meaningful outcome was `started`, `interrupted`, `completed`, or `failed`
- whether completion came from `backend_reported` or fallback
- whether degraded continuation was applied
- the latest failure source and failure status

This means historical summaries are no longer anchored only to the metadata that existed at request time.

## Compact Historical Audio Surface Introduced

New historical surface:

- `recent_audio_events`

It is intentionally compact and currently keeps only the recent persisted lifecycle outcomes, with fields such as:

- `event_type`
- `state`
- `timestamp`
- `spot_id`
- `spot_name`
- `text`
- `extra`

This gives operators a small post-run audio trail without requiring live runtime internals.

## How Raw-State Log Spam Was Avoided

I did not persist:

- `playback_prepared`
- `playback_queued`
- full `audio_playback_state`
- raw queue snapshots on every refresh

Instead, persistence is driven only by the explicit lifecycle callback for the four high-signal events above.

That keeps session logs readable while preserving the most important historical audio outcomes.

## Exact Validation Performed

### Automated

- `python -m unittest tests.test_audio_session_persistence -v`
  - passed
  - `Ran 3 tests ... OK`
- `python -m unittest tests.test_api_server -v`
  - passed
  - `Ran 6 tests ... OK`
- `python -m unittest discover -s tests`
  - passed
  - `Ran 63 tests ... OK`

### Manual

Ran an inline FastAPI/TestClient sample with service-backed mock audio and captured `/session/latest` after narration plus follow-up answer.

Observed:

- `audio_summary.latest_lifecycle_event = "playback_started"`
- `audio_summary.active_playback_kind = "answer"`
- `recent_audio_events` included:
  - `playback_started`
  - `playback_interrupted`
  - `playback_started`

This confirmed:

- persisted interruption data survives into historical session summary output
- persisted audio history is compact but useful
- live API behavior still works with the new persistence seam

## Current Branch

- `main`

## Full Git Status --short --branch

```text
## main...origin/main [ahead 19]
 M docs/DEV_WORKFLOW.md
?? coordination/
```

## Commit Hash

- `0a7544568b677a7d94623c1383ca4c3917358afc`

## Staged / Committed State

- Round 018 code bundle: committed
- `coordination/latest_result.md`: updated locally after commit, not staged
- Unrelated local modification in `docs/DEV_WORKFLOW.md` remains untouched

## Blockers, Risks, Or Remaining Gaps Before Real Engine Or Device-Backed Playback

- Historical summaries are now meaningfully better, but they still intentionally compress detail.
- Full queue internals, live handle transitions, and raw recent event streams still belong to:
  - `audio_playback_state`
- Persisted audio lifecycle events inherit the latest known session pose/state rather than owning an independent playback-state machine snapshot.
- Real engine/device playback will still need:
  - backend-specific completion accuracy
  - backend-specific interruption fidelity
  - stronger failure taxonomy
  - longer-term session replay decisions if product asks for them later
