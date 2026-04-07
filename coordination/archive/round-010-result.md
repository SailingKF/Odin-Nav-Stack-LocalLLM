# Current Round Result

## Round
Round 010 - Audio Output Interface And Mock Playback Baseline

## Summary

- Status: PASSED
- The repository now contains a platform-agnostic audio output boundary.
- Narration and follow-up answers now flow through an explicit audio playback path while preserving existing text state and session logs.
- Development and tests use a mock audio implementation, with a silent fallback mode also available for non-audible execution.

## What I Changed

- Added the core audio output contract:
  - `core/interfaces/audio_output.py`
- Added mock development audio adapters:
  - `adapters/mock/audio_output.py`
- Wired the orchestrator to request playback for:
  - narration
  - follow-up answers
  in:
  - `core/tour_orchestrator/orchestrator.py`
- Extended session logging to track audio playback requests and expose the latest playback summary:
  - `core/session/logger.py`
- Wired development runtimes to build and inject audio output adapters:
  - `services/api_server/runtime.py`
  - `services/sim_pose_ingress/runtime.py`
  - `scripts/run_mock_tour.py`
- Added explicit config selection for development, sim, and edge bundles:
  - `configs/dev.yaml`
  - `configs/sim.yaml`
  - `configs/edge.yaml`
- Added focused audio contract docs:
  - `docs/AUDIO_OUTPUT_CONTRACT.md`
- Updated `README.md` with the new audio boundary, mock behavior, and quick validation steps
- Added automated tests for:
  - mock playback behavior
  - silent playback behavior
  - orchestrator audio routing
  - API state/session exposure of playback activity
  in:
  - `tests/test_audio_output.py`
  - `tests/test_api_server.py`

## Exact Files Changed

- `core/interfaces/audio_output.py`
- `adapters/mock/audio_output.py`
- `core/tour_orchestrator/orchestrator.py`
- `core/session/logger.py`
- `services/api_server/runtime.py`
- `services/sim_pose_ingress/runtime.py`
- `scripts/run_mock_tour.py`
- `configs/dev.yaml`
- `configs/sim.yaml`
- `configs/edge.yaml`
- `docs/AUDIO_OUTPUT_CONTRACT.md`
- `README.md`
- `tests/test_audio_output.py`
- `tests/test_api_server.py`
- `coordination/latest_result.md`

## Audio Output Contract Introduced

New core boundary:

- `core/interfaces/audio_output.py`

Key types:

- `AudioPlaybackRequest`
- `AudioPlaybackResult`
- `AudioOutput`

Current contract responsibilities:

- accept text plus a playback kind such as `narration` or `answer`
- carry optional POI identity and session metadata
- return a structured result with:
  - `output_type`
  - `playback_kind`
  - `status`
  - original text
  - optional metadata

This keeps `core` platform-agnostic and prevents the orchestrator from binding directly to a TTS engine.

## Mock Audio Behavior Used For Validation

Development adapter module:

- `adapters/mock/audio_output.py`

Current development modes:

- `MockAudioOutput`
  - `output_type: "mock"`
  - `status: "played"`
  - emits a lightweight `[AUDIO] ...` trace through the shared event callback
  - stores an in-memory history for tests
- `SilentAudioOutput`
  - `output_type: "silent"`
  - `status: "skipped"`
  - preserves the execution path without audible playback

Development config selection now uses:

```yaml
audio_output_type: mock
```

## How Playback Activity Is Exposed In State Or Session Output

Playback activity is now exposed in runtime state through:

- `audio_output_type`
- `last_audio_playback`

Playback activity is now exposed in latest session summaries through:

- `latest_audio_playback`

Playback requests are recorded as:

- `audio_playback_requested` session events

Example latest session audio playback summary from manual validation:

```json
{
  "event_type": "audio_playback_requested",
  "state": "IDLE",
  "pose": {
    "x": 11.4,
    "y": -0.3,
    "label": null
  },
  "spot_id": "gallery",
  "spot_name": "History Gallery",
  "text": "It proves that the route can finish cleanly after several narrations without duplicate triggers.",
  "extra": {
    "output_type": "mock",
    "playback_kind": "answer",
    "status": "played",
    "session_id": "mock_tour_20260405T033744Z",
    "metadata": {
      "question": "Why does the tour start here?"
    }
  }
}
```

## Exact Validation Performed

### Automated

- `python -m unittest tests.test_audio_output -v`
  - passed
  - `Ran 3 tests ... OK`
- `python -m unittest tests.test_api_server -v`
  - passed
  - `Ran 5 tests ... OK`
- `python -m unittest discover -s tests`
  - passed
  - `Ran 45 tests ... OK`

### Manual Validation

Ran:

```shell
python scripts/run_mock_tour.py
```

Observed:

- narration playback requests:
  - `[AUDIO] narration via mock: East Gate`
  - `[AUDIO] narration via mock: Central Plaza`
  - `[AUDIO] narration via mock: History Gallery`
- follow-up answer playback request:
  - `[AUDIO] answer via mock: History Gallery`

Observed narration text still present:

```text
[NARRATION] East Gate: Welcome to the East Gate. This first stop introduces the route and confirms that the guided tour can trigger narration as soon as the robot reaches a POI.
```

Observed answer text still present:

```text
[ANSWER] History Gallery: It proves that the route can finish cleanly after several narrations without duplicate triggers.
```

Read the latest session summary after the run:

```shell
python -c "from core.session.logger import JsonlSessionStore; from pathlib import Path; import json; summary = JsonlSessionStore.read_latest_session_summary(Path('session_logs/dev')); print(json.dumps(summary, ensure_ascii=False, indent=2))"
```

Observed:

- `latest_narration_text` populated
- `latest_answer_text` populated
- `latest_audio_playback.extra.output_type == "mock"`
- `latest_audio_playback.extra.playback_kind == "answer"`

## Current Branch

- `main`

## Full Git Status --short --branch

```text
## main...origin/main [ahead 11]
 M docs/DEV_WORKFLOW.md
?? coordination/
```

## Commit Hash

- `63097883d95dd4e9180b4685f16096a9ea4eceb4`

## Staged / Committed State

- Round 010 code bundle: committed
- `coordination/latest_result.md`: updated locally, not staged
- Unrelated local modification in `docs/DEV_WORKFLOW.md` remains untouched

## Blockers, Risks, Or Remaining Gaps To Real TTS Integration

- This round intentionally does not choose or install a real TTS backend.
- Real spoken playback still needs:
  - a concrete TTS adapter implementation
  - queueing or interrupt behavior for overlapping playback
  - device/output selection
  - decisions about blocking vs asynchronous audio semantics
  - any waveform or stream generation details
