# Pricing Table

Built-in rates used to estimate cost. All prices are USD per 1 million tokens.

Override any entry or add new models in `config.yaml`. See [configuration.md](configuration.md#pricing).

---

## Built-in Rates

| Model | Input ($/1M) | Output ($/1M) | Cache ($/1M) |
|---|---|---|---|
| **Xiaomi MiMo** | | | |
| `mimo-v2.5-pro` | $0.435 | $0.870 | $0.0036 |
| `mimo-v2.5` | $0.14 | $0.28 | $0.0028 |
| `mimo-v2-flash` | $0.10 | $0.30 | $0.01 |
| `mimo-v2-pro` | $1.00 | $3.00 | — |
| **DeepSeek** | | | |
| `deepseek-v4-pro` | $0.50 | $2.00 | — |
| `deepseek-v4-flash` | $0.10 | $0.40 | — |
| **MiniMax** (legacy) | | | |
| `MiniMax-M2.7` | $0.30 | $1.10 | — |
| `MiniMax-Text-01` | $0.20 | $0.80 | — |
| **Gemini** | | |
| `gemini-2.5-flash` | $0.15 | $0.60 | — |
| `gemini-2.5-flash-lite` | $0.075 | $0.30 | — |
| `gemini-2.5-pro` | $1.25 | $10.00 | — |
| **Anthropic** | | | |
| `claude-opus-4-7` | $15.00 | $75.00 | — |
| `claude-sonnet-4-6` | $3.00 | $15.00 | — |
| `gemini-2.5-pro` | $1.25 | $10.00 | — |
| **OpenAI** | | | |
| `gpt-5.5` | $5.00 | $30.00 | $0.50 |
| `gpt-4o` | $2.50 | $10.00 | — |
| `gpt-4o-mini` | $0.15 | $0.60 | — |
| **Ollama / Local** | | | |
| `qwen2.5:7b` | free | free | — |
| `qwen2.5:3b` | free | free | — |

---

## Model Matching

The lookup uses exact match first, then case-insensitive prefix matching in either direction. This means:

- `claude-sonnet-4-6-20251001` → matches `claude-sonnet-4-6` (prefix)
- `gemini-2.5-flash-exp` → matches `gemini-2.5-flash` (prefix)
- `MiniMax-M2` → matches `MiniMax-M2.7` (suffix direction)

If no match is found, the cost field is omitted from the footer.

---

## Cached Token Pricing

When a model reports cached input tokens (via `prompt_tokens_details.cached_tokens` in the API response), the cost calculation splits them out:

```
cost = (non_cached_input / 1M × input_rate) + (cached_input / 1M × cache_rate) + (output / 1M × output_rate)
```

Cache rates are significantly cheaper than regular input — MiMo v2.5 Pro's cache rate is **$0.0036/1M** vs **$0.435/1M** for regular input (a ~99% discount). Models without a `cache` rate in the table fall back to the regular `input` rate.

The footer shows cached token count when > 0: `1,200 cached`. This appears between the token total and cost fields by default.

---

## Adding Overrides

```yaml
signature:
  pricing:
    mimo-v2.5-pro:
      input: 0.435
      output: 0.870
      cache: 0.0036
    another-model:
      input: 0.00
      output: 0.00    # marks as free
```

Overrides are merged on top of the built-in table. Hermes gateway restart is not required — config is re-read on every turn.

---

## MiMo Token Plan (Subscription)

Xiaomi offers a unified Credits subscription system with four tiers. One subscription covers multiple coding tools (OpenCode, Claude Code, Cline, etc.).

### Annual Plans (12% off vs. monthly)

| Tier | Annual Price (USD) | Annual Credits | Notes |
|---|---|---|---|
| **Lite** | $63.36 | 720M | Personal / light use |
| **Standard** | $168.96 | 2,400M | Regular daily coding |
| **Pro** | $528.00 | 8,400M | Heavy daily use |
| **Max** | $1,056.00 | 19,200M | Core infrastructure |

**Credit consumption rates:**
- `mimo-v2.5` / `mimo-v2-flash` — **1x** (1 token = 1 credit)
- `mimo-v2.5-pro` / `mimo-v2-pro` — **2x** (1 token = 2 credits)
- **TTS models** (`mimo-v2.5-tts`, `mimo-v2-tts-voiceclone`, `mimo-v2-tts-voicedesign`, `mimo-v2-tts`) — **0x** (free for a limited time)

**Key policies:**
- Token Plan uses `tp-xxxxx` format API keys (distinct from pay-as-you-go `sk-xxxxx` keys)
- No 5-hour quota cap — supports concentrated heavy tasks
- **Off-peak discount:** usage during 9:00 AM – 5:00 PM PDT (00:00–08:00 Beijing Time) gets a **0.8x** coefficient — **20% off** credit consumption
- Downgrades not supported; upgrades pay the difference
- First purchase: 12% off (once per account)
- Refunds not supported; unused credits are not refunded

> **Note:** Token Plan quota is limited to configured coding tools. Not for automated scripts or custom backends in non-coding scenarios.

---

## Accuracy

These are estimates. Actual costs may differ due to:
- Provider-specific token counting differences
- Batch vs. real-time pricing tiers
- Caching discounts (e.g. Anthropic prompt cache)
- Pricing changes after this table was last updated

Always verify against your provider's billing dashboard for accurate spend tracking.
