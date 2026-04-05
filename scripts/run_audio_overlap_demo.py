import json
from pathlib import Path
import sys

import yaml

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from adapters.mock.audio_output import build_audio_output
from core.interfaces.audio_output import AudioPlaybackRequest


def load_config(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as handle:
        return yaml.safe_load(handle) or {}


def main() -> int:
    config = load_config(REPO_ROOT / "configs" / "dev.yaml")
    audio_output = build_audio_output(config, event_callback=print, repo_root=REPO_ROOT)

    requests = [
        AudioPlaybackRequest(
            text="Welcome to the East Gate. This is the first narration request.",
            playback_kind="narration",
            spot_id="gate",
            spot_name="East Gate",
            session_id="audio-overlap-demo",
        ),
        AudioPlaybackRequest(
            text="Central Plaza is ready to be narrated next.",
            playback_kind="narration",
            spot_id="plaza",
            spot_name="Central Plaza",
            session_id="audio-overlap-demo",
        ),
        AudioPlaybackRequest(
            text="Short follow-up answer should interrupt the active narration.",
            playback_kind="answer",
            spot_id="gate",
            spot_name="East Gate",
            session_id="audio-overlap-demo",
        ),
    ]

    for request in requests:
        result = audio_output.play_text(request)
        print(json.dumps({"play_result": result.metadata}, ensure_ascii=False, indent=2))
        print(json.dumps({"playback_state": audio_output.get_playback_state()}, ensure_ascii=False, indent=2))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
