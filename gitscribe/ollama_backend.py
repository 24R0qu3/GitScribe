import requests

from .config import OLLAMA_MODEL, OLLAMA_TIMEOUT, OLLAMA_URL


def _post(prompt: str) -> str:
    payload = {
        "model": OLLAMA_MODEL,
        "messages": [{"role": "user", "content": prompt}],
        "think": False,
        "stream": False,
    }
    try:
        response = requests.post(OLLAMA_URL, json=payload, timeout=OLLAMA_TIMEOUT)
        response.raise_for_status()
    except requests.exceptions.Timeout:
        raise RuntimeError(f"Ollama timed out after {OLLAMA_TIMEOUT}s.")
    except requests.exceptions.ConnectionError as e:
        raise RuntimeError(f"Could not connect to Ollama: {e}")
    except requests.exceptions.HTTPError as e:
        raise RuntimeError(f"Ollama HTTP error: {e}")
    data = response.json()
    content = data.get("message", {}).get("content", "").strip()
    if not content and data.get("done_reason") == "load":
        raise _ModelLoading()
    return content


class _ModelLoading(Exception):
    """Raised when Ollama returns done_reason=load with no content."""


def generate(prompt: str) -> str:
    """Call Ollama, retrying once if the model was still loading on the first call."""
    try:
        return _post(prompt)
    except _ModelLoading:
        pass
    # Second attempt after the model has finished loading
    try:
        return _post(prompt)
    except _ModelLoading:
        raise RuntimeError(
            f"Ollama model '{OLLAMA_MODEL}' loaded but returned no content. "
            "Try again or check the model."
        )
