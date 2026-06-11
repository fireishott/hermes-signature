# Changelog

## [0.11.0] — 2026-06-10

### Added
- **GPT-5.5 pricing** — added built-in rates (.00/0.00//bin/bash.50).

### Changed
- **Footer format** — removed agent profile name from the primary line.
- Version bumped to 0.11.0.

## 0.10.2 — Simplified: profile name IS the agent name

- Removed `agent_name` config. Footer now shows `{icon} {profile_name}` — the active profile slug + its icon.
- Removed `show_profile` toggle. Profile name is always the primary identity.
- Config now just needs `icon:` per profile.


## 0.10.1 — agent_name auto-fallback

- `agent_name` now falls back to the active profile name when not explicitly set in config. Set `agent_name` only to override (e.g. "Ignyte" for the default profile).

## 0.10.0 — Multi-profile support

- **Profile field** — Footer now shows the active Hermes profile name (e.g., `default`, `flynt`). Controlled by `show_profile: true` (default on).
- **Profile-scoped caches** — Usage/balance caches are now keyed by `(profile, provider)` tuple, preventing cross-profile data bleed when switching between profiles.
- **New config flag** — `show_profile: true/false` in the signature config block.

## 0.9.0 — DeepSeek balance tracking

### Added
- **Cached token tracking** — footer now shows `800 cached` when the API reports cached input tokens via `prompt_tokens_details.cached_tokens`
- **Cache-aware cost calculation** — cached input tokens use the cheaper cache rate (e.g. MiMo v2.5 Pro: $0.0036/1M vs $0.435/1M regular input); models without a cache rate fall back to the regular input rate
- `show_cached` config flag (default: `true`) — toggle cached token display on/off
- `cache` field in pricing table — per-model cached input rate (optional; falls back to `input` rate if absent)
- `cached` field added to configurable `order:` list (default position: after `tokens_total`)
- Built-in cache rates for MiMo v2.5 series: `mimo-v2.5-pro` ($0.0036), `mimo-v2.5` ($0.0028), `mimo-v2-flash` ($0.01)

### Changed
- `estimate_cost()` now accepts optional `cached_tokens` parameter for split-rate calculation
- `on_post_api_request` extracts and accumulates cached tokens per model per turn
- Version bumped to 0.9.0

---

## [0.8.0] — 2026-06-09

### Added
- **Xiaomi MiMo v2.5 series pricing** — built-in rates for `mimo-v2.5-pro` ($0.435/$0.870), `mimo-v2.5` ($0.14/$0.28), `mimo-v2-flash` ($0.10/$0.30), `mimo-v2-pro` ($1.00/$3.00)
- **DeepSeek v4 series pricing** — `deepseek-v4-pro` ($0.50/$2.00), `deepseek-v4-flash` ($0.10/$0.40)
- **MiMo Token Plan subscription docs** — annual plans, credit consumption rates, key policies (Lite $63.36/yr through Max $1,056/yr)

### Changed
- Default model reference updated from `MiniMax-M2.7` to `mimo-v2.5-pro` across docstrings and config examples
- MiniMax demoted to "legacy" in pricing docs
- Footer example updated to show MiMo model and 🔥 icon
- Version bumped to 0.8.0

---

## [0.6.5] — 2026-06-08

### Fixed
- Balance and usage quota not showing for `custom:openrouter` and `custom:deepseek` providers — updated provider mapping and balance fetch logic to handle the `custom:` prefix correctly.

---

## [0.6.4] — 2026-05-26

### Fixed
- Balance and provider not showing when framework omits `provider` kwarg in `transform_llm_output` — add `default_provider` config key as fallback (mirrors `default_model`)

### Added
- `default_provider` config key — used when framework doesn't pass a provider name in hook kwargs

---

## [0.6.3] — 2026-05-26

### Fixed
- Balance not showing — API key reads now fall back to `~/.hermes/.env` when `os.environ` doesn't have it (gateway may not propagate env to plugin threads)
- Per-turn cost now labeled as `~$0.0271 trn` to distinguish it from session cost (`$0.43 ses`)

---

## [0.6.2] — 2026-05-26

### Added
- Configurable footer field order via `order:` list in config
  - All primary line fields are addressable: `model`, `provider`, `latency`, `tokens_direction`, `tokens_total`, `cost`, `session_cost`, `turns`, `usage_pct`, `reset`, `balance`
  - Extra lines also orderable: `tools`, `aux`
  - Omit `order:` entirely to keep the default order unchanged
  - Fields omitted from the list are hidden regardless of their `show_*` flag

---

## [0.6.1] — 2026-05-26

### Added
- Token display sub-flags — `show_tokens` remains the master toggle; two new flags for granular control:
  - `show_tokens_direction` (default: `true`) — show `1,247↑ 600↓` input/output split
  - `show_tokens_total` (default: `true`) — show `1,847 tok` combined count
  - Both default `true` so existing behavior is unchanged

---

## [0.6.0] — 2026-05-26

### Added
- Session cost — cumulative spend for the current session shown as `$0.43 ses`
  - Accumulates across turns like the turn counter — never resets mid-session
  - `show_session_cost` config flag (default: `true`)
- Account balance — remaining API balance shown as `$99.48 bal`
  - Supported providers: `deepseek` (DEEPSEEK_API_KEY), `openrouter` (OPENROUTER_API_KEY)
  - Fetched in background after each response; zero latency (cached value on next call)
  - `show_balance` config flag (default: `true`)

---

## [0.5.2] — 2026-05-26

### Changed
- Aux model tracking is now plugin-only — uses `aux_tool_models` config map (tool name → model) instead of requiring framework hook support
- `on_post_tool_call` maps known tools to their backing models and counts calls per model
- Aux line renders as `-# 🔩 gemini-2.5-flash-lite×3` (same count style as tools line) — no token data since aux calls bypass `post_api_request`
- Removed dead code path that attempted to split aux usage from `post_api_request` (framework never fires that hook for aux calls)

### Added
- `aux_tool_models` config key — map any tool name to its backing model

---

## [0.5.1] — 2026-05-26

### Changed
- Aux model lines (`-# 🔩`) now appear after the tool call line (`-# 🔧`) instead of before it

---

## [0.5.0] — 2026-05-25

### Added
- Aux model tracking — footer now shows a separate `-# 🔩` line for each aux model called in a turn (vision, MCP, local LLM, etc.)
  - Token usage and cost are reported per aux model
  - Aux lines appear between the primary footer and the tool line
- `show_aux` config flag (default: `true`) — toggle aux model lines on/off
- `default_model` config key — fallback model name shown in footer when the framework doesn't pass one in hook kwargs
- Token accumulator is now keyed per model — `post_api_request` buckets usage by model name so primary vs aux are tracked independently

---

## [0.4.0] — 2026-05-25

### Added
- Session turn counter — footer now shows `12 turns` (number of LLM turns in the current session)
  - Counter accumulates for the full session lifetime — never resets between turns
  - Shows `1 turn` / `N turns` (singular/plural)
- `show_turns` config flag (default: `true`) — toggle turn counter on/off

---

## [0.3.0] — 2026-05-24

### Added
- Usage quota countdown — footer now shows `resets in 4h 57m` for supported providers
  - Supported: `anthropic` (OAuth), `openai-codex`, `openrouter`
  - Unsupported providers (minimax, gemini, xai, custom) silently skip — no error
  - Background thread fetches after each response; zero latency (cached value on next call)
  - First call shows nothing; second call onward shows live data
- `show_reset` config flag (default: `true`) — toggle countdown on/off
- `show_usage_pct` config flag (default: `false`) — toggle `42% used` display
- New `usage.py` module — provider mapping, background fetching, cache layer

### Notes
- Anthropic usage requires OAuth token (Claude.ai login via `hermes auth`), not a raw API key
- MiniMax, Gemini, and xAI have no public usage quota API — those providers are skipped

---

## [0.2.0] — 2026-05-24

### Added
- Tool call footer line — shows every tool used in the turn with call counts
  - Single call: `read_file`
  - Multiple calls: `bash×3`
  - Format: `-# 🔧 web_search×2 · bash · read_file`
- `post_tool_call` hook registered to accumulate tool counts per session
- `show_tools` config flag (default: `true`) to toggle tool line independently

## [0.1.1] — 2026-05-24

### Changed
- Token field now shows input↑, completion↓, and total: `1,247↑ 600↓ 1,847 tok`

---

All notable changes to hermes-signature will be documented here.

Format follows [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).
Versioning follows [Semantic Versioning](https://semver.org/).

---

## [0.1.0] — 2026-05-23

### Added
- Initial release
- `pre_llm_call` hook — records turn start time per session
- `post_api_request` hook — accumulates token usage across all API calls in a turn (handles tool call chains)
- `transform_llm_output` hook — builds and appends footer to every LLM response
- Footer fields: icon, agent name, model, provider, estimated latency, token count, cost estimate
- Built-in pricing table for MiniMax, Gemini, Anthropic, OpenAI, and local Ollama models
- Per-model price overrides via `config.yaml`
- Platform filtering — restrict footer to specific platforms (Discord, BlueBubbles, etc.)
- All fields individually toggleable via config
- Local/Ollama models show `free` instead of a cost
- Cost `<$0.0001` shown as `<$0.0001` to avoid misleading `~$0.0000`
- `install.sh` — copies plugin and appends starter config block
- Full documentation suite (docs/)
