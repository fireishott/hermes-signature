# Footer Format

## Structure

```
-# {icon} {agent_name} · {profile} · {model} · {provider} · ~{latency}s est. · {tokens} tok · ~${cost}
```

Fields are joined with ` · ` (space-middot-space). Any field that is disabled or unavailable is omitted — the separators contract automatically.

---

## Prefix

The footer is appended to the response with two newlines:

```
{response_text}

-# ⚡ hermes · default · deepseek-v4-pro · deepseek · ~1.4s est. · 1,847 tok · ~$0.0004
```

The `-#` prefix is a Discord markdown feature — it renders as small, dimmed subheading text. On other platforms it appears as literal `-#` followed by the content.

---

## Field Details

| Field | Example | Notes |
|---|---|---|
| icon + name | `⚡ hermes` | Always present when plugin is enabled |
| profile | `flynt` | Omitted if `show_profile: false` or when unavailable |
| model | `mimo-v2.5-pro` | Omitted if model name is empty |
| provider | `xiaomi` | Omitted if provider is empty |
| latency | `~1.4s est.` | Omitted if `pre_llm_call` wasn't recorded for this session |
| tokens | `1,247↑ 600↓ 1,847 tok` | input↑ completion↓ total. Omitted if total is zero |
| cost | `~$0.0004` | See cost rendering rules below |

### Cost Rendering

| Condition | Displayed |
|---|---|
| Model not in pricing table | field omitted |
| `input: 0.00, output: 0.00` | `free` |
| Cost > 0 but < $0.0001 | `<$0.0001` |
| Cost ≥ $0.0001 | `~$X.XXXX` (4 decimal places) |

---

## Platform Rendering

### Discord

Discord renders `-#` as small dimmed text (Discord "subtext" markdown). The footer appears visually de-emphasized below the main response — ideal for metadata that shouldn't dominate the message.

```
Here's your answer...

⚡ hermes · default · deepseek-v4-pro · deepseek · ~1.4s est. · 1,847 tok · ~$0.0004
↑ rendered small and grey
```

### BlueBubbles / iMessage

No special markdown rendering. The `-#` appears as a literal prefix:

```
Here's your answer...

-# ⚡ hermes · default · deepseek-v4-pro · deepseek · ~1.4s est. · 1,847 tok · ~$0.0004
```

Consider using `platforms: ["discord"]` if you only want the footer where it renders nicely, or customize the icon/format for other platforms.

### CLI

Same as BlueBubbles — plain text, `-#` is literal. Works fine as a visible footer.

---

## Examples by Field Combination

All fields on, with tools and aux model:
```
-# ⚡ hermes · default · deepseek-v4-pro · deepseek · ~1.4s est. · 1,247↑ 600↓ 1,847 tok · ~$0.0004 · 4 turns
-# 🔧 web_search×3 · vision_analyze×3
-# 🔩 gemini-2.5-flash-lite×3
```

All fields on, no aux:
```
-# ⚡ hermes · default · deepseek-v4-pro · deepseek · ~1.4s est. · 1,247↑ 600↓ 1,847 tok · ~$0.0004
```

No provider, no cost:
```
-# ⚡ hermes · default · deepseek-v4-pro · ~1.4s est. · 1,247↑ 600↓ 1,847 tok
```

Local model (free):
```
-# ⚡ hermes · default · qwen2.5:7b · custom · ~0.8s est. · 412↑ 100↓ 512 tok · free
```

Model not in pricing table:
```
-# ⚡ hermes · default · my-unknown-model · custom · ~1.1s est. · 240↑ 60↓ 300 tok
```

Tokens only:
```
-# ⚡ hermes · default · 1,247↑ 600↓ 1,847 tok
```
