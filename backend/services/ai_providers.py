"""
AI provider adapters — a small common interface so ai_engine.py doesn't
care whether it's talking to paid Anthropic, Google's free-tier Gemini
API, or a fully local, $0-forever Ollama instance.

Every provider implements the same async signature:

    await provider.complete(system_prompt: str, messages: list[dict]) -> str

`messages` is a list of {"role": "user"|"assistant", "content": str},
oldest first — the same shape ai_engine.py already builds for Anthropic.

Selected at runtime via settings.AI_PROVIDER ("anthropic" | "gemini" | "ollama").
"""
from __future__ import annotations

import json
from abc import ABC, abstractmethod
from typing import Any

import httpx

from core.config import settings
from utils.logger import get_logger

log = get_logger(__name__)


class AIProviderError(RuntimeError):
    pass


class AIProvider(ABC):
    @abstractmethod
    async def complete(self, system_prompt: str, messages: list[dict[str, str]]) -> str:
        ...


# --------------------------------------------------------------------------- #
# Anthropic — paid, pay-per-token, no ongoing free tier
# --------------------------------------------------------------------------- #


class AnthropicProvider(AIProvider):
    def __init__(self) -> None:
        from anthropic import AsyncAnthropic  # imported lazily so it's optional

        if not settings.ANTHROPIC_API_KEY:
            log.warning(
                "AI_PROVIDER=anthropic but ANTHROPIC_API_KEY is empty — "
                "requests will fail until it's set."
            )
        self._client = AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY)
        self._model = settings.AI_MODEL
        self._max_tokens = settings.AI_MAX_TOKENS

    async def complete(self, system_prompt: str, messages: list[dict[str, str]]) -> str:
        try:
            response = await self._client.messages.create(
                model=self._model,
                max_tokens=self._max_tokens,
                system=system_prompt,
                messages=messages,
            )
        except Exception as exc:  # noqa: BLE001
            raise AIProviderError(f"Anthropic request failed: {exc}") from exc

        parts = [b.text for b in response.content if getattr(b, "type", None) == "text"]
        return "\n".join(parts).strip()


# --------------------------------------------------------------------------- #
# Gemini — Google's genuinely free API tier (Flash / Flash-Lite), no card
# required. Get a key at https://aistudio.google.com/apikey
# --------------------------------------------------------------------------- #


class GeminiProvider(AIProvider):
    _BASE_URL = "https://generativelanguage.googleapis.com/v1beta/models"

    def __init__(self) -> None:
        if not settings.GEMINI_API_KEY:
            log.warning(
                "AI_PROVIDER=gemini but GEMINI_API_KEY is empty — "
                "requests will fail until it's set."
            )
        self._api_key = settings.GEMINI_API_KEY
        self._model = settings.GEMINI_MODEL
        self._client = httpx.AsyncClient(timeout=60.0)

    async def complete(self, system_prompt: str, messages: list[dict[str, str]]) -> str:
        # Gemini uses "model" instead of "assistant" for the AI turn, and
        # wraps text in a `parts` array rather than a flat string.
        contents = [
            {
                "role": "model" if m["role"] == "assistant" else "user",
                "parts": [{"text": m["content"]}],
            }
            for m in messages
        ]
        payload = {
            "contents": contents,
            "systemInstruction": {"parts": [{"text": system_prompt}]},
            "generationConfig": {"temperature": 0.4, "maxOutputTokens": settings.AI_MAX_TOKENS},
        }
        url = f"{self._BASE_URL}/{self._model}:generateContent?key={self._api_key}"

        try:
            resp = await self._client.post(url, json=payload)
            resp.raise_for_status()
            data = resp.json()
        except httpx.HTTPStatusError as exc:
            raise AIProviderError(
                f"Gemini request failed ({exc.response.status_code}): {exc.response.text[:300]}"
            ) from exc
        except Exception as exc:  # noqa: BLE001
            raise AIProviderError(f"Gemini request failed: {exc}") from exc

        try:
            candidate = data["candidates"][0]
            text_parts = [p.get("text", "") for p in candidate["content"]["parts"]]
            return "".join(text_parts).strip()
        except (KeyError, IndexError) as exc:
            raise AIProviderError(f"Unexpected Gemini response shape: {data}") from exc


# --------------------------------------------------------------------------- #
# Ollama — fully local, $0 forever, no signup, no rate limits, no data
# leaving the machine. Requires Ollama running (`ollama serve`, usually
# automatic) with a model pulled, e.g. `ollama pull llama3.1`.
# --------------------------------------------------------------------------- #


class OllamaProvider(AIProvider):
    def __init__(self) -> None:
        self._base_url = settings.OLLAMA_BASE_URL.rstrip("/")
        self._model = settings.OLLAMA_MODEL
        # Local inference on modest hardware can be slow — generous timeout.
        self._client = httpx.AsyncClient(timeout=180.0)

    async def complete(self, system_prompt: str, messages: list[dict[str, str]]) -> str:
        payload = {
            "model": self._model,
            "messages": [{"role": "system", "content": system_prompt}, *messages],
            "stream": False,
            "options": {"temperature": 0.4},
        }
        url = f"{self._base_url}/api/chat"

        try:
            resp = await self._client.post(url, json=payload)
            resp.raise_for_status()
            data = resp.json()
        except httpx.ConnectError as exc:
            raise AIProviderError(
                "Could not reach Ollama. Is it running? Try `ollama serve` and "
                f"`ollama pull {self._model}` first. ({exc})"
            ) from exc
        except httpx.HTTPStatusError as exc:
            raise AIProviderError(
                f"Ollama request failed ({exc.response.status_code}): {exc.response.text[:300]}"
            ) from exc
        except Exception as exc:  # noqa: BLE001
            raise AIProviderError(f"Ollama request failed: {exc}") from exc

        try:
            return data["message"]["content"].strip()
        except KeyError as exc:
            raise AIProviderError(f"Unexpected Ollama response shape: {data}") from exc


# --------------------------------------------------------------------------- #
# Factory
# --------------------------------------------------------------------------- #

_PROVIDERS: dict[str, type[AIProvider]] = {
    "anthropic": AnthropicProvider,
    "gemini": GeminiProvider,
    "ollama": OllamaProvider,
}


def get_provider() -> AIProvider:
    provider_name = settings.AI_PROVIDER.lower().strip()
    provider_cls = _PROVIDERS.get(provider_name)
    if not provider_cls:
        raise AIProviderError(
            f"Unknown AI_PROVIDER '{provider_name}'. Valid options: {', '.join(_PROVIDERS)}"
        )
    log.info(f"AI engine using provider: {provider_name}")
    return provider_cls()
