import requests

from .config import OLLAMA_MODEL, OLLAMA_TIMEOUT, OLLAMA_URL


def generate(prompt: str) -> str:
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
    return response.json()["message"]["content"].strip()
