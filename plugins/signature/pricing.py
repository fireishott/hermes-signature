"""
Model pricing table (USD per 1M tokens).
Override via config.yaml:

    signature:
      pricing:
        MiniMax-M2.7:
          input: 0.30
          output: 1.10
"""

from __future__ import annotations

# Format: "model-name": {"input": $/1M, "output": $/1M}
PRICING: dict[str, dict[str, float]] = {
    # MiniMax
    "MiniMax-M2.7":         {"input": 0.30,   "output": 1.10},
    "MiniMax-Text-01":      {"input": 0.20,   "output": 0.80},
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


def estimate_cost(
    model: str,
    prompt_tokens: int,
    completion_tokens: int,
    custom_pricing: dict | None = None,
) -> float | None:
    table = {**PRICING, **(custom_pricing or {})}
    # Try exact match, then prefix match
    rates = table.get(model)
    if not rates:
        for key in table:
            if model.lower().startswith(key.lower()) or key.lower().startswith(model.lower()):
                rates = table[key]
                break
    if not rates:
        return None
    cost = (prompt_tokens / 1_000_000 * rates["input"]) + \
           (completion_tokens / 1_000_000 * rates["output"])
    return cost
