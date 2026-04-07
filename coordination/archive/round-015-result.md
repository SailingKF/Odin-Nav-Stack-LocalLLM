# Current Round Result

## Round
Round 015 - Playback Completion Signal Baseline

## Summary

- Status: PASSED
- Service-backed playback now exposes backend-side handle completion state.
- `ManagedAudioOutput` now uses backend-reported completion for service-backed playback before falling back to estimated-duration completion.
- Runtime state now distinguishes:
  - backend-reported completion
  - estimated fallback completion

## What I Changed

- Extended the artifact playback backend contract in:
  - `adapters/mock/artifact_player.py`
- Added:
  - `ArtifactPlaybackObservation`
  - `ArtifactPlayerBackend.get_handle_state(...)`
- Upgraded `MockArtifactPlayerBackend` so it now tracks per-handle runtime state and reports:
  - `active`
  - `completed`
  - `interrupted`
- Updated the service-backed audio delegate in:
  - `adapters/mock/audio_output.py`
- `ServiceBackedTTSAudioOutput` now:
  - passes estimated duration to the playback backend as preparation metadata
  - polls backend-side handle state through `get_completion_state(...)`
  - exposes backend completion metadata on active playback state
- Updated `ManagedAudioOutput` so active playback completion now works like this:
  - ask delegate for backend completion state
  - if backend reports completion:
    - record `playback_completed` with `completion_source: "backend_reported"`
    - advance the queue immediately
  - otherwise, if no backend-side completion reporting exists and the estimated duration expires:
    - record `playback_completed` with `completion_source: "estimated_fallback"`
    - advance the queue
- Added focused completion tests in:
  - `tests/test_playback_completion.py`
- Extended existing audio tests in:
  - `tests/test_audio_output.py`
- Updated focused docs:
  - `docs/ARTIFACT_PLAYER_BACKEND.md`
  - `docs/AUDIO_PLAYBACK_POLICY.md`
  - `docs/TTS_SERVICE_CONTRACT.md`
  - `README.md`

## Exact Files Changed

- `README.md`
- `adapters/mock/artifact_player.py`
- `adapters/mock/audio_output.py`
- `docs/ARTIFACT_PLAYER_BACKEND.md`
- `docs/AUDIO_PLAYBACK_POLICY.md`
- `docs/TTS_SERVICE_CONTRACT.md`
- `tests/test_audio_output.py`
- `tests/test_playback_completion.py`
- `coordination/latest_result.md`

## Completion-Reporting Contract Introduced

The playback backend contract now includes:

- `get_handle_state(handle: ArtifactPlaybackHandle) -> ArtifactPlaybackObservation`

`ArtifactPlaybackObservation` reports:

- `backend_type`
- `handle_id`
- `status`
- `completion_supported`
- `observed_at_monotonic`
- `completed_at_monotonic`
- `metadata`

This seam remains outside `core/`.

## How Service-Backed Completion Is Now Determined

For service-backed playback:

1. playback starts through the artifact player backend
2. the active playback item stores its playback handle metadata
3. during lifecycle refresh, `ManagedAudioOutput` asks the service-backed delegate for completion state
4. the delegate polls the playback backend with `get_handle_state(...)`
5. if the backend reports `status == "completed"`:
   - the lifecycle manager records a `playback_completed` event
   - `completion_source` is set to `backend_reported`
   - the next queued item starts immediately

This means completion ownership is now represented on the playback backend side for service-backed playback.

## What Fallback Remains For Modes Without Backend-Side Completion

The development-safe fallback remains:

- `MockAudioOutput`
- `SilentAudioOutput`
- any delegate path that does not expose backend-side completion polling

For those modes, `ManagedAudioOutput` still completes active playback by comparing `finish_at` against the current clock.

Those completion events are now explicitly labeled with:

- `completion_source: "estimated_fallback"`

## How Completion-Source Metadata Is Exposed In Runtime Or Session Output

Runtime state now exposes completion ownership more clearly through:

- `audio_playback_state.active_playback.metadata`
- `audio_playback_state.recent_events`

Service-backed active playback metadata can now include:

- `playback_completion_supported`
- `playback_completion_source`
- `latest_playback_handle_status`
- `playback_completion_observation`

Completion lifecycle events now include:

- `completion_source`
- `latest_playback_handle_status`
- `completion_supported`
- `player_completion_hook_invoked`
- `playback_completion_observation`

This makes it possible to tell whether a completed item finished because:

- the backend reported completion
- or the lifecycle manager used estimated fallback timing

## Exact Validation Performed

### Automated

- `python -m unittest tests.test_playback_completion -v`
  - passed
  - `Ran 2 tests ... OK`
- `python -m unittest tests.test_audio_output -v`
  - passed
  - `Ran 8 tests ... OK`
- `python -m unittest tests.test_api_server -v`
  - passed
  - `Ran 6 tests ... OK`
- `python -m unittest discover -s tests`
  - passed
  - `Ran 57 tests ... OK`

### Manual

Ran an inline completion demo using:

- `ManagedAudioOutput`
- `ServiceBackedTTSAudioOutput`
- `MockArtifactPlayerBackend`
- a fake monotonic clock

Observed completion event payload:

```json
{
  "completion_source": "backend_reported",
  "latest_playback_handle_status": "completed",
  "completion_supported": true,
  "player_completion_hook_invoked": true,
  "playback_completion_observation": {
    "backend_type": "mock_artifact_player",
    "handle_id": "artifact-playback-1",
    "status": "completed",
    "completion_supported": true,
    "observed_at_monotonic": 5.0,
    "completed_at_monotonic": 5.0
  }
}
```

This confirmed:

- completion can now be backend-reported for service-backed playback
- queue rollover can happen from backend-side completion state
- completion-source metadata is visible in runtime lifecycle events

## Current Branch

- `main`

## Full Git Status --short --branch

```text
## main...origin/main [ahead 16]
 M docs/DEV_WORKFLOW.md
?? coordination/
```

## Commit Hash

- `6be3d6884e20b4c02eca5bb1a629889e4528c85e`

## Staged / Committed State

- Round 015 code bundle: committed
- `coordination/latest_result.md`: updated locally after commit, not staged
- Unrelated local modification in `docs/DEV_WORKFLOW.md` remains untouched

## Blockers, Risks, Or Remaining Gaps Before Real Engine Or Device-Backed Playback

- The playback completion seam is still mock-backed and development-safe.
- Real engine integration still needs:
  - a playback backend that polls or receives completion from a real device or engine
  - a stronger model for completion when device playback can stall or error
  - clear ownership for asynchronous completion callbacks or worker loops if the real backend becomes process-bound
- Session summaries still center on latest playback request metadata; completion-source visibility is currently strongest in runtime playback state and lifecycle events rather than a dedicated session-level completion summary.
