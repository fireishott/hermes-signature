#!/usr/bin/env bash
# hermes-signature installer
# Copies the plugin into ~/.hermes/plugins/ (user plugin dir), enables it
# via `hermes plugins enable`, and adds starter config to ~/.hermes/config.yaml.

set -euo pipefail

PLUGIN_SRC="$(cd "$(dirname "$0")/plugins/signature" && pwd)"
HERMES_DIR="${HERMES_DIR:-$HOME/.hermes}"
PLUGIN_DEST="$HERMES_DIR/plugins/signature"
CONFIG="$HERMES_DIR/config.yaml"

echo "→ Installing hermes-signature plugin..."

# Copy plugin files into user plugin directory
mkdir -p "$PLUGIN_DEST"
cp -r "$PLUGIN_SRC/." "$PLUGIN_DEST/"
echo "✓ Plugin copied to $PLUGIN_DEST"

# Enable via Hermes CLI
hermes plugins enable hermes-signature 2>/dev/null \
  || ~/.local/bin/hermes plugins enable hermes-signature 2>/dev/null \
  || echo "→ Run 'hermes plugins enable hermes-signature' to activate"

# Add starter config if signature block not present
if ! grep -q "^signature:" "$CONFIG" 2>/dev/null; then
  cat >> "$CONFIG" <<'EOF'

# ── Hermes Signature ──────────────────────────────────────────────────────────
signature:
  enabled: true
  agent_name: "ignyte"
  icon: "⚡"
  show_model: true
  show_provider: true
  show_latency: true
  show_tokens: true
  show_cost: true
  platforms: []   # empty = all; e.g. ["discord", "bluebubbles"] to restrict
EOF
  echo "✓ Config block added to $CONFIG"
else
  echo "→ Config block already present, skipping"
fi

echo ""
echo "✓ Done. Restart the gateway: hermes gateway restart"
