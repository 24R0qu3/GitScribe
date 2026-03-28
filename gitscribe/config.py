import os
import tomllib
from pathlib import Path

from platformdirs import user_config_dir

_CONFIG_DIR = Path(user_config_dir("gitscribe"))
_CONFIG_FILE = _CONFIG_DIR / "config.toml"

_DEFAULTS: dict = {
    "backend": "auto",
    "ollama_url": "http://localhost:11434/api/generate",
    "ollama_health_url": "http://localhost:11434/api/tags",
    "ollama_model": "qwen2.5:3b",
    "ollama_timeout": 60,
    "claude_model": "claude-haiku-4-5-20251001",
    "claude_timeout": 60,
    "diff_max_lines": 500,
}


def _load() -> dict:
    if not _CONFIG_FILE.exists():
        return _DEFAULTS.copy()
    with open(_CONFIG_FILE, "rb") as f:
        user = tomllib.load(f)
    return {**_DEFAULTS, **user}


_cfg = _load()

BACKEND: str = _cfg["backend"]
OLLAMA_URL: str = _cfg["ollama_url"]
OLLAMA_HEALTH_URL: str = _cfg["ollama_health_url"]
OLLAMA_MODEL: str = _cfg["ollama_model"]
OLLAMA_TIMEOUT: int = _cfg["ollama_timeout"]
CLAUDE_MODEL: str = _cfg["claude_model"]
CLAUDE_TIMEOUT: int = _cfg["claude_timeout"]
DIFF_MAX_LINES: int = _cfg["diff_max_lines"]
