"""Settings from environment variables or a .env file. No credentials live in this repo."""

import os
from pathlib import Path

from dotenv import load_dotenv

REPO_ROOT = Path(__file__).resolve().parents[2]


def load_env() -> None:
    """WGR_MCP_ENV_FILES (os.pathsep-separated) wins over the repo .env."""
    files = os.environ.get("WGR_MCP_ENV_FILES")
    paths = [Path(f).expanduser() for f in files.split(os.pathsep)] if files else [REPO_ROOT / ".env"]
    for path in paths:
        if path.exists():
            load_dotenv(path, override=False)


def require(name: str) -> str:
    value = os.environ.get(name)
    if not value:
        raise RuntimeError(f"Missing environment variable {name}. See .env.example.")
    return value


def live_configured() -> bool:
    return all(os.environ.get(n) for n in ("WGR_API_URL", "WGR_API_USER", "WGR_API_PASSWORD"))


def writes_allowed() -> bool:
    return os.environ.get("WGR_ALLOW_WRITE") == "1"
