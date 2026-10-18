#!/usr/bin/env bash
# =======================================================
#       Josh's AI Tools Setup for Linux & macOS
# =======================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CLAUDE_DIR="$HOME/.claude"
SOURCE_SETTINGS="$SCRIPT_DIR/templates/claude_settings.json"
CONFIGURATOR="$SCRIPT_DIR/scripts/configure.py"

echo "======================================================="
echo "        Josh's AI Tools Setup (Linux/macOS)            "
echo "======================================================="
echo ""

# Check for Python
PY_BIN=""
if command -v python3 >/dev/null 2>&1; then
    PY_BIN="python3"
elif command -v python >/dev/null 2>&1; then
    PY_BIN="python"
fi

if [ -z "$PY_BIN" ]; then
    echo "[!] ERROR: Python 3 was not found in your PATH."
    echo "    Please install Python 3.9+ to run the setup and linter tools."
    exit 1
fi

PY_VER="$($PY_BIN --version 2>&1)"
echo "[OK] Python detected: $PY_VER"
echo "Repo directory: $SCRIPT_DIR"
echo ""

echo "Choose configuration mode:"
echo "  [1] Configure Claude Code only (Global ~/.claude/CLAUDE.md)"
echo "  [2] Configure ALL AI Tools (Claude, Cursor, Cline, Antigravity, Codex, Windsurf, Copilot, Aider)"
echo "  [3] Custom Interactive Wizard"
echo ""

read -r -p "Select option [1, 2, or 3, default 2]: " mode_choice
mode_choice="${mode_choice:-2}"

case "$mode_choice" in
    1)
        echo ""
        echo "[+] Configuring Claude Code..."
        $PY_BIN "$CONFIGURATOR" --tools claude --scope global
        ;;
    2)
        echo ""
        echo "[+] Configuring ALL supported AI tools..."
        $PY_BIN "$CONFIGURATOR" --tools all --scope global
        ;;
    3)
        echo ""
        $PY_BIN "$CONFIGURATOR"
        ;;
    *)
        echo ""
        echo "[+] Configuring ALL supported AI tools..."
        $PY_BIN "$CONFIGURATOR" --tools all --scope global
        ;;
esac

# Handle Claude settings.json template if ~/.claude exists
echo ""
DEST_SETTINGS="$CLAUDE_DIR/settings.json"
if [ -d "$CLAUDE_DIR" ]; then
    if [ -f "$DEST_SETTINGS" ]; then
        read -r -p "[?] Claude settings.json already exists at $DEST_SETTINGS. Overwrite? [y/N]: " ow_settings
        case "$ow_settings" in
            [Yy]*)
                cp "$SOURCE_SETTINGS" "$DEST_SETTINGS"
                echo "[OK] settings.json updated."
                ;;
            *)
                echo "[=] Kept existing settings.json."
                ;;
        esac
    else
        read -r -p "[?] Install recommended Claude settings.json (bypassPermissions mode, dark theme)? [Y/n]: " inst_settings
        case "$inst_settings" in
            [Nn]*)
                echo "[=] Skipped settings.json."
                ;;
            *)
                cp "$SOURCE_SETTINGS" "$DEST_SETTINGS"
                echo "[OK] settings.json installed."
                ;;
        esac
    fi
fi

# Optional vulture install
echo ""
read -r -p "[?] Install optional 'vulture' package for unused code detection (rule 21)? [y/N]: " inst_vulture
case "$inst_vulture" in
    [Yy]*)
        echo "[+] Running: $PY_BIN -m pip install vulture"
        $PY_BIN -m pip install vulture || pip install vulture || echo "[!] Could not install vulture automatically. Install manually via pip if needed."
        ;;
    *)
        echo "[=] Skipped vulture installation."
        ;;
esac

# Global terminal shortcuts
echo ""
read -r -p "[?] Install global shortcuts (ailint, aifix, airepo, aimd, aitree, aisearch, aislice, aidiff, airollback, aisync, aitest, aitokens, aicontext, aisec, aihook) into ~/.local/bin? [Y/n]: " inst_shortcuts
case "$inst_shortcuts" in
    [Nn]*)
        echo "[=] Skipped global shortcuts."
        ;;
    *)
        mkdir -p "$HOME/.local/bin"
        for cmd_file in "$SCRIPT_DIR/bin/"*; do
            cmd_name="$(basename "$cmd_file")"
            if [ "${cmd_name##*.}" != "cmd" ]; then
                ln -sf "$cmd_file" "$HOME/.local/bin/$cmd_name"
            fi
        done
        chmod +x "$SCRIPT_DIR/bin/"*
        echo "[OK] Symlinks created in ~/.local/bin/ (ensure ~/.local/bin is in your PATH)."
        ;;
esac

echo ""
echo "======================================================="
echo "               Setup Completed Successfully!           "
echo "======================================================="
echo "All selected AI tools are configured with your rules and linter."
echo ""
