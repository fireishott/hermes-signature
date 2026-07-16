"""
hermes-signature — appends a configurable signature footer to every LLM response.

Footer example:
    -# 🔥 default · deepseek-v4-pro · deepseek · ~1.2s est. · 1,247↑ 600↓ 1,847 tok · ~$0.0004 trn · 12 turns
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
      icon: "🔥"                     # emoji for this profile
      default_model: "mimo-v2.5-pro"  # fallback when model not in hook kwargs
      show_model: true
      show_provider: true
      show_latency: true
      show_tokens: true           # master toggle for token display
      show_tokens_direction: true # show input↑ / output↓ counts separately
      show_tokens_total: true     # show combined total token count
      show_cached: true           # show cached token count (e.g., "500 cached")
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
        - cached
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
        mimo-v2.5-pro:
          input: 0.435
          output: 0.870
"""

from __future__ import annotations

import threading
import time
from typing import Any

from .pricing import estimate_cost
from .usage import get_balance_label, get_reset_label, get_usage_label, refresh_in_background
from .wrapper_metadata import fetch_wrapper_turn_metadata

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


def _profile_exists(name: str) -> bool:
    """Return True when *name* is a real local Hermes profile."""
    clean = (name or "").strip()
    if not clean or clean in {"default", "custom"}:
        return clean == "default"
    try:
        from hermes_cli.profiles import get_profile_dir
        return get_profile_dir(clean).exists()
    except Exception:
        return False


def _profile_from_home_path(home: Any) -> str | None:
    """Infer a profile name from a Hermes home path."""
    try:
        from pathlib import Path

        resolved = Path(str(home)).expanduser().resolve()
        parts = resolved.parts
        if len(parts) >= 2 and parts[-2] == "profiles" and parts[-1]:
            return parts[-1]
        if resolved.name == ".hermes":
            return "default"
    except Exception:
        return None
    return None


def _valid_profile_label(value: Any) -> str | None:
    """Normalize and validate a candidate profile label.

    Desktop/API layers may advertise a model alias like ``hermes``. Do not let
    that leak into the footer unless it is an actual profile directory.
    """
    label = str(value or "").strip()
    if not label:
        return None
    if label in {"custom"}:
        return None
    if label == "default":
        return label
    return label if _profile_exists(label) else None


