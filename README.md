# hermes-signature

A lightweight Hermes plugin that appends a signature footer to every LLM response.

```
-# ⚡ ignyte · MiniMax-M2.7 · minimax · ~1.2s est.
```

No patching of Hermes core. Survives `hermes update`. Uses the native `transform_llm_output` plugin hook.

## Install

```bash
git clone https://github.com/fih/hermes-signature
cd hermes-signature
chmod +x install.sh
./install.sh
hermes gateway restart
```

## Config

Added to `~/.hermes/config.yaml` by the installer:

```yaml
signature:
  enabled: true
  agent_name: "ignyte"    # label shown in footer
  icon: "⚡"              # leading emoji/icon
  show_model: true         # include model name
  show_provider: true      # include provider name
  show_latency: true       # include ~Xs est. latency
  platforms: []            # restrict to platforms; empty = all
```

## Notes

- Latency is measured from `pre_llm_call` hook entry and labelled `est.` since it includes hook overhead, not raw API time.
- `transform_llm_output` fires before platform delivery so the footer lands in the same message — no editing after the fact.
- First non-None return wins; won't conflict with other transform plugins as long as this one loads first.
