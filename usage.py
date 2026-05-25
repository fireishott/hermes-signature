"""
Usage quota fetching for hermes-signature.

Fetches reset times and usage percentages from provider account APIs in a
background thread after each response so the NEXT call shows the countdown
at zero latency. First call shows nothing; second call onward shows live data.

Supported providers (via agent.account_usage):
    anthropic    — OAuth tokens only (Claude.ai login), not raw API keys
    openai-codex — Codex OAuth (hermes auth)
    openrouter   — OPENROUTER_API_KEY

Unsupported (no public usage API): minimax, gemini, xai, grok, ollama/custom
"""

from __future__ import annotations

import threading
from datetime import datetime, timezone
from typing import Optional

# Hermes provider name → account_usage provider key
_PROVIDER_MAP: dict[str, str] = {
    "anthropic":   "anthropic",
    "claude":      "anthropic",
    "openai-codex":"openai-codex",
    "codex":       "openai-codex",
    "openrouter":  "openrouter",
}

# Cache: usage_provider_key → (reset_at, used_percent)
_cache: dict[str, tuple[Optional[datetime], Optional[float]]] = {}
_cache_lock = threading.Lock()


def _resolve_provider(hermes_provider: str) -> Optional[str]:
    return _PROVIDER_MAP.get((hermes_provider or "").lower().strip())


def _fetch_and_cache(usage_provider: str, base_url: Optional[str] = None, api_key: Optional[str] = None) -> None:
    try:
        from agent.account_usage import fetch_account_usage
        snap = fetch_account_usage(usage_provider, base_url=base_url, api_key=api_key)
        if not snap or not snap.available:
            return
        reset_at: Optional[datetime] = None
        used_pct: Optional[float] = None
        if snap.windows:
            # Use the earliest reset_at (most pressing window)
            for w in snap.windows:
                if w.reset_at and (reset_at is None or w.reset_at < reset_at):
                    reset_at = w.reset_at
            # Use highest used_percent (most constrained window)
            for w in snap.windows:
                if w.used_percent is not None:
                    if used_pct is None or w.used_percent > used_pct:
                        used_pct = w.used_percent
        with _cache_lock:
            _cache[usage_provider] = (reset_at, used_pct)
    except Exception:
        pass


def refresh_in_background(hermes_provider: str, base_url: Optional[str] = None, api_key: Optional[str] = None) -> None:
    """Kick off a background fetch for the given hermes provider. Non-blocking."""
    usage_provider = _resolve_provider(hermes_provider)
    if not usage_provider:
        return
    threading.Thread(
        target=_fetch_and_cache,
        args=(usage_provider, base_url, api_key),
        daemon=True,
    ).start()


def get_reset_label(hermes_provider: str) -> Optional[str]:
    """Return 'resets in 4h 57m' from cache, or None if not available."""
    usage_provider = _resolve_provider(hermes_provider)
    if not usage_provider:
        return None
    with _cache_lock:
        entry = _cache.get(usage_provider)
    if not entry:
        return None
    reset_at, _ = entry
    if not reset_at:
        return None
    delta = int((reset_at - datetime.now(timezone.utc)).total_seconds())
    if delta <= 0:
        return None
    rh, rrem = divmod(delta, 3600)
    rm = rrem // 60
    if rh:
        return f"resets in {rh}h {rm}m"
    return f"resets in {rm}m"


def get_usage_label(hermes_provider: str) -> Optional[str]:
    """Return '42% used' from cache, or None if not available."""
    usage_provider = _resolve_provider(hermes_provider)
    if not usage_provider:
        return None
    with _cache_lock:
        entry = _cache.get(usage_provider)
    if not entry:
        return None
    _, used_pct = entry
    if used_pct is None:
        return None
    return f"{round(used_pct)}% used"
