#!/usr/bin/env bash
# Also runnable with: zsh uninstall.sh
set -euo pipefail

VAULT="$(cd "$(dirname "${BASH_SOURCE[0]:-$0}")" && pwd)"
APP_NAME="$(basename "$VAULT")"
BRAIN_CONFIG="$HOME/.config/$APP_NAME/vault"
LOCAL_BIN="$HOME/.local/bin"

echo "Uninstalling brain vault tooling..."
echo "  Vault: $VAULT"
echo "  (Your notes will NOT be deleted.)"
echo ""

# ── 1. MCP server ─────────────────────────────────────────────────────────────
echo "→ Removing brain-obsidian MCP server..."
claude mcp remove brain-obsidian --scope user 2>/dev/null && echo "  Done" || echo "  Not found — skipping"

# ── 2. Stop hook ──────────────────────────────────────────────────────────────
echo "→ Removing brain-persist Stop hook from ~/.claude/settings.json..."
python3 - <<'PYEOF'
import json, sys
from pathlib import Path

settings_path = Path.home() / ".claude" / "settings.json"
if not settings_path.exists():
    print("  settings.json not found — skipping")
    sys.exit(0)

try:
    settings = json.loads(settings_path.read_text())
except json.JSONDecodeError:
    print(f"  ERROR: {settings_path} is not valid JSON — skipping")
    sys.exit(0)

stop_hooks = settings.get("hooks", {}).get("Stop", [])
filtered = [
    entry for entry in stop_hooks
    if not any(h.get("command") == "brain-persist" for h in entry.get("hooks", []))
]

if len(filtered) == len(stop_hooks):
    print("  Not found — skipping")
else:
    settings["hooks"]["Stop"] = filtered
    if not settings["hooks"]["Stop"]:
        del settings["hooks"]["Stop"]
    if not settings["hooks"]:
        del settings["hooks"]
    settings_path.write_text(json.dumps(settings, indent=2))
    print("  Done")
PYEOF

# ── 3. CLI wrappers ───────────────────────────────────────────────────────────
echo "→ Removing CLI wrappers from $LOCAL_BIN..."
for cmd in brain-ingest brain-persist; do
  if [ -f "$LOCAL_BIN/$cmd" ]; then
    rm "$LOCAL_BIN/$cmd"
    echo "  Removed $cmd"
  else
    echo "  $cmd not found — skipping"
  fi
done

# ── 4. Vault path config ──────────────────────────────────────────────────────
echo "→ Removing vault path config..."
if [ -f "$BRAIN_CONFIG" ]; then
  rm "$BRAIN_CONFIG"
  echo "  Removed $BRAIN_CONFIG"
else
  echo "  Not found — skipping"
fi

# ── 5. Python venv ────────────────────────────────────────────────────────────
echo "→ Removing Python venv..."
if [ -d "$VAULT/.venv" ]; then
  rm -rf "$VAULT/.venv"
  echo "  Removed .venv"
else
  echo "  Not found — skipping"
fi

# ── 6. Generated project configs ─────────────────────────────────────────────
echo "→ Removing generated project configs..."
for f in "$VAULT/.mcp.json" "$VAULT/.claude/settings.local.json"; do
  if [ -f "$f" ]; then
    rm "$f"
    echo "  Removed $f"
  fi
done

# ── 7. PATH entry hint ────────────────────────────────────────────────────────
echo ""
echo "→ If setup.sh added ~/.local/bin to your PATH, remove it manually from:"
for profile in "$HOME/.zshrc" "$HOME/.bashrc" "$HOME/.bash_profile"; do
  [ -f "$profile" ] && grep -q 'brain vault' "$profile" && echo "    $profile"
done || true

# ── Done ──────────────────────────────────────────────────────────────────────
echo ""
echo "✓ Uninstall complete. Your vault notes are untouched at:"
echo "  $VAULT"
