"""
hermes-signature — appends a configurable signature footer to every LLM response.

Footer example:
    -# ⚡ ignyte · MiniMax-M2.7 · minimax · ~1.2s est. · 1,247↑ 600↓ 1,847 tok · ~$0.0004
    -# 🔧 web_search×3 · bash×2 · read_file

Hooks used:
    pre_llm_call         — record turn start time, reset accumulators
    post_api_request     — accumulate token usage per session
    post_tool_call       — accumulate tool call counts per session
    transform_llm_output — build and append footer

Config (config.yaml):
    signature:
      enabled: true
      agent_name: "ignyte"
      icon: "⚡"
      show_model: true
      show_provider: true
      show_latency: true
      show_tokens: true
      show_cost: true
      show_tools: true
      show_reset: true     # resets in Xh Ym (anthropic, openai-codex, openrouter)
      show_usage_pct: false # X% used (same providers; off by default)
      platforms: []        # empty = all; ["discord", "bluebubbles"] to restrict
      pricing:             # optional overrides (USD per 1M tokens)
        MiniMax-M2.7:
          input: 0.30
          output: 1.10
"""

from __future__ import annotations

import threading
import time
from typing import Any

from .pricing import estimate_cost
from .usage import get_reset_label, get_usage_label, refresh_in_background

# Per-session token accumulator: {session_id: {"prompt": int, "completion": int}}
_session_usage: dict[str, dict[str, int]] = {}
_usage_lock = threading.Lock()

# Per-session turn start time: {session_id: float}
_turn_start: dict[str, float] = {}
_start_lock = threading.Lock()

# Per-session tool call counts: {session_id: {tool_name: count}}
_session_tools: dict[str, dict[str, int]] = {}
_tools_lock = threading.Lock()


def _load_config() -> dict:
    try:
        from hermes_cli.config import load_config
        cfg = load_config() or {}
        return cfg.get("signature", {})
    except Exception:
        return {}


def on_pre_llm_call(**kwargs: Any) -> None:
    """Record turn start time and reset accumulators for this session."""
    session_id = kwargs.get("session_id", "") or ""
    with _start_lock:
        _turn_start[session_id] = time.monotonic()
    with _usage_lock:
        _session_usage[session_id] = {"prompt": 0, "completion": 0}
    with _tools_lock:
        _session_tools[session_id] = {}


def on_post_api_request(**kwargs: Any) -> None:
    """Accumulate token usage across all API calls in this turn."""
    session_id = kwargs.get("session_id", "") or ""
    usage = kwargs.get("usage") or {}
    if not usage:
        return
    prompt = usage.get("prompt_tokens") or usage.get("input_tokens") or 0
    completion = usage.get("completion_tokens") or usage.get("output_tokens") or 0
    with _usage_lock:
        bucket = _session_usage.setdefault(session_id, {"prompt": 0, "completion": 0})
        bucket["prompt"] += prompt
        bucket["completion"] += completion


def on_post_tool_call(**kwargs: Any) -> None:
    """Accumulate tool call counts for this turn."""
    session_id = kwargs.get("session_id", "") or ""
    tool_name = kwargs.get("tool_name", "") or ""
    if not tool_name:
        return
    with _tools_lock:
        bucket = _session_tools.setdefault(session_id, {})
        bucket[tool_name] = bucket.get(tool_name, 0) + 1


def on_transform_llm_output(response_text: str, **kwargs: Any) -> str | None:
    cfg = _load_config()

    if not cfg.get("enabled", True):
        return None

    # Platform filter
    allowed_platforms = cfg.get("platforms", [])
    if allowed_platforms:
        platform = kwargs.get("platform", "")
        if platform not in allowed_platforms:
            return None

    session_id = kwargs.get("session_id", "") or ""
    model = kwargs.get("model", "") or ""

    icon        = cfg.get("icon", "⚡")
    agent_name  = cfg.get("agent_name", "hermes")
    show_model     = cfg.get("show_model", True)
    show_provider  = cfg.get("show_provider", True)
    show_latency   = cfg.get("show_latency", True)
    show_tokens    = cfg.get("show_tokens", True)
    show_cost      = cfg.get("show_cost", True)
    show_tools     = cfg.get("show_tools", True)
    show_reset     = cfg.get("show_reset", True)
    show_usage_pct = cfg.get("show_usage_pct", False)

    provider = kwargs.get("provider", "")

    parts: list[str] = [f"{icon} {agent_name}"]

    if show_model and model:
        parts.append(model)

    if show_provider and provider:
        parts.append(provider)

    # Latency
    if show_latency:
        with _start_lock:
            start = _turn_start.get(session_id)
        if start:
            elapsed = time.monotonic() - start
            parts.append(f"~{elapsed:.1f}s est.")

    # Tokens + cost
    with _usage_lock:
        usage = _session_usage.pop(session_id, None)

    if usage:
        prompt_tok = usage["prompt"]
        completion_tok = usage["completion"]
        total_tok = prompt_tok + completion_tok

        if show_tokens and total_tok:
            parts.append(f"{prompt_tok:,}↑ {completion_tok:,}↓ {total_tok:,} tok")

        if show_cost:
            custom_pricing = cfg.get("pricing")
            cost = estimate_cost(model, prompt_tok, completion_tok, custom_pricing)
            if cost is not None:
                if cost == 0.0:
                    parts.append("free")
                elif cost < 0.0001:
                    parts.append("<$0.0001")
                else:
                    parts.append(f"~${cost:.4f}")

    # Tool calls
    with _tools_lock:
        tools = _session_tools.pop(session_id, None)

    # Usage quota — read from cache (populated by background thread on prior call)
    if show_usage_pct:
        label = get_usage_label(provider)
        if label:
            parts.append(label)

    if show_reset:
        label = get_reset_label(provider)
        if label:
            parts.append(label)

    # Kick off background refresh so the NEXT call has fresh data
    refresh_in_background(provider)

    footer = "-# " + " · ".join(parts)

    if show_tools and tools:
        tool_parts = []
        for name, count in tools.items():
            tool_parts.append(f"{name}×{count}" if count > 1 else name)
        footer += "\n-# 🔧 " + " · ".join(tool_parts)

    return response_text + "\n\n" + footer
