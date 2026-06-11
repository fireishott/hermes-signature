# hermes-signature

![Version](https://img.shields.io/badge/version-0.10.0-blue?style=flat-square)
![Python](https://img.shields.io/badge/python-3.11%2B-3776AB?style=flat-square&logo=python&logoColor=white)
![Hermes](https://img.shields.io/badge/hermes--agent-compatible-gold?style=flat-square)
![License](https://img.shields.io/badge/license-MIT-green?style=flat-square)
![Platform](https://img.shields.io/badge/platform-macOS%20%7C%20Linux-lightgrey?style=flat-square)

A lightweight [Hermes Agent](https://github.com/NousResearch/hermes-agent) plugin that appends a signature footer to every LLM response.

```
-# 🔥 ignyte · default · deepseek-v4-pro · deepseek · ~1.2s est. · 1,247↑ 600↓ 1,847 tok · 800 cached · ~$0.0004 trn · $0.43 ses · 12 turns · resets in 4h 57m · $99.48 bal
-# 🔧 web_search×3 · bash×2 · vision_analyze×3
-# 🔩 gemini-2.5-flash-lite×3
```

No patching of Hermes core. Survives `hermes update`. Pure plugin via native hooks.

---

## Features

- **Model & provider** — shows exactly what handled the turn
- **Estimated latency** — measured from `pre_llm_call` to response, labelled `est.`
- **Token usage** — accumulated across all API calls in the turn; shows `input↑ output↓` split and/or total, independently togglable
- **Cached tokens** — shows `800 cached` when the API reports cached input; cost calculation uses the cheaper cache rate
- **Per-turn cost** — computed from a built-in pricing table, labelled `trn`; overridable per model in config
- **Session cost** — cumulative spend for the full session, labelled `ses`
- **Session turn counter** — number of LLM turns since session start
- **Tool call line** — every tool used in the turn with call counts (`🔧 bash×3 · read_file`)
- **Aux model line** — tracks calls to backing models (vision, MCP, local LLM) via a config map; shown as `🔩 gemini-2.5-flash-lite×3`
- **Usage quota** — `resets in 4h 57m` and/or `42% used` for supported providers (Anthropic OAuth, OpenAI Codex, OpenRouter)
- **Account balance** — `$99.48 bal` for DeepSeek and OpenRouter; fetched in background at zero latency
- **Configurable field order** — reorder any footer field via `order:` list in config
- **Platform filtering** — restrict footer to specific platforms (Discord, BlueBubbles, etc.)
- **Local models = free** — Ollama/local models show `free` instead of a cost

---

## Install

```bash
git clone https://github.com/fireishott/hermes-signature ~/.hermes/plugins/hermes-signature
hermes gateway restart
```

Or use the included installer which also appends a starter config block:

```bash
git clone https://github.com/fireishott/hermes-signature
cd hermes-signature
chmod +x install.sh
./install.sh
hermes gateway restart
```

---

## Configuration

```yaml
signature:
  enabled: true
  agent_name: "hermes"          # Label shown at the start of the footer
  icon: "⚡"                    # Leading icon/emoji
  default_model: ""             # Fallback model name when framework doesn't pass one

  # Field toggles
  show_profile: true            # Show active profile name (default, flynt, etc.)
  show_model: true
  show_provider: true
  show_latency: true
  show_tokens: true             # Master toggle for all token display
  show_tokens_direction: true   # Show 1,247↑ 600↓ input/output split
  show_tokens_total: true       # Show 1,847 tok combined count
  show_cached: true             # Show cached token count (500 cached)
  show_cost: true               # Per-turn cost (~$0.0004 trn)
  show_session_cost: true       # Cumulative session cost ($0.43 ses)
  show_turns: true              # Turn counter (12 turns)
  show_usage_pct: false         # Quota usage percentage (42% used)
  show_reset: true              # Quota reset countdown (resets in 4h 57m)
  show_balance: true            # Account balance ($99.48 bal)
  show_tools: true              # Tool call line (🔧 bash×3)
  show_aux: true                # Aux model line (🔩 gemini-2.5-flash-lite×3)

  # Field order — controls left-to-right order on the primary line
  # Omit entirely to use the default order. Fields not listed are hidden.
  order:
    - profile
    - model
    - provider
    - latency
    - tokens_direction
    - tokens_total
    - cached
    - cost
    - session_cost
    - turns
    - usage_pct
    - reset
    - balance
    - tools
    - aux

  platforms: []                 # Restrict to platforms; empty = all
                                # e.g. ["discord", "bluebubbles"]

  # Map tool name → backing model for the 🔩 aux line
  # Use this for tools that call a secondary LLM internally
  aux_tool_models:
    vision_analyze: "gemini-2.5-flash-lite"
    video_analyze: "gemini-2.5-flash-lite"

  pricing:                      # Optional per-model price overrides (USD/1M tokens)
    mimo-v2.5-pro:
      input: 0.435
      output: 0.870
      cache: 0.0036
```

See [docs/configuration.md](docs/configuration.md) for the full reference.

---

## Footer Format

```
-# {icon} {agent_name} · {profile} · {model} · {provider} · ~{latency} · {input}↑ {output}↓ · {total} tok · {cached} cached · ~${cost} trn · ${session} ses · {N} turns · {reset} · ${balance} bal
-# 🔧 {tool}×{n} · {tool} · ...
-# 🔩 {aux_model}×{n} · ...
```

The `-#` prefix renders as small dimmed text in Discord. All three lines are optional. Every field can be toggled independently, and the order of fields on the primary line is configurable.

See [docs/footer-format.md](docs/footer-format.md) for format details and platform rendering notes.

---

## Aux Model Tracking

Hermes aux calls (vision, MCP tools, local LLMs) bypass the `post_api_request` hook, so the plugin can't see their token usage directly. Instead, configure a `aux_tool_models` map that links tool names to their backing models. When those tools are called, the plugin counts them and renders the `🔩` line.

```yaml
aux_tool_models:
  vision_analyze: "gemini-2.5-flash-lite"
  browser_vision: "gemini-flash-latest"
  web_extract: "gemini-2.5-flash-lite"
```

This means no token counts for aux models — just call counts. That's an acceptable trade-off to keep the plugin fully self-contained.

---

## Usage Quota & Balance

Background threads fetch quota and balance data after each response so the *next* call shows live data at zero latency. First call shows nothing; second call onward shows cached data.

**Quota (reset countdown + usage %):**
- `anthropic` — requires OAuth token (Claude.ai login via `hermes auth`), not a raw API key
- `openai-codex` — Codex OAuth
- `openrouter` — `OPENROUTER_API_KEY` (also supports `custom:openrouter`)

**Balance:**
- `deepseek` — `DEEPSEEK_API_KEY` (also supports `custom:deepseek`)
- `openrouter` — `OPENROUTER_API_KEY` (also supports `custom:openrouter`)

API keys are read from `os.environ` first, then from `~/.hermes/.env` as fallback.

---

## Pricing Table

Built-in rates are included for MiMo, DeepSeek, MiniMax, Gemini, Anthropic, OpenAI, and local Ollama models (always `free`). Override any model in config. See [docs/pricing.md](docs/pricing.md) for the full table and MiMo Token Plan subscription details.

---

## Changelog

See [CHANGELOG.md](CHANGELOG.md).

---

## Acknowledgments

This plugin exists because of the people who build things in the open and share them without gatekeeping.

**[NousResearch](https://github.com/NousResearch)** — for building Hermes Agent and designing a plugin system clean enough that something like this is a weekend project, not a fork. The hook architecture made this possible without touching core.

**The Hermes contributors and community** — the developers maintaining the agent runtime, writing plugins, and pushing the ecosystem forward. This plugin stands on top of what you built.

**The homelab community** — the people running their own stacks at home, self-hosting everything from LLMs to smart home infrastructure, and sharing how they do it. You proved that serious infrastructure doesn't require enterprise budgets.

**The vibe coders** — the ones who get it. The architect may not know how to lay a brick. The bricklayer may not know how to design. But when they work together, beautiful things get built. Keep finding your people.

Build something, share it, help the next person go faster.

---

## License

MIT
