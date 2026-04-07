# Current Round Result

## Round
Round 014 - Artifact Player Backend Baseline

## Summary

- Status: PASSED
- The service-backed audio path now has an explicit playback backend seam after synthesis.
- `services/tts_service/` remains synthesis-only.
- Service-backed playback start and interruption now route through a mock artifact player backend on the adapter side.

## What I Changed

- Added a narrow playback backend contract for synthesized artifacts in:
  - `adapters/mock/artifact_player.py`
- Introduced:
  - `ArtifactPlaybackRequest`
  - `ArtifactPlaybackHandle`
  - `ArtifactPlayerBackend`
  - `MockArtifactPlayerBackend`
  - `build_artifact_player_backend(...)`
- Updated the service-backed audio delegate in:
  - `adapters/mock/audio_output.py`
- `ServiceBackedTTSAudioOutput` now:
  - synthesizes through `TTSService`
  - starts synthesized artifacts through `artifact_player_backend.start_artifact(...)`
  - interrupts active service-backed playback through `artifact_player_backend.interrupt_handle(...)`
- Kept existing audio modes intact:
  - `mock`
  - `silent`
  - `tts_service`
- Added explicit config for the new seam:
  - `artifact_player_backend_type: mock`
- Extended service metadata in:
  - `services/tts_service/service.py`
  - now exposes both legacy fields and explicit synthesis fields:
    - `backend_type`
    - `status`
    - `tts_backend_type`
    - `tts_status`
- Added focused tests for the new backend seam in:
  - `tests/test_artifact_player_backend.py`
- Updated existing service-backed audio tests in:
  - `tests/test_audio_output.py`
- Updated focused docs:
  - `docs/ARTIFACT_PLAYER_BACKEND.md`
  - `docs/TTS_SERVICE_CONTRACT.md`
  - `docs/AUDIO_PLAYBACK_POLICY.md`
  - `README.md`

## Exact Files Changed

- `README.md`
- `adapters/mock/artifact_player.py`
- `adapters/mock/audio_output.py`
- `configs/dev.yaml`
- `configs/edge.yaml`
- `configs/sim.yaml`
- `docs/ARTIFACT_PLAYER_BACKEND.md`
- `docs/AUDIO_PLAYBACK_POLICY.md`
- `docs/TTS_SERVICE_CONTRACT.md`
- `services/tts_service/service.py`
- `tests/test_artifact_player_backend.py`
- `tests/test_audio_output.py`
- `coordination/latest_result.md`

## Playback Backend Contract Introduced

The explicit playback backend seam now lives in:

- `adapters/mock/artifact_player.py`

Minimal contract:

- `start_artifact(request: ArtifactPlaybackRequest) -> ArtifactPlaybackHandle`
- `interrupt_handle(handle: ArtifactPlaybackHandle) -> Dict[str, Any]`

The seam is intentionally outside `core/`.

Current responsibilities are now separated like this:

- `services/tts_service/`
  - synthesize text into an artifact
  - return artifact metadata and estimated duration
- `adapters/mock/artifact_player.py`
  - start playback for a synthesized artifact
  - create observable playback-handle metadata
  - interrupt an active playback handle
- `adapters/mock/audio_output.py`
  - own queueing, activation, interruption policy, and runtime lifecycle state

## How Service-Backed Start Is Routed Through It

Current start path:

1. `ManagedAudioOutput` prepares the service-backed item.
2. `ServiceBackedTTSAudioOutput.prepare_playback(...)` calls `TTSService.synthesize(...)`.
3. When the prepared item becomes active, `ServiceBackedTTSAudioOutput.start_prepared(...)` now calls:
   - `artifact_player_backend.start_artifact(...)`
4. The returned `ArtifactPlaybackHandle` is merged into playback metadata and stored on the prepared item.

This means the service-backed path no longer treats the synthesized artifact as implicitly playable.

## How Interruption Is Routed Through It

When an answer replaces an active service-backed playback:

1. `ManagedAudioOutput` calls the active delegate's `interrupt_prepared(...)`.
2. `ServiceBackedTTSAudioOutput.interrupt_prepared(...)` reads the stored playback handle metadata.
3. It now calls:
   - `artifact_player_backend.interrupt_handle(...)`
4. The returned interrupt metadata is recorded into the `playback_interrupted` lifecycle event.

## How Backend / Handle State Is Exposed In Runtime Or Session Output

Service-backed playback metadata now exposes both synthesis-side and playback-side ownership.

Synthesis-side fields:

- `backend_type`
- `status`
- `tts_backend_type`
- `tts_status`
- `artifact`

Playback-side fields:

- `playback_backend_type`
- `playback_handle`
- `player_start_hook_invoked`
- `player_status`

Interruption events now include:

- `playback_backend_type`
- `playback_handle_id`
- `player_interrupt_hook_invoked`
- `player_interrupt_status`

These are visible through:

- `audio_playback_state.active_playback.metadata`
- `audio_playback_state.recent_events[*].extra`
- `latest_audio_playback.extra.metadata`

## Exact Validation Performed

### Automated

- `python -m unittest tests.test_artifact_player_backend -v`
  - passed
  - `Ran 2 tests ... OK`
- `python -m unittest tests.test_audio_output -v`
  - passed
  - `Ran 7 tests ... OK`
- `python -m unittest tests.test_api_server -v`
  - passed
  - `Ran 6 tests ... OK`
- `python -m unittest discover -s tests`
  - passed
  - `Ran 54 tests ... OK`

### Manual

Ran:

```shell
python scripts/run_audio_overlap_demo.py
```

Observed:

- first service-backed narration emitted:
  - `[AUDIO] narration via artifact_player/mock: East Gate`
- returned metadata included:
  - `playback_backend_type: "mock_artifact_player"`
  - `playback_handle.handle_id: "artifact-playback-1"`
  - `player_start_hook_invoked: true`
- second narration remained queued and had no player start-side effect while waiting
- answer emitted:
  - `[AUDIO] answer via artifact_player/mock: East Gate`
- interruption event now included:
  - `playback_backend_type: "mock_artifact_player"`
  - `playback_handle_id: "artifact-playback-1"`
  - `player_interrupt_hook_invoked: true`
  - `player_interrupt_status: "artifact_player_interrupted"`

This manually confirmed:

- service-backed start now goes through the new playback backend seam
- service-backed interruption now goes through the new playback backend seam
- existing queue semantics still hold

## Current Branch

- `main`

## Full Git Status --short --branch

```text
## main...origin/main [ahead 15]
 M docs/DEV_WORKFLOW.md
?? coordination/
```

## Commit Hash

- `d308d4451793395bf755fd45bf5a18d2f5883207`

## Staged / Committed State

- Round 014 code bundle: committed
- `coordination/latest_result.md`: updated locally after commit, not staged
- Unrelated local modification in `docs/DEV_WORKFLOW.md` remains untouched

## Blockers, Risks, Or Remaining Gaps Before Real Engine Or Device-Backed Playback

- The new seam is still development-safe and mock-only at the playback backend level.
- Real engine or device-backed playback still needs:
  - a backend that actually drives OS or device audio playback
  - a real stop / interrupt implementation against that backend
  - completion reporting driven by the real player rather than only estimated duration
  - possible async worker ownership if playback and completion reporting become long-running
