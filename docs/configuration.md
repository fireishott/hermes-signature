# Configuration Reference

All configuration lives under the `signature:` key in `~/.hermes/config.yaml`.

---

## Full Schema

```yaml
signature:
  enabled: true             # Master switch. false = plugin is silent.
  agent_name: "hermes"      # Label shown at the start of every footer.
  icon: "⚡"                # Leading character(s). Any emoji or text.

  show_model: true          # Include model name in footer.
  show_provider: true       # Include provider name in footer.
  show_latency: true        # Include ~Xs est. latency.
  show_tokens: true         # Include total token count.
  show_cost: true           # Include estimated cost.

  platforms: []             # Restrict footer to these platforms.
                            # Empty list = all platforms.
                            # e.g. ["discord", "bluebubbles"]

  pricing:                  # Per-model price overrides (USD per 1M tokens).
    MyModel:
      input: 1.00
      output: 4.00
```

---

## Fields

### `enabled`
**Type:** `bool` | **Default:** `true`

Master on/off switch. When `false`, the plugin registers its hooks but returns `None` from `transform_llm_output`, leaving responses unmodified.

---

### `agent_name`
**Type:** `string` | **Default:** `"hermes"`

The label displayed after the icon at the start of the footer. Change this to match your agent's name or persona.

```
-# ⚡ myagent · gpt-4o · openai · ~1.2s est. · 842 tok · ~$0.0023
          ───────
          this part
```

---

### `icon`
**Type:** `string` | **Default:** `"⚡"`

Any string placed before `agent_name`. Typically a single emoji, but can be any character sequence.

---

### `show_model`
**Type:** `bool` | **Default:** `true`

Includes the model name (e.g. `MiniMax-M2.7`, `claude-sonnet-4-6`) in the footer. The model name comes from Hermes's `model` kwarg passed to `transform_llm_output`.

---

### `show_provider`
**Type:** `bool` | **Default:** `true`

Includes the provider name (e.g. `minimax`, `anthropic`, `openai`) if available.

---

### `show_latency`
**Type:** `bool` | **Default:** `true`

Includes estimated turn latency, measured from `pre_llm_call` entry to `transform_llm_output` exit. Always labelled `est.` because it includes Hermes processing overhead, not just API time.

Format: `~1.4s est.`

---

### `show_tokens`
**Type:** `bool` | **Default:** `true`

Includes total tokens for the turn (prompt + completion, summed across all API calls including tool call rounds).

Format: `1,247↑ 600↓ 1,847 tok` (input↑ completion↓ total)

---

### `show_cost`
**Type:** `bool` | **Default:** `true`

Includes cost estimate based on the built-in pricing table (or your overrides). See [pricing.md](pricing.md) for the full table.

- If the model is in the pricing table with `0.00` rates: shows `free`
- If cost is non-zero but below `$0.0001`: shows `<$0.0001`
- Otherwise: shows `~$X.XXXX`
- If model is not in the pricing table: cost field is omitted

---

### `platforms`
**Type:** `list[string]` | **Default:** `[]` (all platforms)

When non-empty, the footer is only added if the current platform matches one of the listed values. Platform names are lowercase strings as reported by Hermes (e.g. `"discord"`, `"bluebubbles"`, `"cli"`).

```yaml
platforms: ["discord", "bluebubbles"]   # footer only on these two
platforms: []                            # footer on every platform
```

---

### `pricing`
**Type:** `dict` | **Default:** `{}` (use built-in table)

Override pricing for specific models. Keys are model names (case-insensitive prefix matching is used). Values have `input` and `output` fields in USD per 1 million tokens.

```yaml
pricing:
  MiniMax-M2.7:
    input: 0.30
    output: 1.10
  my-fine-tune:
    input: 2.00
    output: 8.00
```

Overrides are merged with the built-in table. Your overrides take precedence.

To mark a model as free (local/self-hosted):
```yaml
pricing:
  my-local-model:
    input: 0.00
    output: 0.00
```

---

## Minimal Config

```yaml
signature:
  enabled: true
  agent_name: "hermes"
```

Everything else defaults to `true` / empty.

---

## Disabling Individual Fields

```yaml
signature:
  enabled: true
  agent_name: "bot"
  icon: "·"
  show_model: true
  show_provider: false   # hide provider
  show_latency: false    # hide latency
  show_tokens: true
  show_cost: false       # hide cost
```

Result:
```
-# · bot · gpt-4o · 1,024 tok
```
