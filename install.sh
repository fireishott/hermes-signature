#!/usr/bin/env bash
# hermes-signature installer
# Clones the repo directly into ~/.hermes/plugins/hermes-signature/ so Hermes
# recognises it as a git-sourced plugin. Enables it via `hermes plugins enable`
# and appends a starter config block to ~/.hermes/config.yaml.

set -euo pipefail

HERMES_DIR="${HERMES_DIR:-$HOME/.hermes}"
PLUGIN_DEST="$HERMES_DIR/plugins/hermes-signature"
CONFIG="$HERMES_DIR/config.yaml"
REPO_URL="https://github.com/fireishott/hermes-signature.git"

echo "→ Installing hermes-signature plugin..."

# Clone or update
if [ -d "$PLUGIN_DEST/.git" ]; then
  echo "→ Existing install found — pulling latest..."
  git -C "$PLUGIN_DEST" pull --ff-only
else
  git clone "$REPO_URL" "$PLUGIN_DEST"
fi
echo "✓ Plugin at $PLUGIN_DEST"

# Enable via Hermes CLI
hermes plugins enable hermes-signature 2>/dev/null \
  || ~/.local/bin/hermes plugins enable hermes-signature 2>/dev/null \
  || echo "→ Run 'hermes plugins enable hermes-signature' manually"

# Add starter config if signature block not present
if ! grep -q "^signature:" "$CONFIG" 2>/dev/null; then
  cat >> "$CONFIG" <<'EOF'

# ── Hermes Signature ──────────────────────────────────────────────────────────
signature:
  enabled: true
  agent_name: "hermes"
  icon: "⚡"
  show_model: true
  show_provider: true
  show_latency: true
  show_tokens: true
  show_cost: true
  show_tools: true
  platforms: []   # empty = all; e.g. ["discord", "bluebubbles"] to restrict
EOF
  echo "✓ Config block added to $CONFIG"
else
  echo "→ Config block already present, skipping"
fi

echo ""
echo "✓ Done. Restart the gateway: hermes gateway restart"
