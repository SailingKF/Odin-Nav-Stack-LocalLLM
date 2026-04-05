import argparse
from pathlib import Path
import sys

import uvicorn

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from services.sim_pose_ingress.app import create_app


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the sim pose ingress HTTP bridge.")
    parser.add_argument("--config", default=str(REPO_ROOT / "configs" / "sim.yaml"), help="Config file to load.")
    parser.add_argument("--host", default="127.0.0.1", help="Bind host.")
    parser.add_argument("--port", type=int, default=8100, help="Bind port.")
    args = parser.parse_args()

    uvicorn.run(create_app(config_path=Path(args.config)), host=args.host, port=args.port, log_level="info")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
