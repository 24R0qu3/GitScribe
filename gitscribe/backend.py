import requests

from .config import BACKEND, OLLAMA_HEALTH_URL


def _ollama_reachable() -> bool:
    try:
        r = requests.get(OLLAMA_HEALTH_URL, timeout=2)
        return r.status_code == 200
    except Exception:
        return False


def generate(prompt: str) -> str:
    """Generate text using the configured backend.

    backend="auto"   → try Ollama first, fall back to Claude
    backend="ollama" → use Ollama (raise if unreachable)
    backend="claude" → use Claude API (raise if key missing)
    """
    backend = BACKEND.lower()

    if backend == "ollama":
        from .ollama_backend import generate as ollama_generate

        return ollama_generate(prompt)

    if backend == "claude":
        from .claude_backend import generate as claude_generate

        return claude_generate(prompt)

    if backend == "auto":
        if _ollama_reachable():
            from .ollama_backend import generate as ollama_generate

            return ollama_generate(prompt)
        from .claude_backend import generate as claude_generate

        return claude_generate(prompt)

    raise RuntimeError(f"Unknown backend '{backend}'. Choose: auto, ollama, claude.")
