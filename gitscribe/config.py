import os
import tomllib
from pathlib import Path

from platformdirs import user_config_dir

_CONFIG_DIR = Path(user_config_dir("gitscribe"))
_CONFIG_FILE = _CONFIG_DIR / "config.toml"

_DEFAULTS: dict = {
    "repo_path": os.getcwd(),
    "backend": "auto",
    "ollama_url": "http://localhost:11434/api/chat",
    "ollama_health_url": "http://localhost:11434/api/tags",
    "ollama_model": "qwen3:1.7b",
    "ollama_timeout": 120,
    "claude_model": "claude-haiku-4-5-20251001",
    "claude_timeout": 60,
    "diff_max_lines": 200,
}


def _load() -> dict:
    if not _CONFIG_FILE.exists():
        return _DEFAULTS.copy()
    with open(_CONFIG_FILE, "rb") as f:
        user = tomllib.load(f)
    return {**_DEFAULTS, **user}


_cfg = _load()

REPO_PATH: str = _cfg["repo_path"]
BACKEND: str = _cfg["backend"]
OLLAMA_URL: str = _cfg["ollama_url"]
OLLAMA_HEALTH_URL: str = _cfg["ollama_health_url"]
OLLAMA_MODEL: str = _cfg["ollama_model"]
OLLAMA_TIMEOUT: int = _cfg["ollama_timeout"]
CLAUDE_MODEL: str = _cfg["claude_model"]
CLAUDE_TIMEOUT: int = _cfg["claude_timeout"]
DIFF_MAX_LINES: int = _cfg["diff_max_lines"]
