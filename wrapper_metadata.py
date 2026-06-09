from __future__ import annotations

import hashlib
import json
import urllib.parse
import urllib.request
from typing import Any, Optional


def response_text_sha256(response_text: str) -> str:
    return hashlib.sha256((response_text or "").encode("utf-8")).hexdigest()


def fetch_wrapper_turn_metadata(
    base_url: str,
    *,
    model: str,
    response_text: str,
    timeout_ms: int = 150,
) -> Optional[dict[str, Any]]:
    if not base_url or not response_text:
        return None

    query = urllib.parse.urlencode(
        {
            "model": model or "",
            "response_sha256": response_text_sha256(response_text),
        }
    )
    url = f"{base_url.rstrip('/')}/v1/turn-metadata/latest?{query}"
    request = urllib.request.Request(url, headers={"Accept": "application/json"})

    try:
        with urllib.request.urlopen(request, timeout=max(timeout_ms, 1) / 1000.0) as response:
            data = json.loads(response.read().decode("utf-8"))
    except Exception:
        return None

    if not isinstance(data, dict):
        return None
    if data.get("response_text_sha256") != response_text_sha256(response_text):
        return None
    return data
