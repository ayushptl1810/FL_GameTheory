from __future__ import annotations
import os

class LLMError(RuntimeError):
    pass

def llm_complete(system: str, user: str, *, json_mode: bool = False) -> str:
    provider = os.environ.get("ARCHITECT_LLM_PROVIDER", "anthropic")
    model = os.environ.get("ARCHITECT_LLM_MODEL", "claude-sonnet-5")
    try:
        if provider == "anthropic":
            import anthropic
            client = anthropic.Anthropic()
            msg = client.messages.create(
                model=model, max_tokens=4096,
                system=system, messages=[{"role": "user", "content": user}])
            return msg.content[0].text
        raise LLMError(f"unknown provider {provider!r}")
    except LLMError:
        raise
    except Exception as exc:  # noqa: BLE001
        raise LLMError(str(exc)) from exc
