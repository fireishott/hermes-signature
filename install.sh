#!/usr/bin/env bash
# hermes-signature installer
# Copies the plugin into ~/.hermes/hermes-agent/plugins/ and adds
# starter config to ~/.hermes/config.yaml if not already present.

set -euo pipefail

PLUGIN_SRC="$(cd "$(dirname "$0")/plugins/signature" && pwd)"
HERMES_DIR="${HERMES_DIR:-$HOME/.hermes}"
PLUGIN_DEST="$HERMES_DIR/hermes-agent/plugins/signature"
CONFIG="$HERMES_DIR/config.yaml"

echo "→ Installing hermes-signature plugin..."

# Copy plugin files
mkdir -p "$PLUGIN_DEST"
cp -r "$PLUGIN_SRC/." "$PLUGIN_DEST/"
echo "✓ Plugin copied to $PLUGIN_DEST"

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
  platforms: []   # empty = all; e.g. ["discord", "bluebubbles"] to restrict
EOF
  echo "✓ Config block added to $CONFIG"
else
  echo "→ Config block already present, skipping"
fi

echo ""
echo "✓ Done. Restart the gateway: hermes gateway restart"
