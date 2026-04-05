# Artifact Player Backend Contract

## Purpose

This document defines the narrow playback backend seam introduced after the TTS service boundary.

The goal is to keep:

- synthesis ownership in `services/tts_service/`
- playback-engine ownership in adapter-side code
- queue and interruption lifecycle ownership in the audio-output runtime

## Module

Current development module:

- `adapters/mock/artifact_player.py`

Key types:

- `ArtifactPlaybackRequest`
- `ArtifactPlaybackHandle`
- `ArtifactPlayerBackend`
- `MockArtifactPlayerBackend`

## Contract

The playback backend receives an already synthesized artifact and is responsible for:

- starting playback for that artifact
- returning observable playback-handle metadata
- interrupting a previously started handle
- reporting latest playback-handle state for completion polling

Minimal start input:

- `artifact_uri`
- `artifact_kind`
- `mime_type`
- `content_hash`
- `text`
- `playback_kind`
- `session_id`
- `spot_id`
- `spot_name`

Minimal handle output:

- `backend_type`
- `handle_id`
- `status`
- `artifact_uri`
- `artifact_kind`
- `mime_type`
- `content_hash`

Interruption returns:

- `playback_backend_type`
- `playback_handle_id`
- `player_interrupt_hook_invoked`
- `player_interrupt_status`

Completion observation returns:

- `backend_type`
- `handle_id`
- `status`
- `completion_supported`
- `observed_at_monotonic`
- `completed_at_monotonic`
- `metadata`

## Current Development Backend

Current backend:

- `MockArtifactPlayerBackend`

Behavior:

- accepts synthesized artifact metadata from the TTS path
- creates a development playback handle
- emits a lightweight `[AUDIO] ...` trace only when playback actually starts
- records explicit interrupt metadata when active playback is replaced
- reports backend-side handle state as:
  - `active`
  - `completed`
  - `interrupted`

## Ownership Split

Current architecture now separates ownership like this:

- `services/tts_service/`
  - owns synthesis
  - decides artifact metadata
- `adapters/mock/artifact_player.py`
  - owns playback of the synthesized artifact
  - models playback start / interrupt hooks
- `adapters/mock/audio_output.py`
  - owns queueing, activation, and interruption policy

This keeps `core/` free of playback-engine details.

## Observable Metadata

Service-backed playback now exposes both synthesis and playback metadata.

Synthesis-side examples:

- `backend_type`
- `status`
- `tts_backend_type`
- `tts_status`
- `artifact`

Playback-side examples:

- `playback_backend_type`
- `playback_handle`
- `player_start_hook_invoked`
- `player_status`
- `playback_completion_supported`
- `playback_completion_source`
- `latest_playback_handle_status`
- `playback_completion_observation`

Interruption events include:

- `playback_backend_type`
- `playback_handle_id`
- `player_interrupt_hook_invoked`
- `player_interrupt_status`

Completion events now include:

- `completion_source`
- `latest_playback_handle_status`
- `player_completion_hook_invoked`
- `playback_completion_observation`

## Current Config Knob

```yaml
artifact_player_backend_type: mock
```

This is intentionally narrow so the next backend can be added without moving playback ownership into `core/` or back into the TTS service.
