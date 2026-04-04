import argparse
from pathlib import Path
import sys

import uvicorn

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from services.api_server.app import create_app


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the mock tour API server.")
    parser.add_argument("--host", default="0.0.0.0", help="Bind host. Use 0.0.0.0 for LAN/Android access.")
    parser.add_argument("--port", type=int, default=8000, help="Bind port.")
    args = parser.parse_args()

    app = create_app(config_path=REPO_ROOT / "configs" / "dev.yaml")
    uvicorn.run(app, host=args.host, port=args.port, log_level="info")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
