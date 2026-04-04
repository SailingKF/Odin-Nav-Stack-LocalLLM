from pathlib import Path
import sys

import uvicorn

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from services.api_server.app import create_app


def main() -> int:
    app = create_app(config_path=REPO_ROOT / "configs" / "dev.yaml")
    uvicorn.run(app, host="127.0.0.1", port=8000, log_level="info")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
