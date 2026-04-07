# Current Round Result

## Round
Round 011 - TTS Service Contract And Mock Synthesis Baseline

## Summary

- Status: PASSED
- The repository now contains a dedicated `services/tts_service` layer with a minimal synthesis contract and a deterministic mock backend.
- A new service-backed audio output path can synthesize narration and answers through the TTS service while keeping the orchestrator dependent only on the audio output boundary.
- Existing direct `mock` and `silent` audio output modes still work.

## What I Changed

- Added the TTS service layer:
  - `services/tts_service/__init__.py`
  - `services/tts_service/service.py`
- Defined a minimal synthesis contract with:
  - `TTSRequest`
  - `TTSResponse`
  - `TTSArtifact`
  - `TTSBackend`
  - `TTSService`
- Added a deterministic mock synthesis backend:
  - `MockTTSBackend`
- Extended the audio output adapter layer with a service-backed path:
  - `ServiceBackedTTSAudioOutput`
  in:
  - `adapters/mock/audio_output.py`
- Kept existing direct `MockAudioOutput` and `SilentAudioOutput` modes intact
- Updated audio output config selection to support:
  - `mock`
  - `silent`
  - `tts_service`
- Updated:
  - `scripts/run_mock_tour.py`
  - `services/api_server/runtime.py`
  - `services/sim_pose_ingress/runtime.py`
  so service-backed audio output can be built from config
- Expanded config fields in:
  - `configs/dev.yaml`
  - `configs/sim.yaml`
  - `configs/edge.yaml`
  with:
  - `audio_output_type`
  - `tts_backend_type`
  - `tts_artifact_dir`
- Updated the shared audio output interface metadata type so synthesis details can be carried through the existing audio boundary:
  - `core/interfaces/audio_output.py`
- Added focused TTS service documentation:
  - `docs/TTS_SERVICE_CONTRACT.md`
- Updated:
  - `docs/AUDIO_OUTPUT_CONTRACT.md`
  - `README.md`
- Added automated tests for:
  - the TTS service contract and mock backend
  - service-backed audio output behavior
  - API/session exposure of synthesis metadata
  in:
  - `tests/test_tts_service.py`
  - `tests/test_audio_output.py`
  - `tests/test_api_server.py`

## Exact Files Changed

- `services/tts_service/__init__.py`
- `services/tts_service/service.py`
- `adapters/mock/audio_output.py`
- `core/interfaces/audio_output.py`
- `scripts/run_mock_tour.py`
- `services/api_server/runtime.py`
- `services/sim_pose_ingress/runtime.py`
- `configs/dev.yaml`
- `configs/sim.yaml`
- `configs/edge.yaml`
- `docs/TTS_SERVICE_CONTRACT.md`
- `docs/AUDIO_OUTPUT_CONTRACT.md`
- `README.md`
- `tests/test_tts_service.py`
- `tests/test_audio_output.py`
- `tests/test_api_server.py`
- `coordination/latest_result.md`

## TTS Service Contract Introduced

New service-layer contract:

- `services/tts_service/service.py`

Core types:

- `TTSRequest`
- `TTSResponse`
- `TTSArtifact`
- `TTSBackend`
- `TTSService`

Current request shape includes:

- `text`
- `playback_kind`
- `session_id`
- `spot_id`
- `spot_name`
- `metadata`

Current response shape includes:

- `backend_type`
- `status`
- `text`
- `playback_kind`
- `estimated_duration_ms`
- `artifact`
- `metadata`

Artifact shape includes:

- `artifact_uri`
- `artifact_kind`
- `mime_type`
- `content_hash`

## Mock Synthesis Behavior Used For Validation

Current mock backend:

- `MockTTSBackend`

Behavior:

- computes a deterministic content hash from:
  - `session_id`
  - `playback_kind`
  - `spot_id`
  - `text`
- writes a lightweight JSON artifact instead of generating audio
- returns:
  - `backend_type: "mock"`
  - `status: "synthesized"`
  - deterministic `estimated_duration_ms`
  - artifact metadata with URI, kind, mime type, and content hash

Example artifact metadata observed during manual validation:

