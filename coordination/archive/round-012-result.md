# Current Round Result

## Round
Round 012 - Audio Queue And Interruption Semantics Baseline

## Summary

- Status: PASSED
- The repository now contains an explicit audio queue and interruption policy on the audio-output side.
- Development-safe playback lifecycle semantics now model:
  - active playback
  - queued narration
  - interruption / replacement by higher-priority answers
- Playback lifecycle state is now observable in runtime state through `audio_playback_state`.

## What I Changed

- Extended the core audio output boundary with observable playback state:
  - `core/interfaces/audio_output.py`
- Reworked the development audio-output implementation to add lifecycle management:
  - `adapters/mock/audio_output.py`
- Added a queue / interruption manager:
  - `ManagedAudioOutput`
- Kept existing delegate paths available underneath that manager:
  - `MockAudioOutput`
  - `ServiceBackedTTSAudioOutput`
  - `SilentAudioOutput`
- Added explicit queue / interruption semantics:
  - narration requests queue in FIFO order if playback is already active
  - answer requests interrupt and replace the active playback
- Exposed current playback lifecycle state through orchestrator state:
  - `core/tour_orchestrator/orchestrator.py`
- Updated runtime default state payloads so `audio_playback_state` is always present or explicitly `None`:
  - `services/api_server/runtime.py`
  - `services/sim_pose_ingress/runtime.py`
- Added a focused policy doc:
  - `docs/AUDIO_PLAYBACK_POLICY.md`
- Updated related docs:
  - `docs/AUDIO_OUTPUT_CONTRACT.md`
  - `README.md`
- Added a runnable overlap demo:
  - `scripts/run_audio_overlap_demo.py`
- Added automated tests covering:
  - narration queueing
  - answer interruption
  - service-backed playback state exposure
  - API visibility of playback lifecycle state
  in:
  - `tests/test_audio_output.py`
  - `tests/test_api_server.py`

## Exact Files Changed

- `core/interfaces/audio_output.py`
- `adapters/mock/audio_output.py`
- `core/tour_orchestrator/orchestrator.py`
- `services/api_server/runtime.py`
- `services/sim_pose_ingress/runtime.py`
- `docs/AUDIO_OUTPUT_CONTRACT.md`
- `docs/AUDIO_PLAYBACK_POLICY.md`
- `README.md`
- `scripts/run_audio_overlap_demo.py`
- `tests/test_audio_output.py`
- `tests/test_api_server.py`
- `coordination/latest_result.md`

## Queue / Interruption Policy Introduced

Chosen policy name:

- `answers_interrupt_active_playback__narration_queues_fifo`

Current semantics:

- if nothing is active:
  - the incoming playback starts immediately
- if narration arrives while another playback item is active:
  - the narration request is queued in FIFO order
- if an answer arrives while another playback item is active:
  - the active playback is interrupted
  - the answer starts immediately

Why this policy was chosen:

- answers usually carry higher urgency than finishing a long guide segment
- narration is safe to delay in order
- the policy is simple enough to model without real device control

## How Overlapping Playback Was Handled In Validation

### Automated overlap validation

Tested in:

- `tests/test_audio_output.py`

Covered scenarios:

- second narration request queues behind an active narration
- answer request interrupts and replaces an active narration
- queued playback becomes active after the previous playback duration expires

### Manual overlap validation

Ran:

```shell
python scripts/run_audio_overlap_demo.py
```

Observed first request:

- first narration started immediately
- `lifecycle_action: "started"`
- active playback became `audio-1`

Observed second request:

- second narration was queued
- `lifecycle_action: "queued"`
- `queued_playbacks` contained the plaza narration

Observed third request:

- answer replaced the active narration
- `lifecycle_action: "replaced_active"`
- `replaced_playback_id: "audio-1"`
- active playback became the answer item
- the queued plaza narration remained in `queued_playbacks`

Observed recent lifecycle events included:

- `playback_started`
- `playback_queued`
- `playback_interrupted`
- `playback_started` for the answer replacement

## How Playback Lifecycle State Is Exposed In State Or Session Output

Runtime state now exposes:

- `audio_output_type`
- `audio_playback_state`
- `last_audio_playback`

`audio_playback_state` currently includes:

- `policy_name`
- `delegate_output_type`
- `active_playback`
- `queued_playbacks`
- `recent_events`

Each playback item currently includes:

- `playback_id`
- `output_type`
- `playback_kind`
- `status`
- `text`
- `spot_id`
- `spot_name`
- `session_id`
- `duration_ms`
- `remaining_ms`
- `metadata`

Session output still preserves:

- `latest_audio_playback`

That means callers can confirm:

- whether a request was queued
- whether a request replaced a previous one
- which playback item is currently active
- what the recent lifecycle transitions were

## Exact Validation Performed

### Automated

- `python -m unittest tests.test_audio_output -v`
  - passed
  - `Ran 7 tests ... OK`
- `python -m unittest tests.test_api_server -v`
  - passed
  - `Ran 6 tests ... OK`
- `python -m unittest tests.test_tts_service -v`
  - passed
  - `Ran 2 tests ... OK`
- `python -m unittest discover -s tests`
  - passed
  - `Ran 52 tests ... OK`

### Manual

Ran overlap demo:

```shell
python scripts/run_audio_overlap_demo.py
```

Observed:

- first narration started immediately
- second narration was queued
- answer interrupted and replaced the active narration
- playback state showed:
  - active answer playback
  - queued plaza narration
  - recent interruption event history

## Current Branch

- `main`

## Full Git Status --short --branch

```text
## main...origin/main [ahead 13]
 M docs/DEV_WORKFLOW.md
?? coordination/
```

## Commit Hash

- `09e061ed6a161ba9fa31a33a79f253a3623a3536`

## Staged / Committed State

- Round 012 code bundle: committed
- `coordination/latest_result.md`: updated locally, not staged
- Unrelated local modification in `docs/DEV_WORKFLOW.md` remains untouched

## Blockers, Risks, Or Remaining Gaps To Real TTS Playback Control

- This round models playback lifecycle semantics but does not control a real playback device.
- Real backend playback control still needs:
  - true start/stop / interrupt hooks at the engine or device layer
  - synchronization between synthesis completion and actual playback completion
  - queue persistence and recovery rules
  - async backend error handling during playback, not just request-time synthesis
