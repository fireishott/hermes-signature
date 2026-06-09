# Examples

## Default Configuration

Config:
```yaml
signature:
  enabled: true
  agent_name: "hermes"
  icon: "⚡"
```

Footer:
```
-# ⚡ hermes · mimo-v2.5-pro · xiaomi · ~1.4s est. · 1,247↑ 600↓ 1,847 tok · ~$0.0006
```

---

## High Token Turn (Tool Chain)

A turn that made 3 tool calls before responding — tokens accumulate across all rounds:

```
-# ⚡ hermes · mimo-v2.5-pro · xiaomi · ~4.2s est. · 6,841↑ 1,500↓ 8,341 tok · ~$0.0043
```

---

## Gemini (Vision / Aux Model)

```
-# ⚡ hermes · gemini-2.5-flash-lite · gemini · ~0.9s est. · 510↑ 113↓ 623 tok · ~$0.0001
```

---

## Local Model (Free)

Using qwen2.5:7b on Ollama:
```
-# ⚡ hermes · qwen2.5:7b · custom · ~2.1s est. · 412↑ 100↓ 512 tok · free
```

---

## Claude

```
-# ⚡ hermes · claude-sonnet-4-6 · anthropic · ~2.3s est. · 882↑ 220↓ 1,102 tok · ~$0.0195
```

---

## OpenAI

```
-# ⚡ hermes · gpt-4o · openai · ~1.8s est. · 760↑ 180↓ 940 tok · ~$0.0118
```

---

## Very Cheap Turn

When cost rounds below $0.0001:
```
-# ⚡ hermes · gemini-2.5-flash-lite · gemini · ~0.6s est. · 72↑ 16↓ 88 tok · <$0.0001
```

---

## Unknown Model (No Cost)

If the model isn't in the pricing table and no override is set, cost is omitted:
```
-# ⚡ hermes · my-fine-tune · custom · ~1.3s est. · 580↑ 120↓ 700 tok
```

---

## Discord-Only Footer

Config with platform filter:
```yaml
signature:
  enabled: true
  agent_name: "hermes"
  platforms: ["discord"]
```

On Discord — footer appended. On BlueBubbles / CLI — no footer.

---

## Minimal Footer (Name + Tokens Only)

Config:
```yaml
signature:
  enabled: true
  agent_name: "bot"
  icon: "·"
  show_model: false
  show_provider: false
  show_latency: false
  show_tokens: true
  show_cost: false
```

Footer:
```
-# · bot · 1,247↑ 600↓ 1,847 tok
```

---

## Custom Agent Name and Icon

Config:
```yaml
signature:
  enabled: true
  agent_name: "aria"
  icon: "🔮"
```

Footer:
```
-# 🔮 aria · claude-opus-4-7 · anthropic · ~3.1s est. · 1,621↑ 420↓ 2,041 tok · ~$0.1836
```

---

## Cost Override for Custom Model

Config:
```yaml
signature:
  pricing:
    my-fine-tune:
      input: 2.00
      output: 8.00
```

Footer with that model:
```
-# ⚡ hermes · my-fine-tune · custom · ~1.5s est. · 780↑ 170↓ 950 tok · ~$0.0046
```
