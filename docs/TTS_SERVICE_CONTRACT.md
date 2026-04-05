# TTS Service Contract

## Purpose

This document defines the service-layer TTS contract introduced before selecting a real synthesis engine.

The goal is to let the project move from direct mock playback toward a realistic synthesis architecture while keeping engine choice deferred.

## Service Layer

Service module:

- `services/tts_service/service.py`

Key types:

- `TTSRequest`
- `TTSResponse`
- `TTSArtifact`
- `TTSBackend`
- `TTSService`

## Request / Response Shape

Minimal request fields:

- `text`
- `playback_kind`
- `session_id`
- `spot_id`
- `spot_name`
- `metadata`

Minimal response fields:

- `backend_type`
- `status`
- `text`
- `playback_kind`
- `estimated_duration_ms`
- `artifact`
- `metadata`

Artifact contract:

- `artifact_uri`
- `artifact_kind`
- `mime_type`
- `content_hash`

## Mock Synthesis Behavior

Current development backend:

- `MockTTSBackend`

Behavior:

- deterministic content hash based on session, playback kind, spot, and text
- writes a lightweight JSON artifact instead of generating audio
- returns:
  - `backend_type: "mock"`
  - `status: "synthesized"`
  - deterministic `estimated_duration_ms`
  - artifact metadata pointing to the generated JSON file

This lets downstream audio output verify:

- synthesis was requested
- which backend handled it
- what artifact metadata came back

Current synthesis metadata now also exposes:

- `tts_backend_type`
- `tts_status`

The legacy keys:

- `backend_type`
- `status`

remain present for compatibility with earlier development rounds.

## Service-Backed Audio Path

Service-backed audio output lives in:

- `adapters/mock/audio_output.py`
- `ServiceBackedTTSAudioOutput`

That path:

- accepts a normal `AudioPlaybackRequest`
- calls `TTSService.synthesize(...)`
- hands the synthesized artifact to an explicit artifact playback backend
- preserves orchestrator independence from concrete TTS and playback details

Playback backend details are defined in:

- `docs/ARTIFACT_PLAYER_BACKEND.md`

Completion ownership also remains outside the TTS service:

- the TTS service does not report playback completion
- the playback backend reports handle state
- the audio-output lifecycle manager consumes that state and falls back to estimated completion only when no backend-side completion reporting exists

## Current Config Knobs

Current config fields:

```yaml
audio_output_type: tts_service
tts_backend_type: mock
artifact_player_backend_type: mock
tts_artifact_dir: session_logs/dev_tts_artifacts
```

Supported audio output modes remain:

- `mock`
- `silent`
- `tts_service`

Current TTS backend modes:

- `mock`

## What Still Remains Before Real TTS Integration

- selecting a real engine
- filling in a real backend implementation
- filling in a real playback backend implementation
- deciding file vs stream transport
- choosing device/output routing behavior
