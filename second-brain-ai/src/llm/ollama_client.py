"""
Ollama utilities — health check, model listing, streaming calls.
Uses streaming so responses appear word-by-word instead of waiting
for the full response (much better UX for local models).
"""
import logging
import urllib.request
import urllib.error
import json
from typing import List, Optional, Generator

logger = logging.getLogger(__name__)

OLLAMA_BASE_URL = "http://localhost:11434"
OLLAMA_TIMEOUT = 300  # 5 min hard timeout per request

RECOMMENDED_MODELS = {
    "llama3.2":       {"size": "2GB",  "speed": "⚡ Fast",   "quality": "⭐⭐⭐⭐",  "desc": "Best overall for most machines"},
    "llama3.1":       {"size": "4.7GB","speed": "🐢 Medium", "quality": "⭐⭐⭐⭐⭐", "desc": "Higher quality, needs more RAM"},
    "mistral":        {"size": "4.1GB","speed": "🐢 Medium", "quality": "⭐⭐⭐⭐",  "desc": "Great for Q&A and summaries"},
    "gemma2:2b":      {"size": "1.6GB","speed": "⚡ Fast",   "quality": "⭐⭐⭐",    "desc": "Lightweight, good for low-RAM machines"},
    "phi3:mini":      {"size": "2.2GB","speed": "⚡ Fast",   "quality": "⭐⭐⭐⭐",  "desc": "Microsoft model, surprisingly capable"},
    "codellama":      {"size": "3.8GB","speed": "🐢 Medium", "quality": "⭐⭐⭐⭐",  "desc": "Best for technical/coding content"},
    "deepseek-r1:7b": {"size": "4.7GB","speed": "🐢 Medium", "quality": "⭐⭐⭐⭐⭐", "desc": "Strong reasoning model"},
}


def is_ollama_running() -> bool:
    """Check if Ollama server is running on localhost:11434."""
    try:
        req = urllib.request.Request(f"{OLLAMA_BASE_URL}/api/tags")
        with urllib.request.urlopen(req, timeout=3) as resp:
            return resp.status == 200
    except Exception:
        return False


def get_installed_models() -> List[str]:
    """Return list of model names currently installed in Ollama."""
    try:
        req = urllib.request.Request(f"{OLLAMA_BASE_URL}/api/tags")
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read())
            return [m["name"].split(":")[0] for m in data.get("models", [])]
    except Exception as e:
        logger.warning("Could not fetch Ollama models: %s", e)
        return []


def get_best_available_model() -> Optional[str]:
    """Return the best available installed model."""
    installed = get_installed_models()
    for model in RECOMMENDED_MODELS:
        if model in installed:
            return model
    return installed[0] if installed else None


def stream_ollama(model: str, prompt: str, max_tokens: int = 400) -> Generator[str, None, None]:
    """
    Stream response from Ollama token by token.
    Yields each token as it arrives — use in Streamlit with st.write_stream().

    Options tuned for speed:
    - num_ctx=512:   tiny context window — fast on any machine
    - num_predict:   hard cap on output length
    - temperature:   0.5 for faster, more focused sampling
    - num_thread:    use all CPU cores
    """
    payload = json.dumps({
        "model": model,
        "prompt": prompt,
        "stream": True,
        "options": {
            "num_predict": max_tokens,
            "temperature": 0.5,
            "num_ctx": 512,
            "num_thread": 8,
            "num_batch": 8,
            "top_k": 20,
            "top_p": 0.9,
        }
    }).encode("utf-8")

    req = urllib.request.Request(
        f"{OLLAMA_BASE_URL}/api/generate",
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST"
    )

    first_token_received = False
    try:
        with urllib.request.urlopen(req, timeout=OLLAMA_TIMEOUT) as resp:
            for line in resp:
                if not line.strip():
                    continue
                try:
                    chunk = json.loads(line.decode("utf-8"))
                    token = chunk.get("response", "")
                    if token:
                        first_token_received = True
                        yield token
                    if chunk.get("done", False):
                        break
                except json.JSONDecodeError:
                    continue

    except urllib.error.URLError as e:
        raise ConnectionError(
            f"Ollama connection failed. Is it running?\n"
            f"Start with: ollama serve\nError: {e}"
        )
    except Exception:
        if not first_token_received:
            raise TimeoutError(
                "Ollama is too slow on this machine for the current model.\n\n"
                "Fix options (pick one):\n"
                "1. Use a smaller model: ollama pull gemma2:2b\n"
                "2. Use a cloud provider (Groq is free and fast)"
            )
        return


def call_ollama(model: str, prompt: str, max_tokens: int = 400) -> str:
    """
    Non-streaming Ollama call — collects full streamed response.
    Used for MCQ generation, flashcards, concept maps.
    """
    return "".join(stream_ollama(model, prompt, max_tokens))


def benchmark_model(model: str, timeout_sec: int = 15) -> Optional[float]:
    """
    Quick benchmark: send a tiny prompt and measure tokens/sec.
    Returns tokens_per_second or None if timed out.
    """
    import time
    test_prompt = "Say hello in one word."
    start = time.time()
    token_count = 0

    payload = json.dumps({
        "model": model,
        "prompt": test_prompt,
        "stream": True,
        "options": {"num_predict": 10, "num_ctx": 128, "temperature": 0.1}
    }).encode("utf-8")

    req = urllib.request.Request(
        f"{OLLAMA_BASE_URL}/api/generate",
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST"
    )

    try:
        with urllib.request.urlopen(req, timeout=timeout_sec) as resp:
            for line in resp:
                if not line.strip():
                    continue
                try:
                    chunk = json.loads(line.decode("utf-8"))
                    if chunk.get("response"):
                        token_count += 1
                    if chunk.get("done"):
                        break
                except json.JSONDecodeError:
                    continue
        elapsed = time.time() - start
        return round(token_count / elapsed, 1) if elapsed > 0 else None
    except Exception:
        return None


def get_install_instructions() -> str:
    return """
**Install Ollama (free, one-time setup):**

**Mac/Linux:**
```bash
curl -fsSL https://ollama.com/install.sh | sh
```

**Windows:**
Download from [ollama.com/download](https://ollama.com/download)

**Pull a model:**
```bash
ollama pull llama3.2      # Recommended (2GB, fast)
ollama pull gemma2:2b     # Lightest option (1.6GB)
```

**Start Ollama:**
```bash
ollama serve
```
"""
