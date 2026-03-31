import subprocess
import time

import requests

from .config import BACKEND, OLLAMA_HEALTH_URL


def _ollama_reachable() -> bool:
    try:
        r = requests.get(OLLAMA_HEALTH_URL, timeout=2)
        return r.status_code == 200
    except Exception:
        return False


def _try_start_ollama() -> bool:
    """Start the Ollama daemon and wait up to 10 s for it to become reachable."""
    try:
        subprocess.Popen(
            ["ollama", "serve"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    except FileNotFoundError:
        return False
    for _ in range(10):
        time.sleep(1)
        if _ollama_reachable():
            return True
    return False


def generate(prompt: str) -> str:
    """Generate text using the configured backend.

    backend="auto"   → try Ollama (start if needed), fall back to Claude
    backend="ollama" → use Ollama (start if needed, raise if still unreachable)
    backend="claude" → use Claude API (raise if key missing)
    """
    backend = BACKEND.lower()

    if backend == "ollama":
        if not _ollama_reachable():
            _try_start_ollama()
        from .ollama_backend import generate as ollama_generate

        return ollama_generate(prompt)

    if backend == "claude":
        from .claude_backend import generate as claude_generate

        return claude_generate(prompt)

    if backend == "auto":
        if _ollama_reachable() or _try_start_ollama():
            from .ollama_backend import generate as ollama_generate

            return ollama_generate(prompt)
        from .claude_backend import generate as claude_generate

        return claude_generate(prompt)

    raise RuntimeError(f"Unknown backend '{backend}'. Choose: auto, ollama, claude.")
