import os
import time
from typing import Dict, Any, Tuple

import requests


class SaviClient:
    """Minimal client for an OpenAI-compatible chat endpoint.

    Supported environment variables (prefer OPENAI_*):
      - OPENAI_BASE_URL or SAVI_API_BASE: e.g. https://api.openai.com/v1 or full /chat/completions
      - OPENAI_API_KEY  or SAVI_API_KEY: bearer token
      - OPENAI_MODEL    or SAVI_MODEL:   model name (default: gpt-4o)
      - SAVI_API_PATH:  optional, defaults to /chat/completions
    """

    def __init__(self) -> None:
        base = os.getenv("OPENAI_BASE_URL") or os.getenv("SAVI_API_BASE", "")
        base = base.rstrip("/")
        path = os.getenv("SAVI_API_PATH", "/chat/completions")
        if base.endswith("/chat/completions"):
            self.url = base
        elif base:
            self.url = f"{base}{path}"
        else:
            self.url = ""
        self.api_key = os.getenv("OPENAI_API_KEY") or os.getenv("SAVI_API_KEY", "")
        self.model = os.getenv("OPENAI_MODEL") or os.getenv("SAVI_MODEL") or "gpt-4o"

    def chat(self, prompt: str, system: str = None, max_tokens: int = 256, temperature: float = 0.2) -> Tuple[str, float, Dict[str, Any]]:
        headers = {
            "Content-Type": "application/json",
        }
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        t0 = time.perf_counter()
        resp = requests.post(self.url, json=payload, headers=headers, timeout=60)
        dt = (time.perf_counter() - t0) * 1000.0
        resp.raise_for_status()
        data = resp.json()
        # OpenAI-compatible
        try:
            text = data["choices"][0]["message"]["content"].strip()
        except Exception:  # pragma: no cover
            # Try a few common shapes
            text = (
                data.get("output")
                or data.get("text")
                or str(data)
            )
        return text, dt, data

