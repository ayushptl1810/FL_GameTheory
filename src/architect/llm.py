from __future__ import annotations
import os
import re

class LLMError(RuntimeError):
    pass

# Reasoning models (DeepSeek-R1, Nemotron "reasoning on", QwQ, ...) prefix the
# answer with a <think>...</think> block that breaks json.loads downstream.
_THINK_RE = re.compile(r"^\s*<think>.*?</think>\s*", re.DOTALL | re.IGNORECASE)


def _strip_think(text: str) -> str:
    return _THINK_RE.sub("", text or "", count=1)

# provider -> (base_url, api-key env var, default model)
# All three speak the OpenAI chat-completions wire format, so one code path
# covers them; switching provider is one env var.
_PROVIDERS = {
    "nvidia": ("https://integrate.api.nvidia.com/v1", "NVIDIA_API_KEY",
               "meta/llama-3.3-70b-instruct"),
    "groq":   ("https://api.groq.com/openai/v1", "GROQ_API_KEY",
               "llama-3.3-70b-versatile"),
    "openai": ("https://api.openai.com/v1", "OPENAI_API_KEY", "gpt-4o"),
}


def llm_complete(system: str, user: str, *, json_mode: bool = False) -> str:
    provider = os.environ.get("ARCHITECT_LLM_PROVIDER", "nvidia")
    if provider not in _PROVIDERS:
        raise LLMError(f"unknown provider {provider!r}; expected one of {sorted(_PROVIDERS)}")
    base_url, key_env, default_model = _PROVIDERS[provider]
    model = os.environ.get("ARCHITECT_LLM_MODEL", default_model)
    api_key = os.environ.get("ARCHITECT_LLM_API_KEY") or os.environ.get(key_env)
    if not api_key:
        raise LLMError(f"no API key: set {key_env} (or ARCHITECT_LLM_API_KEY) for provider {provider!r}")

    try:
        from openai import OpenAI
        client = OpenAI(base_url=base_url, api_key=api_key)
        kwargs: dict = {
            "model": model,
            "max_tokens": 4096,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
        }
        if json_mode:
            # Supported by NVIDIA NIM / Groq / OpenAI for most instruct models.
            # If a given model rejects it, retry once without.
            kwargs["response_format"] = {"type": "json_object"}
        try:
            resp = client.chat.completions.create(**kwargs)
        except Exception:  # noqa: BLE001
            if "response_format" in kwargs:
                kwargs.pop("response_format")
                resp = client.chat.completions.create(**kwargs)
            else:
                raise
        return _strip_think(resp.choices[0].message.content or "")
    except LLMError:
        raise
    except Exception as exc:  # noqa: BLE001
        raise LLMError(str(exc)) from exc