```json
{
  "backend_type": "mock",
  "status": "synthesized",
  "estimated_duration_ms": 4320,
  "metadata": {
    "artifact_file_name": "e74822e311404683.mock_tts.json"
  },
  "artifact": {
    "artifact_uri": "C:\\Users\\saili\\Desktop\\odin_nav_stack_local_llm_docs\\session_logs\\dev_tts_artifacts\\e74822e311404683.mock_tts.json",
    "artifact_kind": "mock_json",
    "mime_type": "application/json",
    "content_hash": "e74822e31140468388b03e3f2761eb2be739a7c3"
  }
}
```

## How Synthesis Activity Is Exposed In State Or Session Output

The orchestrator still only depends on the audio output boundary.
Synthesis activity is exposed through the existing playback event shape.

State/session visibility remains under:

- `audio_output_type`
- `last_audio_playback`
- `latest_audio_playback`

For service-backed playback, the following are now visible in:

- `latest_audio_playback.extra.output_type`
- `latest_audio_playback.extra.metadata.backend_type`
- `latest_audio_playback.extra.metadata.status`
- `latest_audio_playback.extra.metadata.estimated_duration_ms`
- `latest_audio_playback.extra.metadata.artifact`

This means callers can confirm:

- synthesis was requested
- which backend handled it
- what artifact metadata was returned

## Exact Validation Performed

### Automated

- `python -m unittest tests.test_tts_service -v`
  - passed
  - `Ran 2 tests ... OK`
- `python -m unittest tests.test_audio_output -v`
  - passed
  - `Ran 5 tests ... OK`
- `python -m unittest tests.test_api_server -v`
  - passed
  - `Ran 6 tests ... OK`
- `python -m unittest discover -s tests`
  - passed
  - `Ran 50 tests ... OK`

### Manual Validation

Used the current dev config, which now selects:

```yaml
audio_output_type: tts_service
tts_backend_type: mock
tts_artifact_dir: session_logs/dev_tts_artifacts
```

Ran:

```shell
python scripts/run_mock_tour.py
```

Observed service-backed playback traces:

```text
[AUDIO] narration via tts_service/mock: East Gate
[AUDIO] narration via tts_service/mock: Central Plaza
[AUDIO] narration via tts_service/mock: History Gallery
[AUDIO] answer via tts_service/mock: History Gallery
```

Observed narration still flowed normally:

```text
[NARRATION] East Gate: Welcome to the East Gate. This first stop introduces the route and confirms that the guided tour can trigger narration as soon as the robot reaches a POI.
```

Observed follow-up answer still flowed normally:

```text
[ANSWER] History Gallery: It proves that the route can finish cleanly after several narrations without duplicate triggers.
```

Read latest session summary:

```shell
python -c "from core.session.logger import JsonlSessionStore; from pathlib import Path; import json; summary = JsonlSessionStore.read_latest_session_summary(Path('session_logs/dev')); print(json.dumps(summary, ensure_ascii=False, indent=2))"
```

Observed:

- `latest_answer_text` populated
- `latest_audio_playback.extra.output_type == "tts_service"`
- `latest_audio_playback.extra.metadata.backend_type == "mock"`
- `latest_audio_playback.extra.metadata.artifact.artifact_uri` points at a generated mock artifact

Confirmed recent artifact files exist under:

- `session_logs/dev_tts_artifacts/`

## Current Branch

- `main`

## Full Git Status --short --branch

```text
## main...origin/main [ahead 12]
 M docs/DEV_WORKFLOW.md
?? coordination/
```

## Commit Hash

- `771aa4b993a9554c5402a5c6a5afaa3a18966e62`

## Staged / Committed State

- Round 011 code bundle: committed
- `coordination/latest_result.md`: updated locally, not staged
- Unrelated local modification in `docs/DEV_WORKFLOW.md` remains untouched

## Blockers, Risks, Or Remaining Gaps To Real TTS Integration

- This round intentionally does not choose or install a real TTS backend.
- A real TTS integration still needs:
  - a non-mock backend implementation
  - decisions on waveform/file/stream transport
  - queueing and interruption semantics
  - device/output routing behavior
  - possible async or long-running synthesis handling
