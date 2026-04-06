import argparse
import webbrowser
from pathlib import Path
import sys

import uvicorn

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from services.mvsim_validation_harness.app import create_app


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the MVSim guided validation harness.")
    parser.add_argument(
        "--config",
        default=str(REPO_ROOT / "configs" / "sim_harness.yaml"),
        help="Config file to load.",
    )
    parser.add_argument("--host", default="127.0.0.1", help="Bind host.")
    parser.add_argument("--port", type=int, default=8300, help="Bind port.")
    parser.add_argument(
        "--open-browser",
        action="store_true",
        help="Open the local harness page in the default browser after startup.",
    )
    args = parser.parse_args()

    harness_url = f"http://{args.host}:{args.port}"
    if args.open_browser:
        webbrowser.open(f"{harness_url}/harness")

    uvicorn.run(
        create_app(config_path=Path(args.config), harness_url=harness_url),
        host=args.host,
        port=args.port,
        log_level="info",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
