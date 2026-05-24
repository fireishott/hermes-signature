# Changelog

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
