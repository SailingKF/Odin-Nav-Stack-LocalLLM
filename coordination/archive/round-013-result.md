# Current Round Result

## Round
Round 013 - Prepared Playback And Start Stop Hook Baseline

## Summary

- Status: PASSED
- The development audio-output runtime now has an explicit two-phase lifecycle:
  - playback request prepared or accepted
  - playback started
- Queued narration no longer triggers delegate start-side effects while waiting.
- Active interruption now goes through an explicit delegate-side interrupt hook path.

## What I Changed

- Refactored the development audio-output runtime in:
  - `adapters/mock/audio_output.py`
- Introduced an internal prepared-playback seam on the audio-output side:
  - `_PreparedPlayback`
  - `_PreparedAudioDelegate`
- Updated delegate implementations so they now separate:
  - `prepare_playback(...)`
  - `start_prepared(...)`
  - `interrupt_prepared(...)`
- Kept existing development modes:
  - `MockAudioOutput`
  - `SilentAudioOutput`
  - `ServiceBackedTTSAudioOutput`
- Updated `ManagedAudioOutput` to operate on the new two-phase lifecycle:
  - records `playback_prepared`
  - starts only the active item
  - queues narration without invoking start-side effects
  - interrupts active playback via explicit delegate hook before replacement
- Updated tests in:
  - `tests/test_audio_output.py`
- Updated focused docs:
  - `docs/AUDIO_PLAYBACK_POLICY.md`
  - `README.md`

## Exact Files Changed

- `adapters/mock/audio_output.py`
- `tests/test_audio_output.py`
- `docs/AUDIO_PLAYBACK_POLICY.md`
- `README.md`
- `coordination/latest_result.md`

## Two-Phase Lifecycle / Hook Contract Introduced

Chosen lifecycle model:

- `prepared`
- `started`
- `interrupted`
- `completed`

Internal development-safe hook contract now separates:

- `prepare_playback(request)`
  - accepts the request
  - performs preparation work such as mock synthesis
  - returns a prepared playback object
- `start_prepared(prepared)`
  - invokes delegate-side playback start effects
  - emits development traces like `[AUDIO] ...`
  - returns the started playback result
- `interrupt_prepared(prepared)`
  - models explicit stop/interruption of the active playback item

This seam stays on the audio-output side and does not move into `core`.

## How Queued Items Do Not Start Playback Early

Queued items are now only:

- accepted
- prepared
- stored in `queued_playbacks`

They do not call delegate `start_prepared(...)` until they become the active playback item.

This was validated by:

- queueing a second narration behind an active narration
- confirming the second item returned:
  - `status: "prepared"`
  - `lifecycle_action: "queued"`
  - `start_hook_invoked: false`
- confirming delegate-side start history did not grow for the queued item until activation

In the manual overlap demo, the second narration produced:

```json
{
  "lifecycle_action": "queued",
  "started_at_monotonic": null,
  "start_hook_invoked": false
}
```

And no second `[AUDIO] narration ...` start trace appeared while it was only queued.

## How Interruption / Stop Is Modeled In The Dev Baseline

When an answer arrives while another playback item is active:

- `ManagedAudioOutput` calls the active delegate's `interrupt_prepared(...)`
- records a `playback_interrupted` lifecycle event
- then starts the answer item through `start_prepared(...)`

Mock interrupt behavior now returns explicit metadata such as:

- `interrupt_hook_invoked`
- `interrupt_status`

Service-backed interrupt behavior also reports:

- `backend_type`
- `interrupt_status`

In manual validation, the interruption event included:

```json
{
  "event_type": "playback_interrupted",
  "extra": {
    "replaced_by_playback_id": "audio-3",
    "interrupt_hook_invoked": true,
    "interrupt_status": "service_tts_interrupted",
    "backend_type": "mock"
  }
}
```

## How Lifecycle State Is Exposed In Runtime / Session Output

Runtime state continues to expose:

- `audio_playback_state`

That structure now cleanly distinguishes prepared vs started items through:

- `active_playback`
- `queued_playbacks`
- `recent_events`

The lifecycle events now include:

- `playback_prepared`
- `playback_started`
- `playback_queued`
- `playback_interrupted`
- `playback_completed`

Each playback item includes:

- `playback_id`
- `requested_at_monotonic`
- `prepared_at_monotonic`
- `started_at_monotonic`
- `status`
- `duration_ms`
- `remaining_ms`
- `metadata`

Session output still preserves:

- `latest_audio_playback`

which now carries start-related metadata such as:

- `start_hook_invoked`
- `lifecycle_action`
- `started_at_monotonic`

## Exact Validation Performed

### Automated

- `python -m unittest tests.test_audio_output -v`
  - passed
  - `Ran 7 tests ... OK`
- `python -m unittest tests.test_api_server -v`
  - passed
  - `Ran 6 tests ... OK`
- `python -m unittest discover -s tests`
  - passed
  - `Ran 52 tests ... OK`

### Manual

Ran:

```shell
python scripts/run_audio_overlap_demo.py
```

Observed overlap scenario:

1. first narration:
   - prepared
   - started immediately
   - emitted `[AUDIO] narration via tts_service/mock: East Gate`
2. second narration:
   - prepared
   - queued
   - `start_hook_invoked: false`
   - no `[AUDIO]` start-side effect while still queued
3. answer:
   - prepared
   - active narration interrupted through explicit hook
   - answer started immediately
   - emitted `[AUDIO] answer via tts_service/mock: East Gate`

This manually confirmed:

- queued playback does not start early
- interruption goes through an explicit hook path
- service-backed mode still works under the new lifecycle

## Current Branch

- `main`

## Full Git Status --short --branch

```text
## main...origin/main [ahead 14]
 M docs/DEV_WORKFLOW.md
?? coordination/
```

## Commit Hash

- `ae34c610dad612bc8534e923bb8e6bbfaa017af9`

## Staged / Committed State

- Round 013 code bundle: committed
- `coordination/latest_result.md`: updated locally, not staged
- Unrelated local modification in `docs/DEV_WORKFLOW.md` remains untouched

## Blockers, Risks, Or Remaining Gaps Before Real Device / Audio Backend Integration

- This round creates explicit prepare/start/interrupt seams, but there is still no real device playback engine.
- Real backend integration still needs:
  - a backend that can start playback independently from synthesis
  - a real interrupt/stop implementation against the audio device or engine
  - synchronization between actual playback completion and the lifecycle manager
  - async worker ownership if preparation and playback become long-running
