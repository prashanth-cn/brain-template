#!/usr/bin/env bash
# Also runnable with: zsh setup.sh
set -euo pipefail

VAULT="$(pwd)"
APP_NAME="$(basename "$VAULT")"
BRAIN_CONFIG="$HOME/.config/$APP_NAME/vault"
LOCAL_BIN="$HOME/.local/bin"

# ── Detect OS ─────────────────────────────────────────────────────────────────
OS="$(uname -s)"
case "$OS" in
  Darwin) PLATFORM="macos" ;;
  Linux)  PLATFORM="linux" ;;
  *)
    echo "ERROR: Unsupported platform: $OS"
    exit 1
    ;;
esac

# ── Helpers ───────────────────────────────────────────────────────────────────
HAS_BREW=0
[ "$PLATFORM" = "macos" ] && command -v brew &>/dev/null && HAS_BREW=1

brew_install() {
  local pkg="$1"
  if [ "$HAS_BREW" -eq 1 ]; then
    echo "  → brew install $pkg"
    brew install "$pkg" -q
  else
    echo "  WARNING: Homebrew not found. Install it first: https://brew.sh"
    echo "  Then run: brew install $pkg"
  fi
}

linux_install() {
  local pkg="$1"
  if command -v apt-get &>/dev/null; then
    sudo apt-get install -y "$pkg"
  elif command -v dnf &>/dev/null; then
    sudo dnf install -y "$pkg"
  elif command -v pacman &>/dev/null; then
    sudo pacman -S --noconfirm "$pkg"
  else
    echo "  WARNING: Could not detect package manager. Install $pkg manually."
  fi
}

ensure() {
  local cmd="$1" brew_pkg="${2:-$1}" linux_pkg="${3:-$1}"
  if command -v "$cmd" &>/dev/null; then
    return 0
  fi
  echo "→ Installing $cmd..."
  case "$PLATFORM" in
    macos) brew_install "$brew_pkg" ;;
    linux) linux_install "$linux_pkg" ;;
  esac
}

echo "Setting up brain vault at: $VAULT ($PLATFORM)"
[ "$HAS_BREW" -eq 1 ] && echo "  Homebrew detected — missing deps will be installed automatically."
echo ""

# ── 1. System dependencies ────────────────────────────────────────────────────
if ! command -v python3 &>/dev/null; then
  echo "ERROR: python3 not found."
  [ "$PLATFORM" = "macos" ] && echo "  brew install python@3.12"
  [ "$PLATFORM" = "linux" ] && echo "  sudo apt-get install python3 python3-venv"
  exit 1
fi

PY_MAJOR=$(python3 -c 'import sys; print(sys.version_info.major)')
PY_MINOR=$(python3 -c 'import sys; print(sys.version_info.minor)')
if [ "$PY_MAJOR" -lt 3 ] || { [ "$PY_MAJOR" -eq 3 ] && [ "$PY_MINOR" -lt 11 ]; }; then
  echo "ERROR: Python 3.11+ required (found $PY_MAJOR.$PY_MINOR)."
  [ "$PLATFORM" = "macos" ] && echo "  brew install python@3.12"
  exit 1
fi

ensure node node nodejs
ensure ffmpeg ffmpeg ffmpeg

# ── 2. Claude Code (required) ─────────────────────────────────────────────────
echo ""
if ! command -v claude &>/dev/null; then
  echo "ERROR: Claude Code is not installed."
  echo "  Install it from: https://claude.ai/code"
  echo "  Then re-run this script."
  exit 1
fi
echo "→ Claude Code $(claude --version 2>/dev/null || echo '') detected"

# ── 3. Python venv ────────────────────────────────────────────────────────────
echo ""
echo "→ Creating Python venv..."
python3 -m venv "$VAULT/.venv"
"$VAULT/.venv/bin/pip" install -q --upgrade pip
"$VAULT/.venv/bin/pip" install -q -e "$VAULT"
echo "  Done: brain-ingest and brain-persist installed"

# ── 4. API key ────────────────────────────────────────────────────────────────
echo ""
if [ ! -f "$VAULT/.env" ] || ! grep -q "^ANTHROPIC_API_KEY=sk-ant-" "$VAULT/.env" 2>/dev/null; then
  # Check if already in environment
  if [ -n "${ANTHROPIC_API_KEY:-}" ] && [[ "$ANTHROPIC_API_KEY" == sk-ant-* ]]; then
    echo "→ Using ANTHROPIC_API_KEY from environment..."
    echo "ANTHROPIC_API_KEY=$ANTHROPIC_API_KEY" > "$VAULT/.env"
  else
    echo "→ Anthropic API key required."
    echo "  Get yours at: https://console.anthropic.com/settings/keys"
    read -r -p "  Paste your API key (sk-ant-...): " INPUT_KEY
    if [[ "$INPUT_KEY" != sk-ant-* ]]; then
      echo "  ERROR: Key must start with sk-ant-"
      exit 1
    fi
    echo "ANTHROPIC_API_KEY=$INPUT_KEY" > "$VAULT/.env"
    echo "  Saved to .env"
  fi