def _get_active_profile(cfg: dict | None = None, **kwargs: Any) -> str:
    """Return the live Hermes profile name, or 'default'.

    Priority:
    1. Hermes profile resolver / HERMES_HOME path inference (source of truth)
    2. explicit runtime hook kwargs, but only if they name a real profile
    3. legacy signature.profile_name/profile config overrides

    Why this order: some Desktop/API/runtime layers surface non-profile identity
    labels like ``hermes``. Those are useful elsewhere, but the footer should
    display the actual active profile backing the current process.
    """
    cfg = cfg or {}

    try:
        from hermes_cli.profiles import get_active_profile_name
        label = _valid_profile_label(get_active_profile_name())
        if label:
            return label
    except Exception:
        pass

    try:
        from hermes_constants import get_hermes_home
        label = _valid_profile_label(_profile_from_home_path(get_hermes_home()))
        if label:
            return label
    except Exception:
        pass

    try:
        import os
        label = _valid_profile_label(_profile_from_home_path(os.environ.get("HERMES_HOME")))
        if label:
            return label
    except Exception:
        pass

    for key in ("active_profile", "profile_name", "profile", "agent_identity"):
        label = _valid_profile_label(kwargs.get(key))
        if label:
            return label

    for key in ("active_profile", "profile_name", "profile"):
        label = _valid_profile_label(cfg.get(key))
        if label:
            return label

    return "default"


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
    # Extract cached tokens from OpenAI-compatible usage detail
    cached = 0
    details = usage.get("prompt_tokens_details") or {}
    if isinstance(details, dict):
        cached = int(details.get("cached_tokens") or 0)
    with _usage_lock:
        session_bucket = _session_usage.setdefault(session_id, {})
        model_bucket = session_bucket.setdefault(model, {"prompt": 0, "completion": 0, "cached": 0})
        model_bucket["prompt"] += prompt
        model_bucket["completion"] += completion
        model_bucket["cached"] += cached


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
    "profile", "model", "provider", "latency",
    "tokens_direction", "tokens_total", "cached",
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
    hook_model = kwargs.get("model", "") or ""
    hook_provider = kwargs.get("provider", "")
    model = hook_model
    provider = hook_provider

    active_profile = _get_active_profile(cfg, **kwargs)

    icon = cfg.get("icon", "⚡")

    show_profile          = cfg.get("show_profile", True)
    show_model            = cfg.get("show_model", True)
    show_provider         = cfg.get("show_provider", True)
    show_latency          = cfg.get("show_latency", True)
    show_tokens           = cfg.get("show_tokens", True)
    show_tokens_direction = cfg.get("show_tokens_direction", True)
    show_tokens_total     = cfg.get("show_tokens_total", True)
    show_cached           = cfg.get("show_cached", True)
    show_cost             = cfg.get("show_cost", True)
    show_session_cost     = cfg.get("show_session_cost", True)
    show_turns            = cfg.get("show_turns", True)
    show_usage_pct        = cfg.get("show_usage_pct", False)
    show_reset            = cfg.get("show_reset", True)
    show_balance          = cfg.get("show_balance", True)
    show_tools            = cfg.get("show_tools", True)
    show_aux              = cfg.get("show_aux", True)
    footer_format         = cfg.get("footer_format", "discord")  # "discord" (-#) or "standard" (--- separator)

    order: list[str] = cfg.get("order", _DEFAULT_ORDER)
    custom_pricing = cfg.get("pricing")
    wrapper_cfg: dict[str, Any] = cfg.get("wrapper_metadata", {}) or {}
    wrapper_enabled = wrapper_cfg.get("enabled", False)
    wrapper_base_url = str(wrapper_cfg.get("base_url", "http://127.0.0.1:8767")).strip()
    wrapper_timeout_ms = int(wrapper_cfg.get("timeout_ms", 150) or 150)
    wrapper_meta = None
    if wrapper_enabled and wrapper_base_url:
        wrapper_meta = fetch_wrapper_turn_metadata(
            wrapper_base_url,
            model=hook_model or cfg.get("default_model", ""),
            response_text=response_text,
            timeout_ms=wrapper_timeout_ms,
        )

    # Fall back to configured defaults when the framework doesn't pass model/provider
    if wrapper_meta:
        model = str(wrapper_meta.get("display_model") or wrapper_meta.get("upstream_model") or model or "")
        provider = str(wrapper_meta.get("upstream_provider") or provider or "")
    if not model:
        model = cfg.get("default_model", "")
    if not provider:
        provider = cfg.get("default_provider", "")

    # ── Compute all field values upfront ────────────────────────────────────

    f: dict[str, str | None] = {k: None for k in _DEFAULT_ORDER}

    if show_profile:
        f["profile"] = active_profile or None

    if show_model:
        f["model"] = model or None

    if show_provider:
        f["provider"] = provider or None

    if show_latency:
        latency_ms = wrapper_meta.get("latency_ms") if wrapper_meta else None
        if latency_ms:
            f["latency"] = f"~{(float(latency_ms) / 1000):.1f}s est."
        else:
            with _start_lock:
                start = _turn_start.get(session_id)
            if start:
                elapsed = time.monotonic() - start
                f["latency"] = f"~{elapsed:.1f}s est."

    # Tokens + cost (primary model only — aux calls don't fire post_api_request)
    with _usage_lock:
        all_usage = _session_usage.pop(session_id, {})

    primary_usage = all_usage.pop(model, None) or all_usage.pop("_unattributed", None)
    wrapper_prompt_tok = int(wrapper_meta.get("prompt_tokens", 0) or 0) if wrapper_meta else 0
    wrapper_completion_tok = int(wrapper_meta.get("completion_tokens", 0) or 0) if wrapper_meta else 0
    wrapper_total_tok = int(wrapper_meta.get("total_tokens", 0) or 0) if wrapper_meta else 0
    turn_cost_usd = None
    if wrapper_meta and wrapper_meta.get("total_cost_usd") is not None:
        turn_cost_usd = float(wrapper_meta["total_cost_usd"])

    if wrapper_total_tok or primary_usage:
        prompt_tok = wrapper_prompt_tok
        completion_tok = wrapper_completion_tok
        total_tok = wrapper_total_tok
        cached_tok = 0
        if not total_tok and primary_usage:
            prompt_tok = primary_usage["prompt"]
            completion_tok = primary_usage["completion"]
            total_tok = prompt_tok + completion_tok
            cached_tok = primary_usage.get("cached", 0)

        if show_tokens and total_tok:
            if show_tokens_direction:
                f["tokens_direction"] = f"{prompt_tok:,}↑ {completion_tok:,}↓"
            if show_tokens_total:
                f["tokens_total"] = f"{total_tok:,} tok"

        if show_cached and cached_tok:
            f["cached"] = f"{cached_tok:,} cached"

        if show_cost:
            cost = turn_cost_usd
            if cost is None:
                cost = estimate_cost(model, prompt_tok, completion_tok, custom_pricing, cached_tokens=cached_tok)
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
        f["usage_pct"] = get_usage_label(provider, active_profile)

    if show_reset:
        f["reset"] = get_reset_label(provider, active_profile)

    if show_balance:
        f["balance"] = get_balance_label(provider, active_profile)

    # Kick off background refresh so the NEXT call has fresh data
    refresh_in_background(provider, fetch_balance=show_balance, profile=active_profile)

    # ── Assemble primary line in configured order ────────────────────────────

    parts: list[str] = [f"{icon}"]
    for field in order:
        val = f.get(field)
        if val:
            parts.append(val)

    # footer_format: "discord" uses -# prefix (Slack/Discord small-text syntax)
    #                "standard" uses --- separator (renders in any markdown renderer)
    is_standard = footer_format == "standard"
    line_prefix = "" if is_standard else "-# "
    sep = "\n\n---\n" if is_standard else "\n\n"

    footer = line_prefix + " · ".join(parts)

    # ── Extra lines (tools, aux) — order configurable via order list too ─────

    with _tools_lock:
        tools = _session_tools.pop(session_id, None)

    with _aux_lock:
        aux_models = _session_aux_models.pop(session_id, None)

    if wrapper_meta and wrapper_meta.get("tool_counts"):
        wrapper_tools = {
            str(name): int(count)
            for name, count in (wrapper_meta.get("tool_counts") or {}).items()
            if name and count
        }
        if wrapper_tools:
            tools = wrapper_tools
            aux_map: dict[str, str] = cfg.get("aux_tool_models", {})
            derived_aux: dict[str, int] = {}
            for tool_name, count in wrapper_tools.items():
                backing_model = aux_map.get(tool_name)
                if backing_model:
                    derived_aux[backing_model] = derived_aux.get(backing_model, 0) + count
            if derived_aux:
                aux_models = derived_aux

    # Respect user-specified order for extra lines if present, else tools then aux
    extra_order = [f for f in order if f in ("tools", "aux")]
    if not extra_order:
        extra_order = ["tools", "aux"]

    for field in extra_order:
        if field == "tools" and show_tools and tools:
            tool_parts = [
                f"{name}×{count}" if count > 1 else name
                for name, count in sorted(tools.items(), key=lambda item: (-item[1], item[0].lower()))
            ]
            footer += "\n" + line_prefix + "🔧 " + " · ".join(tool_parts)
        elif field == "aux" and show_aux and aux_models:
            aux_parts = [
                f"{name}×{count}" if count > 1 else name
                for name, count in sorted(aux_models.items(), key=lambda item: (-item[1], item[0].lower()))
            ]
            footer += "\n" + line_prefix + "🔩 " + " · ".join(aux_parts)

    return response_text + sep + footer
