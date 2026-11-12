"""LLM interface (P3-06, A1).

- `get_llm()`: report explanations / comparisons - Anthropic Messages API via the official SDK.
- `get_assistant_llm()`: the chatbot - Google Gemini (REST) when GEMINI_API_KEY is set, else `get_llm()`.
When no key is configured, `NoLLM` is returned and services fall back to deterministic, source-grounded
template text - the app stays fully usable offline. Every output still passes safety_validator.
"""
from __future__ import annotations

import json
import os
from functools import lru_cache
from typing import Protocol

from app.core.config import get_settings
from app.core.logging import get_logger

log = get_logger("llm")


class LLMError(RuntimeError):
    pass


class LLMRefused(LLMError):
    pass


class LLMClient(Protocol):
    name: str
    available: bool

    def complete(self, system: str, messages: list[dict], max_tokens: int = 4000,
                 json_schema: dict | None = None, effort: str | None = None) -> str: ...


class NoLLM:
    name = "none"
    available = False

    def complete(self, system: str, messages: list[dict], max_tokens: int = 4000, json_schema: dict | None = None,
                 effort: str | None = None) -> str:
        raise LLMError("No LLM configured")


class AnthropicClient:
    available = True

    def __init__(self, api_key: str | None, model: str, effort: str = "medium"):
        import anthropic

        self._anthropic = anthropic
        self.client = anthropic.Anthropic(api_key=api_key or None, timeout=90.0, max_retries=2)
        self.model = model
        self.effort = effort
        self.name = model

    def complete(self, system: str, messages: list[dict], max_tokens: int = 4000, json_schema: dict | None = None,
                 effort: str | None = None) -> str:
        output_config: dict = {"effort": effort or self.effort}
        if json_schema is not None:
            output_config["format"] = {"type": "json_schema", "schema": json_schema}
        a = self._anthropic
        try:
            response = self.client.beta.messages.create(
                model=self.model,
                max_tokens=max_tokens,
                system=system,
                messages=messages,
                output_config=output_config,
                # Server-side refusal fallback: a declined request is re-run on a fallback model.
                betas=["server-side-fallback-2026-07-01"],
                fallbacks="default",
            )
        except a.RateLimitError as exc:
            raise LLMError("LLM rate limited") from exc
        except a.APIStatusError as exc:
            raise LLMError(f"LLM API error {exc.status_code}") from exc
        except a.APIConnectionError as exc:
            raise LLMError("LLM connection error") from exc
        if response.stop_reason == "refusal":
            raise LLMRefused("LLM declined the request")
        text = "".join(b.text for b in response.content if b.type == "text").strip()
        if not text:
            raise LLMError("Empty LLM response")
        return text


class GeminiClient:
    """Gemini generateContent over REST (httpx is already a dependency). Falls back to a lighter model when busy."""

    available = True
    URL = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"

    def __init__(self, api_key: str, model: str, fallback_model: str | None = None):
        import httpx

        self._httpx = httpx
        self.client = httpx.Client(timeout=25.0)
        self.api_key = api_key
        self.models = [m for m in (model, fallback_model) if m]
        self.name = model

    def complete(self, system: str, messages: list[dict], max_tokens: int = 4000, json_schema: dict | None = None,
                 effort: str | None = None) -> str:
        body: dict = {
            "systemInstruction": {"parts": [{"text": system}]},
            "contents": [{"role": "model" if m["role"] == "assistant" else "user", "parts": [{"text": m["content"]}]}
                         for m in messages],
            "generationConfig": {"maxOutputTokens": max_tokens,
                                 **({"responseMimeType": "application/json"} if json_schema else {})},
        }
        last: Exception | None = None
        for model in self.models:
            try:
                r = self.client.post(self.URL.format(model=model), headers={"x-goog-api-key": self.api_key}, json=body)
            except self._httpx.HTTPError as exc:  # timeout / connection - try the fallback model
                last = LLMError(f"Gemini connection error ({type(exc).__name__})")
                continue
            if r.status_code in (429, 500, 503):
                last = LLMError(f"Gemini busy ({r.status_code})")
                continue
            if r.status_code != 200:
                raise LLMError(f"Gemini API error {r.status_code}")
            data = r.json()
            if data.get("promptFeedback", {}).get("blockReason"):
                raise LLMRefused("Gemini declined the request")
            cand = (data.get("candidates") or [{}])[0]
            if cand.get("finishReason") in ("SAFETY", "PROHIBITED_CONTENT", "BLOCKLIST", "SPII"):
                raise LLMRefused("Gemini declined the request")
            text = "".join(p.get("text", "") for p in cand.get("content", {}).get("parts", []) if not p.get("thought"))
            if text.strip():
                self.name = model
                return text.strip()
            last = LLMError("Empty Gemini response")
        raise last or LLMError("Gemini unavailable")


@lru_cache
def get_assistant_llm() -> LLMClient:
    s = get_settings()
    if s.gemini_api_key:
        return GeminiClient(s.gemini_api_key, s.gemini_model, s.gemini_fallback_model)
    return get_llm()


def parse_json(text: str) -> dict:
    t = text.strip()
    if t.startswith("```"):
        t = t.strip("`")
        t = t[t.find("{"):]
    return json.loads(t[t.find("{"): t.rfind("}") + 1])


@lru_cache
def get_llm() -> LLMClient:
    s = get_settings()
    key = s.llm_api_key or os.environ.get("ANTHROPIC_API_KEY")
    if s.llm_provider == "anthropic" and key:
        try:
            return AnthropicClient(key, s.llm_model, s.llm_effort)
        except Exception as exc:  # pragma: no cover
            log.warning("Anthropic client unavailable: %s", type(exc).__name__)
    return NoLLM()
