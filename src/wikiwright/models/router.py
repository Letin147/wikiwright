"""Minimal OpenAI-compatible LLM router: stdlib http, cost tracking, budget fuse.

Transport decision (ADR-0001): plain urllib, zero new dependencies — the openai
SDK is deferred until streaming/SSE is actually needed (v0.3+), and this module
is the only place that will ever need to change.
"""

from __future__ import annotations

import http.client
import json
import os
import time
import urllib.error
import urllib.request
from pathlib import Path

from pydantic import BaseModel

# Peak (conservative) USD prices per 1M tokens, from the official pricing page
# 2026-10-28; off-peak is half — budget math always assumes the worse case.
PRICES_PER_MTOK: dict[str, dict[str, float]] = {
    "deepseek-flash": {"in_hit": 0.006, "in_miss": 0.30, "out": 1.20},
    "deepseek-v4-pro": {"in_hit": 0.044, "in_miss": 1.32, "out": 3.96},
}


class LLMError(RuntimeError):
    """Explicit API failure (never silent)."""


class BudgetExceeded(LLMError):
    """The run hit its WIKIWRIGHT_BUDGET_CNY ceiling — stop before spending more."""


class Usage(BaseModel):
    """Token accounting for one call."""

    prompt_tokens: int = 0
    prompt_cache_hit_tokens: int = 0
    prompt_cache_miss_tokens: int = 0
    completion_tokens: int = 0
    cost_usd: float = 0.0


def estimate_cost_usd(model: str, miss: int, hit: int, out: int) -> float:
    """Cost of one call under peak pricing; unknown models are priced as flash."""
    price = PRICES_PER_MTOK.get(model, PRICES_PER_MTOK["deepseek-flash"])
    return (
        miss / 1e6 * price["in_miss"] + hit / 1e6 * price["in_hit"] + out / 1e6 * price["out"]
    )


def load_env_file(path: str | Path = ".env") -> dict[str, str]:
    """Parse KEY=VALUE lines; real environment variables take precedence."""
    env_path = Path(path)
    if not env_path.exists():
        return {}
    loaded: dict[str, str] = {}
    for line in env_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        loaded.setdefault(key.strip(), value.strip().strip("'\""))
    return loaded


def _cfg(key: str, default: str = "") -> str:
    for source in (os.environ, load_env_file()):
        if key in source and source[key]:
            return source[key]
    return default


class LLMClient:
    """One OpenAI-compatible endpoint + cumulative budget fuse for one run."""

    RETRIES = 2

    def __init__(self, budget_cny: float | None = None) -> None:
        self.api_key = _cfg("DEEPSEEK_API_KEY")
        self.base_url = _cfg("DEEPSEEK_BASE_URL", "https://api.deepseek.com/v1").rstrip("/")
        self.model = _cfg("DEEPSEEK_MODEL_FLASH", "deepseek-flash")
        if not self.api_key:
            raise LLMError(
                "DEEPSEEK_API_KEY not set (export it or put it in .env); "
                "providers and keys are documented in manual/02 §15"
            )
        usd_cny = float(_cfg("WIKIWRIGHT_USD_CNY", "7.2"))
        self.budget_usd = (
            float(_cfg("WIKIWRIGHT_BUDGET_CNY", "10")) / usd_cny
            if budget_cny is None
            else budget_cny / usd_cny
        )
        self.spent_usd = 0.0
        self.calls = 0

    # -- api ---------------------------------------------------------------

    def chat(
        self,
        messages: list[dict],
        model: str | None = None,
        effort: str = "low",
        temperature: float = 0.0,
        max_tokens: int = 512,
    ) -> tuple[str, Usage]:
        """Return (content, usage); retries transient errors, surfaces the rest."""
        if self.spent_usd >= self.budget_usd:
            raise BudgetExceeded(
                f"budget {self.budget_usd:.4f} USD exhausted (spent {self.spent_usd:.4f}); "
                "raise WIKIWRIGHT_BUDGET_CNY or narrow the task"
            )
        model = model or self.model
        body = json.dumps(
            {
                "model": model,
                "messages": messages,
                "effort": effort,
                "temperature": temperature,
                "max_tokens": max_tokens,
                "stream": False,
            }
        ).encode("utf-8")
        request = urllib.request.Request(
            f"{self.base_url}/chat/completions",
            data=body,
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
        )
        last_error: Exception | None = None
        for attempt in range(self.RETRIES + 1):
            try:
                with urllib.request.urlopen(request, timeout=120) as response:
                    payload = json.loads(response.read().decode("utf-8"))
                break
            except urllib.error.HTTPError as exc:
                detail = exc.read().decode("utf-8", errors="replace")[:300]
                raise LLMError(f"{model} HTTP {exc.code}: {detail}") from exc
            except (OSError, http.client.HTTPException) as exc:
                # covers URLError/timeout AND RemoteDisconnected/reset (EXP-03 lesson:
                # deepseek connections drop mid-request; never let these escape as-is)
                last_error = exc
                if attempt < self.RETRIES:
                    time.sleep(0.6 * (attempt + 1))
        else:
            raise LLMError(f"{model} unreachable after {self.RETRIES + 1} tries: {last_error}")

        choice = payload["choices"][0]["message"]
        raw_usage = payload.get("usage", {})
        usage = Usage(
            prompt_tokens=raw_usage.get("prompt_tokens", 0),
            prompt_cache_hit_tokens=raw_usage.get("prompt_cache_hit_tokens", 0),
            prompt_cache_miss_tokens=raw_usage.get("prompt_cache_miss_tokens", 0),
            completion_tokens=raw_usage.get("completion_tokens", 0),
        )
        usage.cost_usd = estimate_cost_usd(
            model,
            usage.prompt_cache_miss_tokens,
            usage.prompt_cache_hit_tokens,
            usage.completion_tokens,
        )
        self.spent_usd += usage.cost_usd
        self.calls += 1
        return (choice.get("content") or ""), usage

    def summary(self) -> str:
        cny = self.spent_usd * 7.2
        return (
            f"{self.calls} calls, ${self.spent_usd:.5f} (~¥{cny:.4f}) "
            f"of ${self.budget_usd:.2f} budget"
        )
