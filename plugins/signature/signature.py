"""
hermes-signature — appends a configurable footer to every LLM response.

Footer format (default):
    -# ⚡ ignyte · MiniMax-M2.7 · minimax · ~1.2s est.

Config (config.yaml):
    signature:
      enabled: true
      agent_name: "ignyte"
      icon: "⚡"
      show_model: true
      show_provider: true
      show_latency: true
      platforms: []          # empty = all platforms; or ["discord", "bluebubbles"]
"""

from __future__ import annotations

import time
from typing import Any

# Thread-local start time set at hook entry
_turn_start: float = 0.0


def _load_config() -> dict:
    try:
        from hermes_cli.config import load_config
        cfg = load_config() or {}
        return cfg.get("signature", {})
    except Exception:
        return {}


def on_pre_llm_call(**kwargs: Any) -> None:
    """Record turn start time as early as possible."""
    global _turn_start
    _turn_start = time.monotonic()


def on_transform_llm_output(text: str, **kwargs: Any) -> str | None:
    cfg = _load_config()

    if not cfg.get("enabled", True):
        return None

    # Platform filter
    allowed_platforms = cfg.get("platforms", [])
    if allowed_platforms:
        platform = kwargs.get("platform", "")
        if platform not in allowed_platforms:
            return None

    icon = cfg.get("icon", "⚡")
    agent_name = cfg.get("agent_name", "ignyte")
    show_model = cfg.get("show_model", True)
    show_provider = cfg.get("show_provider", True)
    show_latency = cfg.get("show_latency", True)

    # Pull model/provider from agent context if available
    agent = kwargs.get("agent") or kwargs.get("context_obj")
    model = ""
    provider = ""
    if agent:
        model = getattr(agent, "model", "") or ""
        provider = getattr(agent, "provider", "") or ""

    parts = [f"{icon} {agent_name}"]
    if show_model and model:
        parts.append(model)
    if show_provider and provider:
        parts.append(provider)
    if show_latency and _turn_start:
        elapsed = time.monotonic() - _turn_start
        parts.append(f"~{elapsed:.1f}s est.")

    footer = "-# " + " · ".join(parts)
    return text + "\n\n" + footer
