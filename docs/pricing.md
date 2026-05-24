# Pricing Table

Built-in rates used to estimate cost. All prices are USD per 1 million tokens.

Override any entry or add new models in `config.yaml`. See [configuration.md](configuration.md#pricing).

---

## Built-in Rates

| Model | Input ($/1M) | Output ($/1M) |
|---|---|---|
| **MiniMax** | | |
| `MiniMax-M2.7` | $0.30 | $1.10 |
| `MiniMax-Text-01` | $0.20 | $0.80 |
| **Gemini** | | |
| `gemini-2.5-flash` | $0.15 | $0.60 |
| `gemini-2.5-flash-lite` | $0.075 | $0.30 |
| `gemini-2.5-pro` | $1.25 | $10.00 |
| **Anthropic** | | |
| `claude-opus-4-7` | $15.00 | $75.00 |
| `claude-sonnet-4-6` | $3.00 | $15.00 |
| `claude-haiku-4-5` | $0.80 | $4.00 |
| **OpenAI** | | |
| `gpt-4o` | $2.50 | $10.00 |
| `gpt-4o-mini` | $0.15 | $0.60 |
| **Ollama / Local** | | |
| `qwen2.5:7b` | free | free |
| `qwen2.5:3b` | free | free |

---

## Model Matching

The lookup uses exact match first, then case-insensitive prefix matching in either direction. This means:

- `claude-sonnet-4-6-20251001` → matches `claude-sonnet-4-6` (prefix)
- `gemini-2.5-flash-exp` → matches `gemini-2.5-flash` (prefix)
- `MiniMax-M2` → matches `MiniMax-M2.7` (suffix direction)

If no match is found, the cost field is omitted from the footer.

---

## Adding Overrides

```yaml
signature:
  pricing:
    my-model:
      input: 1.00
      output: 4.00
    another-model:
      input: 0.00
      output: 0.00    # marks as free
```

Overrides are merged on top of the built-in table. Hermes gateway restart is not required — config is re-read on every turn.

---

## Accuracy

These are estimates. Actual costs may differ due to:
- Provider-specific token counting differences
- Batch vs. real-time pricing tiers
- Caching discounts (e.g. Anthropic prompt cache)
- Pricing changes after this table was last updated

Always verify against your provider's billing dashboard for accurate spend tracking.
