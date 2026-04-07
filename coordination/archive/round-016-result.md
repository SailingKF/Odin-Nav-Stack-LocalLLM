# Current Round Result

## Round
Round 016 - Playback Failure And Degraded Continuation Baseline

## Summary

- Status: PASSED
- The artifact playback backend now has an explicit failure-reporting seam.
- Service-backed audio can now surface:
  - playback start failure
  - active playback failure after start
- The chosen degraded continuation policy is:
  - mark failed item as failed
  - record failure metadata
  - continue the queue instead of stalling the audio path

## What I Changed

- Extended the playback backend contract in:
  - `adapters/mock/artifact_player.py`
- Added:
  - `ArtifactPlaybackStartError`
  - failure observation fields on `ArtifactPlaybackObservation`
- Upgraded `MockArtifactPlayerBackend` so it can simulate:
  - start failure via `simulate_playback_start_failure`
  - active playback failure via `simulate_active_playback_failure_after_ms`
- Updated the service-backed audio delegate in:
  - `adapters/mock/audio_output.py`
- `ServiceBackedTTSAudioOutput` now:
  - forwards failure-simulation metadata to the playback backend in development mode
  - exposes backend-reported active failure state through `get_completion_state(...)`
  - surfaces `playback_failure_source` metadata
- Updated `ManagedAudioOutput` so it now:
  - catches playback start failure for service-backed playback
  - records `playback_failed`
  - marks failed items with degraded continuation metadata
  - continues the queue after failure using one explicit policy
- Added focused failure tests in:
  - `tests/test_playback_failure.py`
- Extended audio regression coverage in:
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
- `tests/test_playback_failure.py`
- `coordination/latest_result.md`

## Playback-Failure Contract Introduced

The playback backend contract now includes two failure-reporting paths:

1. start failure
   - surfaced by `ArtifactPlaybackStartError`
2. active playback failure after start
   - surfaced through `get_handle_state(...)` returning handle status `failed`

The observation metadata now also supports:

- `failed_at_monotonic`
- `failure_status`
- `failure_reason`

This seam remains outside `core/`.

## Degraded-Continuation Policy Chosen

Chosen policy name:

- `mark_failed_and_continue_queue`

Behavior:

- failed playback item is marked `failed`
- a `playback_failed` lifecycle event is recorded
- failure source and status are made visible in runtime metadata
- if a queued item exists, it is allowed to continue immediately
- the audio path does not stall on failure

This applies to:

- playback start failure
- backend-reported active playback failure

## How Start Failure Is Handled

For service-backed playback start failure:

1. `ServiceBackedTTSAudioOutput.start_prepared(...)` attempts backend playback start
2. the playback backend may raise `ArtifactPlaybackStartError`
3. `ManagedAudioOutput._start_item(...)` catches that failure
4. the item is marked failed
5. `playback_failed` is recorded with:
   - `failure_source: "start_failed"`
   - `failure_status`
   - `failure_message`
   - `degraded_continuation_policy`
6. queue continuation is applied if a queued item exists

Immediate caller-visible result:

- `AudioPlaybackResult.status == "failed"`
- `lifecycle_action == "failed_start_continued"`

## How Active Playback Failure Is Handled

For service-backed active playback failure:

1. active playback remains owned by the playback backend
2. `ManagedAudioOutput` polls backend handle state through the service-backed delegate
3. if backend state reports `status == "failed"`:
   - the active item is marked failed
   - `playback_failed` is recorded with:
     - `failure_source: "backend_reported"`
     - `failure_status`
     - `failure_reason`
     - `playback_failure_observation`
4. the queue continues immediately under the same degraded continuation policy

## How Failure Metadata Is Exposed In Runtime Or Session Output

Failure metadata is now exposed primarily through runtime lifecycle state:

- `audio_playback_state.recent_events`
- `audio_playback_state.active_playback.metadata`

Relevant service-backed metadata now includes:

- `playback_failure_source`
- `degraded_continuation_applied`
- `latest_playback_handle_status`
- `playback_failure_observation`

`playback_failed` events now include:

- `failure_source`
- `failure_status`
- `failure_message`
- `failure_reason`
- `queue_advanced`
- `degraded_continuation_policy`
- `player_start_hook_invoked`
- `player_failure_hook_invoked`
- `playback_failure_observation`

This makes both the failure source and queue-continuation outcome observable.

## Exact Validation Performed

### Automated

- `python -m unittest tests.test_playback_failure -v`
  - passed
  - `Ran 2 tests ... OK`
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
  - `Ran 59 tests ... OK`

### Manual

Ran an inline failure demo using:

- `ManagedAudioOutput`
- `ServiceBackedTTSAudioOutput`
- `MockArtifactPlayerBackend`
- a fake monotonic clock

Observed start failure metadata:

```json
{
  "failure_status": "artifact_player_start_failed",
  "playback_failure_source": "start_failed",
  "degraded_continuation_applied": true,
  "lifecycle_action": "failed_start_continued"
}
```

Observed active failure event metadata:

```json
{
  "failure_source": "backend_reported",
  "degraded_continuation_policy": "mark_failed_and_continue_queue",
  "queue_advanced": true,
  "latest_playback_handle_status": "failed",
  "failure_status": "artifact_player_active_failed",
  "failure_reason": "simulated_active_playback_failure"
}
```

This confirmed:

- start failure is surfaced explicitly
- active playback failure is surfaced explicitly
- queue continuation happens under the chosen degraded policy

## Current Branch

- `main`

## Full Git Status --short --branch

```text
## main...origin/main [ahead 17]
 M docs/DEV_WORKFLOW.md
?? coordination/
```

## Commit Hash

- `1bc65095a9c954a2dac101d72d1bb9f1149ea615`

## Staged / Committed State

- Round 016 code bundle: committed
- `coordination/latest_result.md`: updated locally after commit, not staged
- Unrelated local modification in `docs/DEV_WORKFLOW.md` remains untouched

## Blockers, Risks, Or Remaining Gaps Before Real Engine Or Device-Backed Playback

- The failure seam is still mock-backed and development-safe.
- Real engine integration still needs:
  - richer failure classes for device unavailable / decode error / timeout / callback loss
  - retry or suppression policy decisions for repeated failures
  - stronger session-level summary surfaces for failure events if operators need failure history outside runtime state
  - async ownership rules if real playback backends report failure through callbacks instead of polling
