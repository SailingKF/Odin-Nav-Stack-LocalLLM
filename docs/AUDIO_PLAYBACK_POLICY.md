# Audio Playback Policy

## Purpose

This document defines the minimal queue and interruption semantics introduced for development-safe spoken guidance.

The goal is to make overlap behavior explicit before a real backend adds its own device-level playback control.

## Chosen Policy

Policy name:

- `answers_interrupt_active_playback__narration_queues_fifo`

Lifecycle model introduced in this round:

- `prepared`
- `started`
- `interrupted`
- `completed`

Behavior:

- if no playback is active:
  - the new request starts immediately
- if narration arrives while another playback item is active:
  - the narration request is queued in FIFO order
- if an answer arrives while another playback item is active:
  - the currently active playback is interrupted
  - the answer starts immediately

Why this policy was chosen:

- follow-up answers are usually higher priority than finishing a long guide segment
- narration is safe to delay and replay in order
- the policy is simple enough to test without real device control

## Development Implementation

Implementation lives in:

- `adapters/mock/audio_output.py`
- `ManagedAudioOutput`

Managed behavior includes:

- explicit preparation before start
- active playback tracking
- queued playback tracking
- interruption events
- automatic completion rollover based on estimated duration

The queue manager wraps:

- `MockAudioOutput`
- `ServiceBackedTTSAudioOutput`

This keeps lifecycle concerns on the audio-output side and keeps synthesis concerns in `services/tts_service/`.

## Where Preparation Ends And Playback Start Begins

Preparation now means:

- the playback request is accepted
- any synthesis or artifact preparation may happen
- a playback item receives:
  - `playback_id`
  - `prepared_at_monotonic`
  - estimated duration and metadata

Preparation does not mean:

- delegate-side start hooks have fired
- development playback traces have been emitted
- the item has become the active playback

Playback start now means:

- the prepared item becomes the active playback item
- the delegate `start_prepared(...)` hook is invoked
- `started_at_monotonic` is populated
- a `playback_started` lifecycle event is recorded

Queued narration therefore stays in `prepared` / `queued` state until activation.

Interruption now means:

- the active playback item is passed through the delegate `interrupt_prepared(...)` hook
- a `playback_interrupted` event is recorded
- a replacement item may then start immediately

## Observable Runtime State

Playback lifecycle state is exposed through:

- `audio_playback_state`

Current state shape includes:

- `policy_name`
- `delegate_output_type`
- `active_playback`
- `queued_playbacks`
- `recent_events`

Each playback item carries:

- `playback_id`
- `playback_kind`
- `output_type`
- `status`
- `spot_id`
- `spot_name`
- `duration_ms`
- `remaining_ms`
- `metadata`

Lifecycle events now include:

- `playback_prepared`
- `playback_started`
- `playback_queued`
- `playback_interrupted`
- `playback_completed`

## What Still Remains Before Real Backend Playback Control

- true device-level start/stop control
- real interruption of an engine that is already emitting audio
- synchronization between synthesis completion and playback completion
- queue persistence and recovery rules
