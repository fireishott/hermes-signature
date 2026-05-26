# Changelog

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
