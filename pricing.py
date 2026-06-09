"""
Model pricing table (USD per 1M tokens).
Override via config.yaml:

    signature:
      pricing:
        mimo-v2.5-pro:
          input: 0.435
          output: 0.870
          cache: 0.0036
"""

from __future__ import annotations

# Format: "model-name": {"input": $/1M, "output": $/1M, "cache": $/1M (optional)}
# "cache" = cost per 1M cached input tokens. Models without it fall back to "input" rate.
PRICING: dict[str, dict[str, float]] = {
    # Xiaomi MiMo (v2.5 series — permanent pricing as of May 27, 2026)
    "mimo-v2.5-pro":        {"input": 0.435,  "output": 0.870,  "cache": 0.0036},
    "mimo-v2.5":            {"input": 0.14,   "output": 0.28,   "cache": 0.0028},
    "mimo-v2-flash":        {"input": 0.10,   "output": 0.30,   "cache": 0.01},
    "mimo-v2-pro":          {"input": 1.00,   "output": 3.00},
    # MiniMax (legacy — demoted to fallback)
    "MiniMax-M2.7":         {"input": 0.30,   "output": 1.10},
    "MiniMax-Text-01":      {"input": 0.20,   "output": 0.80},
    # DeepSeek
    "deepseek-v4-pro":      {"input": 0.50,   "output": 2.00},
    "deepseek-v4-flash":    {"input": 0.10,   "output": 0.40},
    # Gemini
    "gemini-2.5-flash":     {"input": 0.15,   "output": 0.60},
    "gemini-2.5-flash-lite":{"input": 0.075,  "output": 0.30},
    "gemini-2.5-pro":       {"input": 1.25,   "output": 10.00},
    # Anthropic
    "claude-opus-4-7":      {"input": 15.00,  "output": 75.00},
    "claude-sonnet-4-6":    {"input": 3.00,   "output": 15.00},
    "claude-haiku-4-5":     {"input": 0.80,   "output": 4.00},
    # OpenAI
    "gpt-4o":               {"input": 2.50,   "output": 10.00},
    "gpt-4o-mini":          {"input": 0.15,   "output": 0.60},
    # Ollama / local
    "qwen2.5:7b":           {"input": 0.00,   "output": 0.00},
    "qwen2.5:3b":           {"input": 0.00,   "output": 0.00},
}


def _resolve_rates(model: str, custom_pricing: dict | None = None) -> dict | None:
    """Look up pricing for a model. Exact match first, then prefix match."""
    table = {**PRICING, **(custom_pricing or {})}
    rates = table.get(model)
    if not rates:
        for key in table:
            if model.lower().startswith(key.lower()) or key.lower().startswith(model.lower()):
                rates = table[key]
                break
    return rates


def estimate_cost(
    model: str,
    prompt_tokens: int,
    completion_tokens: int,
    custom_pricing: dict | None = None,
    cached_tokens: int = 0,
) -> float | None:
    """Estimate turn cost. Splits cached input tokens at the cache rate when available."""
    rates = _resolve_rates(model, custom_pricing)
    if not rates:
        return None
    input_rate = rates["input"]
    output_rate = rates["output"]
    cache_rate = rates.get("cache", input_rate)  # fall back to input rate if no cache rate
    non_cached_prompt = max(0, prompt_tokens - cached_tokens)
    cost = (non_cached_prompt / 1_000_000 * input_rate) + \
           (cached_tokens / 1_000_000 * cache_rate) + \
           (completion_tokens / 1_000_000 * output_rate)
    return cost
