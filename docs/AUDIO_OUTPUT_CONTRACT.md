# Audio Output Contract

## Purpose

This document defines the platform-agnostic audio output boundary for the tour system.

The goal is to let narration and follow-up answers flow through an explicit playback contract before choosing a real TTS backend.

## Contract Shape

Core interface:

- `core/interfaces/audio_output.py`

Key types:

- `AudioPlaybackRequest`
- `AudioPlaybackResult`
- `AudioOutput`

Minimal playback contract:

- input:
  - text
  - playback kind such as `narration` or `answer`
  - optional POI identity
  - optional session metadata
- output:
  - audio output type
  - playback kind
  - status
  - original text
  - optional metadata
- runtime state:
  - `get_playback_state()`

## Development Mock Behavior

Current development implementation:

- `adapters/mock/audio_output.py`
- `MockAudioOutput`
- `SilentAudioOutput`
- `ServiceBackedTTSAudioOutput`

Current behaviors:

- `MockAudioOutput`
  - reports `output_type: mock`
  - returns `status: played`
  - emits a lightweight `[AUDIO] ...` trace through the shared event callback
  - stores a small in-memory history for tests
- `SilentAudioOutput`
  - reports `output_type: silent`
  - returns `status: skipped`
  - keeps the orchestration path intact without audible playback
- `ServiceBackedTTSAudioOutput`
  - reports `output_type: tts_service`
  - routes synthesis through `services/tts_service/`
  - returns artifact-aware metadata from the active TTS backend

## Current Wiring

The orchestrator now requests playback for:

- POI narration
- follow-up question answers

Playback requests are recorded as:

- `audio_playback_requested` session events

Key playback lifecycle outcomes are now also persisted as compact session events:

- `playback_started`
- `playback_interrupted`
- `playback_completed`
- `playback_failed`

Text state is still preserved separately:

- `last_narration_text`
- `last_answer_text`

Playback activity is exposed in runtime state and session summary through:

- `audio_output_type`
- `audio_playback_state`
- `last_audio_playback`
- `latest_audio_playback`
- `audio_summary`
- `recent_audio_events`

Historical persistence is intentionally compact:

- key lifecycle outcomes are written into the session log
- recent historical audio diagnosis is available through `recent_audio_events`
- concise latest-outcome interpretation is available through `audio_summary`

For deep live debugging, operators should still inspect:

- `audio_playback_state`

That raw surface remains the place for queue internals, active playback detail, and full recent lifecycle traces while the runtime is still alive.

## Relation To Future TTS

This boundary is intentionally narrow so a future TTS adapter can plug in without changing:

- POI logic
- narrator selection
- orchestrator state machine
- session schema

A future real TTS adapter still needs to decide:

- which engine/runtime to use
- blocking vs queued playback behavior
- interrupt / stop semantics
- file or stream handling
- device-specific output selection

See also:

- `docs/TTS_SERVICE_CONTRACT.md`
- `docs/AUDIO_PLAYBACK_POLICY.md`