else
  echo "→ .env already configured — skipping"
fi

# ── 5. Project-local configs ──────────────────────────────────────────────────
echo ""
echo "→ Generating project configs..."
cp "$VAULT/.mcp.json.template" "$VAULT/.mcp.json"
mkdir -p "$VAULT/.claude"
cp "$VAULT/.claude/settings.local.json.template" "$VAULT/.claude/settings.local.json"

# ── 6. Save vault path ────────────────────────────────────────────────────────
echo "→ Saving vault path to $BRAIN_CONFIG..."
mkdir -p "$(dirname "$BRAIN_CONFIG")"
echo "$VAULT" > "$BRAIN_CONFIG"

# ── 7. Install wrappers ───────────────────────────────────────────────────────
echo "→ Installing wrappers to $LOCAL_BIN..."
mkdir -p "$LOCAL_BIN"

cat > "$LOCAL_BIN/brain-ingest" <<EOF
#!/usr/bin/env bash
BRAIN_VAULT="\$(cat "$BRAIN_CONFIG")"
exec "\$BRAIN_VAULT/.venv/bin/brain-ingest" "\$@"
EOF

cat > "$LOCAL_BIN/brain-persist" <<EOF
#!/usr/bin/env bash
BRAIN_VAULT="\$(cat "$BRAIN_CONFIG")"
exec "\$BRAIN_VAULT/.venv/bin/brain-persist" "\$@"
EOF

chmod +x "$LOCAL_BIN/brain-ingest" "$LOCAL_BIN/brain-persist"

if ! echo "$PATH" | tr ':' '\n' | grep -qx "$LOCAL_BIN"; then
  echo "  WARNING: $LOCAL_BIN is not in PATH. Adding to your shell profile..."
  PROFILE=""
  [ -f "$HOME/.zshrc" ]    && PROFILE="$HOME/.zshrc"
  [ -z "$PROFILE" ] && [ -f "$HOME/.bashrc" ] && PROFILE="$HOME/.bashrc"
  [ -z "$PROFILE" ] && [ -f "$HOME/.bash_profile" ] && PROFILE="$HOME/.bash_profile"
  if [ -n "$PROFILE" ]; then
    echo '' >> "$PROFILE"
    echo '# brain vault' >> "$PROFILE"
    echo 'export PATH="$HOME/.local/bin:$PATH"' >> "$PROFILE"
    echo "  Added to $PROFILE — restart your shell or run: source $PROFILE"
  else
    echo "  Could not detect shell profile. Add manually:"
    echo '  export PATH="$HOME/.local/bin:$PATH"'
  fi
fi

# ── 8. MCP server ─────────────────────────────────────────────────────────────
echo ""
echo "→ Registering brain-obsidian MCP server with Claude Code..."
claude mcp remove brain-obsidian --scope user 2>/dev/null || true
claude mcp add --scope user brain-obsidian npx -- -y obsidian-mcp "$VAULT"
echo "  Registered — available in all Claude Code projects"

# ── 9. Global Stop hook ───────────────────────────────────────────────────────
echo "→ Installing Stop hook into ~/.claude/settings.json..."
python3 - <<'PYEOF'
import json, os, sys
from pathlib import Path

settings_path = Path.home() / ".claude" / "settings.json"
settings_path.parent.mkdir(parents=True, exist_ok=True)

try:
    settings = json.loads(settings_path.read_text()) if settings_path.exists() else {}
except json.JSONDecodeError:
    print(f"  ERROR: {settings_path} is not valid JSON. Fix it manually.")
    sys.exit(1)

hook_entry = {
    "matcher": "",
    "hooks": [{"type": "command", "command": "brain-persist", "async": True}]
}

hooks = settings.setdefault("hooks", {})
stop_hooks = hooks.setdefault("Stop", [])

# Idempotent: only add if brain-persist not already present
already = any(
    any(h.get("command") == "brain-persist" for h in entry.get("hooks", []))
    for entry in stop_hooks
)

if already:
    print("  Already configured — skipping")
else:
    stop_hooks.append(hook_entry)
    settings_path.write_text(json.dumps(settings, indent=2))
    print("  Done")
PYEOF

# ── 10. Done ──────────────────────────────────────────────────────────────────
echo ""
echo "✓ All done."
echo ""
echo "  Open $VAULT in Obsidian: File → Open folder as vault"
echo "  Restart Claude Code to activate the MCP server"
echo ""
