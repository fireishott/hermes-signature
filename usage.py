"""
Usage quota and balance fetching for hermes-signature.

Fetches reset times, usage percentages, and account balances from provider
APIs in a background thread after each response so the NEXT call shows data
at zero latency. First call shows nothing; second call onward shows live data.

Supported for quota (reset/usage):
    anthropic    — OAuth tokens only (Claude.ai login), not raw API keys
    openai-codex — Codex OAuth (hermes auth)
    openrouter   — OPENROUTER_API_KEY

Supported for balance:
    deepseek     — DEEPSEEK_API_KEY (https://api.deepseek.com/user/balance)
    openrouter   — OPENROUTER_API_KEY

Unsupported (no public usage/balance API): minimax, gemini, xai, grok, ollama/custom
"""

from __future__ import annotations

import os
import threading
from datetime import datetime, timezone
from typing import Optional

# Hermes provider name → account_usage provider key
_PROVIDER_MAP: dict[str, str] = {
    "anthropic":    "anthropic",
    "claude":       "anthropic",
    "openai-codex": "openai-codex",
    "codex":        "openai-codex",
    "openrouter":   "openrouter",
}

# Cache: usage_provider_key → (reset_at, used_percent)
_cache: dict[str, tuple[Optional[datetime], Optional[float]]] = {}
_cache_lock = threading.Lock()

# Balance cache: hermes_provider → float (USD)
_balance_cache: dict[str, float] = {}
_balance_lock = threading.Lock()


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
            for w in snap.windows:
                if w.reset_at and (reset_at is None or w.reset_at < reset_at):
                    reset_at = w.reset_at
            for w in snap.windows:
                if w.used_percent is not None:
                    if used_pct is None or w.used_percent > used_pct:
                        used_pct = w.used_percent
        with _cache_lock:
            _cache[usage_provider] = (reset_at, used_pct)
    except Exception:
        pass


def _load_env_key(key: str) -> str:
    """Read an API key from os.environ, falling back to ~/.hermes/.env."""
    val = os.environ.get(key, "")
    if val:
        return val
    from pathlib import Path
    env_path = Path.home() / ".hermes" / ".env"
    try:
        for line in env_path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line.startswith(f"{key}="):
                return line.split("=", 1)[1].strip().strip("\"'")
    except Exception:
        pass
    return ""


def _fetch_deepseek_balance() -> Optional[float]:
    try:
        import urllib.request
        import json
        api_key = _load_env_key("DEEPSEEK_API_KEY")
        if not api_key:
            return None
        req = urllib.request.Request(
            "https://api.deepseek.com/user/balance",
            headers={"Authorization": f"Bearer {api_key}", "Accept": "application/json"},
        )
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read())
        for info in data.get("balance_infos", []):
            if info.get("currency", "").upper() == "USD":
                return float(info.get("topped_up_balance", 0))
        return None
    except Exception:
        return None


def _fetch_openrouter_balance(api_key: Optional[str] = None) -> Optional[float]:
    try:
        import urllib.request
        import json
        key = api_key or _load_env_key("OPENROUTER_API_KEY")
        if not key:
            return None
        req = urllib.request.Request(
            "https://openrouter.ai/api/v1/credits",
            headers={"Authorization": f"Bearer {key}", "Accept": "application/json"},
        )
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read())
        total = data.get("data", {}).get("total_credits", None)
        used = data.get("data", {}).get("total_usage", None)
        if total is not None and used is not None:
            return max(0.0, float(total) - float(used))
        return None
    except Exception:
        return None


def _fetch_balance_and_cache(hermes_provider: str, api_key: Optional[str] = None) -> None:
    provider = (hermes_provider or "").lower().strip()
    balance: Optional[float] = None
    if provider == "deepseek":
        balance = _fetch_deepseek_balance()
    elif provider == "openrouter":
        balance = _fetch_openrouter_balance(api_key)
    if balance is not None:
        with _balance_lock:
            _balance_cache[provider] = balance


def refresh_in_background(
    hermes_provider: str,
    base_url: Optional[str] = None,
    api_key: Optional[str] = None,
    fetch_balance: bool = False,
) -> None:
    """Kick off background fetches for quota and optionally balance. Non-blocking."""
    usage_provider = _resolve_provider(hermes_provider)
    if usage_provider:
        threading.Thread(
            target=_fetch_and_cache,
            args=(usage_provider, base_url, api_key),
            daemon=True,
        ).start()
    if fetch_balance:
        threading.Thread(
            target=_fetch_balance_and_cache,
            args=(hermes_provider, api_key),
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


def get_balance_label(hermes_provider: str) -> Optional[str]:
    """Return '$99.48 bal' from cache, or None if not available."""
    provider = (hermes_provider or "").lower().strip()
    with _balance_lock:
        balance = _balance_cache.get(provider)
    if balance is None:
        return None
    return f"${balance:.2f} bal"
