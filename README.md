# hermes-signature

![Version](https://img.shields.io/badge/version-0.1.0-blue?style=flat-square)
![Python](https://img.shields.io/badge/python-3.11%2B-3776AB?style=flat-square&logo=python&logoColor=white)
![Hermes](https://img.shields.io/badge/hermes--agent-compatible-gold?style=flat-square)
![License](https://img.shields.io/badge/license-MIT-green?style=flat-square)
![Platform](https://img.shields.io/badge/platform-macOS%20%7C%20Linux-lightgrey?style=flat-square)

A lightweight [Hermes Agent](https://github.com/NousResearch/hermes-agent) plugin that appends a signature footer to every LLM response — showing model, provider, estimated latency, token usage, and cost.

```
-# ⚡ hermes · MiniMax-M2.7 · minimax · ~1.4s est. · 1,247↑ 600↓ 1,847 tok · ~$0.0004
```

No patching of Hermes core. Survives `hermes update`. Pure plugin via the native `transform_llm_output` hook.

---

## Features

- **Model & provider** — shows exactly what handled the turn
- **Estimated latency** — measured from `pre_llm_call` hook entry, clearly labelled `est.`
- **Token usage** — accumulated across all API calls in the turn (including tool calls)
- **Cost estimate** — computed from a built-in pricing table, overridable per model
- **Platform filtering** — show footer only on specific platforms (Discord, BlueBubbles, etc.)
- **Fully configurable** — icon, agent name, show/hide each field individually
- **Local models = free** — Ollama/local models show `free` instead of a cost

---

## Install

```bash
git clone https://github.com/fih/hermes-signature
cd hermes-signature
chmod +x install.sh
./install.sh
hermes gateway restart
```

The installer copies the plugin into `~/.hermes/hermes-agent/plugins/` and appends a starter config block to `~/.hermes/config.yaml`.

---

## Configuration

```yaml
signature:
  enabled: true
  agent_name: "hermes"     # Label shown at the start of the footer
  icon: "⚡"               # Leading icon/emoji
  show_model: true          # Include model name
  show_provider: true       # Include provider name
  show_latency: true        # Include ~Xs est. latency
  show_tokens: true         # Include total token count
  show_cost: true           # Include estimated cost
  platforms: []             # Restrict to platforms; empty = all
                            # e.g. ["discord", "bluebubbles"]
  pricing:                  # Optional per-model price overrides (USD/1M tokens)
    MiniMax-M2.7:
      input: 0.30
      output: 1.10
```

See [docs/configuration.md](docs/configuration.md) for the full reference.

---

## Footer Format

```
-# {icon} {agent_name} · {model} · {provider} · ~{latency}s est. · {input}↑ {output}↓ {total} tok · ~${cost}
```

The `-#` prefix renders as small dimmed text in Discord. Each field is optional and can be toggled independently.

See [docs/footer-format.md](docs/footer-format.md) for format details and platform rendering notes.

---

## Examples

See [docs/examples.md](docs/examples.md) for example footers across different configurations and platforms.

---

## Pricing Table

Built-in rates are included for MiniMax, Gemini, Anthropic, OpenAI, and local Ollama models (always `free`). Override any model in config. See [docs/pricing.md](docs/pricing.md) for the full table.

---

## Changelog

See [CHANGELOG.md](CHANGELOG.md).

---

## Acknowledgments

This plugin exists because of the people who build things in the open and share them without gatekeeping.

**[NousResearch](https://github.com/NousResearch)** — for building Hermes Agent and designing a plugin system clean enough that something like this is a weekend project, not a fork. The hook architecture made this possible without touching core.

**The Hermes contributors and community** — the developers maintaining the agent runtime, writing plugins, and pushing the ecosystem forward. This plugin stands on top of what you built.

**The homelab community** — the people running their own stacks at home, self-hosting everything from LLMs to smart home infrastructure, and sharing how they do it. You proved that serious infrastructure doesn't require enterprise budgets.

**The vibe coders** — those who follow the architect-bricklayer ideal: knowing the blueprint before laying the first brick, thinking in systems while staying hands-on in the code. You ship things that work because you understand both ends of the stack.

Build something, share it, help the next person go faster.

---

## License

MIT
