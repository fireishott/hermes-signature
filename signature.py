"""
hermes-signature — appends a configurable signature footer to every LLM response.

Footer example:
    -# ⚡ ignyte · MiniMax-M2.7 · minimax · ~1.2s est. · 1,247↑ 600↓ 1,847 tok · ~$0.0004 · 12 turns
    -# 🔧 web_search×3 · bash×2 · vision_analyze×3
    -# 🔩 gemini-2.5-flash-lite×3

Hooks used:
    pre_llm_call         — record turn start time, reset accumulators
    post_api_request     — accumulate token usage per model per session
    post_tool_call       — accumulate tool call counts; map aux tools to backing models
    transform_llm_output — build and append footer

Config (config.yaml):
    signature:
      enabled: true
      agent_name: "ignyte"
      icon: "⚡"
      default_model: "MiniMax-M2.7"  # fallback when model not in hook kwargs
      show_model: true
      show_provider: true
      show_latency: true
      show_tokens: true           # master toggle for token display
      show_tokens_direction: true # show input↑ / output↓ counts separately
      show_tokens_total: true     # show combined total token count
      show_cost: true
      show_tools: true
      show_turns: true        # number of turns in this session
      show_aux: true          # show aux model line derived from aux_tool_models map
      show_session_cost: true # cumulative spend for the current session
      show_balance: true      # account balance remaining (deepseek, openrouter)
      show_reset: true        # resets in Xh Ym (anthropic, openai-codex, openrouter)
      show_usage_pct: false   # X% used (same providers; off by default)
      order:                  # footer field order (omit to use default)
        - model
        - provider
        - latency
        - tokens_direction
        - tokens_total
        - cost
        - session_cost
        - turns
        - usage_pct
        - reset
        - balance
        - tools
        - aux
      platforms: []        # empty = all; ["discord", "bluebubbles"] to restrict
      aux_tool_models:     # map tool name → backing model for the 🔩 line
        vision_analyze: "gemini-2.5-flash-lite"
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
from .usage import get_balance_label, get_reset_label, get_usage_label, refresh_in_background

# Per-session token accumulator: {session_id: {model: {"prompt": int, "completion": int}}}
_session_usage: dict[str, dict[str, dict[str, int]]] = {}
_usage_lock = threading.Lock()

# Per-session turn start time: {session_id: float}
_turn_start: dict[str, float] = {}
_start_lock = threading.Lock()

# Per-session tool call counts: {session_id: {tool_name: count}}
_session_tools: dict[str, dict[str, int]] = {}
_tools_lock = threading.Lock()

# Per-session aux model call counts derived from tool map: {session_id: {model: count}}
_session_aux_models: dict[str, dict[str, int]] = {}
_aux_lock = threading.Lock()

# Per-session turn counter: {session_id: int} — never reset, accumulates for session lifetime
_session_turns: dict[str, int] = {}
_turns_lock = threading.Lock()

# Per-session cost accumulator: {session_id: float} — never reset, accumulates for session lifetime
_session_cost: dict[str, float] = {}
_session_cost_lock = threading.Lock()


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
        _session_usage[session_id] = {}
    with _tools_lock:
        _session_tools[session_id] = {}
    with _aux_lock:
        _session_aux_models[session_id] = {}
    with _turns_lock:
        _session_turns[session_id] = _session_turns.get(session_id, 0) + 1


def on_post_api_request(**kwargs: Any) -> None:
    """Accumulate token usage per model across all API calls in this turn."""
    session_id = kwargs.get("session_id", "") or ""
    usage = kwargs.get("usage") or {}
    if not usage:
        return
    model = kwargs.get("model", "") or "_unattributed"
    prompt = usage.get("prompt_tokens") or usage.get("input_tokens") or 0
    completion = usage.get("completion_tokens") or usage.get("output_tokens") or 0
    with _usage_lock:
        session_bucket = _session_usage.setdefault(session_id, {})
        model_bucket = session_bucket.setdefault(model, {"prompt": 0, "completion": 0})
        model_bucket["prompt"] += prompt
        model_bucket["completion"] += completion


def on_post_tool_call(**kwargs: Any) -> None:
    """Accumulate tool call counts; track aux model usage via tool→model config map."""
    session_id = kwargs.get("session_id", "") or ""
    tool_name = kwargs.get("tool_name", "") or ""
    if not tool_name:
        return

    with _tools_lock:
        bucket = _session_tools.setdefault(session_id, {})
        bucket[tool_name] = bucket.get(tool_name, 0) + 1

    cfg = _load_config()
    aux_tool_models: dict = cfg.get("aux_tool_models", {})
    backing_model = aux_tool_models.get(tool_name)
    if backing_model:
        with _aux_lock:
            aux_bucket = _session_aux_models.setdefault(session_id, {})
            aux_bucket[backing_model] = aux_bucket.get(backing_model, 0) + 1


_DEFAULT_ORDER = [
    "model", "provider", "latency",
    "tokens_direction", "tokens_total",
    "cost", "session_cost", "turns",
    "usage_pct", "reset", "balance",
]


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
    provider = kwargs.get("provider", "")

    icon       = cfg.get("icon", "⚡")
    agent_name = cfg.get("agent_name", "hermes")

    show_model            = cfg.get("show_model", True)
    show_provider         = cfg.get("show_provider", True)
    show_latency          = cfg.get("show_latency", True)
    show_tokens           = cfg.get("show_tokens", True)
    show_tokens_direction = cfg.get("show_tokens_direction", True)
    show_tokens_total     = cfg.get("show_tokens_total", True)
    show_cost             = cfg.get("show_cost", True)
    show_session_cost     = cfg.get("show_session_cost", True)
    show_turns            = cfg.get("show_turns", True)
    show_usage_pct        = cfg.get("show_usage_pct", False)
    show_reset            = cfg.get("show_reset", True)
    show_balance          = cfg.get("show_balance", True)
    show_tools            = cfg.get("show_tools", True)
    show_aux              = cfg.get("show_aux", True)

    order: list[str] = cfg.get("order", _DEFAULT_ORDER)
    custom_pricing = cfg.get("pricing")

    # Fall back to configured default when the framework doesn't pass a model name
    if not model:
        model = cfg.get("default_model", "")

    # ── Compute all field values upfront ────────────────────────────────────

    f: dict[str, str | None] = {k: None for k in _DEFAULT_ORDER}

    if show_model:
        f["model"] = model or None

    if show_provider:
        f["provider"] = provider or None

    if show_latency:
        with _start_lock:
            start = _turn_start.get(session_id)
        if start:
            elapsed = time.monotonic() - start
            f["latency"] = f"~{elapsed:.1f}s est."

    # Tokens + cost (primary model only — aux calls don't fire post_api_request)
    with _usage_lock:
        all_usage = _session_usage.pop(session_id, {})

    primary_usage = all_usage.pop(model, None) or all_usage.pop("_unattributed", None)

    if primary_usage:
        prompt_tok = primary_usage["prompt"]
        completion_tok = primary_usage["completion"]
        total_tok = prompt_tok + completion_tok

        if show_tokens and total_tok:
            if show_tokens_direction:
                f["tokens_direction"] = f"{prompt_tok:,}↑ {completion_tok:,}↓"
            if show_tokens_total:
                f["tokens_total"] = f"{total_tok:,} tok"

        if show_cost:
            cost = estimate_cost(model, prompt_tok, completion_tok, custom_pricing)
            if cost is not None:
                if cost == 0.0:
                    f["cost"] = "free"
                elif cost < 0.0001:
                    f["cost"] = "<$0.0001 trn"
                else:
                    f["cost"] = f"~${cost:.4f} trn"
                with _session_cost_lock:
                    _session_cost[session_id] = _session_cost.get(session_id, 0.0) + cost

    if show_session_cost:
        with _session_cost_lock:
            ses_cost = _session_cost.get(session_id, 0.0)
        if ses_cost > 0.0:
            f["session_cost"] = f"${ses_cost:.4f} ses"

    if show_turns:
        with _turns_lock:
            turn_count = _session_turns.get(session_id, 0)
        if turn_count:
            f["turns"] = f"{turn_count} turn" if turn_count == 1 else f"{turn_count} turns"

    if show_usage_pct:
        f["usage_pct"] = get_usage_label(provider)

    if show_reset:
        f["reset"] = get_reset_label(provider)

    if show_balance:
        f["balance"] = get_balance_label(provider)

    # Kick off background refresh so the NEXT call has fresh data
    refresh_in_background(provider, fetch_balance=show_balance)

    # ── Assemble primary line in configured order ────────────────────────────

    parts: list[str] = [f"{icon} {agent_name}"]
    for field in order:
        val = f.get(field)
        if val:
            parts.append(val)

    footer = "-# " + " · ".join(parts)

    # ── Extra lines (tools, aux) — order configurable via order list too ─────

    with _tools_lock:
        tools = _session_tools.pop(session_id, None)

    with _aux_lock:
        aux_models = _session_aux_models.pop(session_id, None)

    # Respect user-specified order for extra lines if present, else tools then aux
    extra_order = [f for f in order if f in ("tools", "aux")]
    if not extra_order:
        extra_order = ["tools", "aux"]

    for field in extra_order:
        if field == "tools" and show_tools and tools:
            tool_parts = [f"{n}×{c}" if c > 1 else n for n, c in tools.items()]
            footer += "\n-# 🔧 " + " · ".join(tool_parts)
        elif field == "aux" and show_aux and aux_models:
            aux_parts = [f"{m}×{c}" if c > 1 else m for m, c in aux_models.items()]
            footer += "\n-# 🔩 " + " · ".join(aux_parts)

    return response_text + "\n\n" + footer
