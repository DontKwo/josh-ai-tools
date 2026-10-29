#!/usr/bin/env bash
# Josh AI Tools Setup for Linux & macOS

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CONFIGURATOR="$SCRIPT_DIR/scripts/configure.py"

echo "Josh AI Tools Setup (Linux/macOS)"
echo "Repo directory: $SCRIPT_DIR"
echo ""

# Check for uv or Python
PY_RUNNER=""
if command -v uv >/dev/null 2>&1; then
    PY_RUNNER="uv run --no-project python"
    echo "[OK] uv detected: $(uv --version)"
elif command -v python3 >/dev/null 2>&1; then
    PY_RUNNER="python3"
    echo "[OK] Python detected: $(python3 --version 2>&1)"
elif command -v python >/dev/null 2>&1; then
    PY_RUNNER="python"
    echo "[OK] Python detected: $(python --version 2>&1)"
else
    echo "[!] ERROR: Neither uv nor Python 3 was found in your PATH."
    echo "    Please install uv (https://docs.astral.sh/uv/) or Python 3.9+."
    exit 1
fi

echo ""
echo "Choose configuration mode:"
echo "  [1] Configure Claude Code only (Global ~/.claude/CLAUDE.md)"
echo "  [2] Configure ALL AI Tools globally (Claude, Cursor, Cline, Antigravity, Codex, Windsurf, Copilot, Aider)"
echo "  [3] Custom Interactive Wizard (choose tools, workspace vs global scope)"
echo ""

read -r -p "Select option [1, 2, or 3, default 2]: " mode_choice
mode_choice="${mode_choice:-2}"

case "$mode_choice" in
    1)
        echo ""
        echo "[+] Configuring Claude Code..."
        $PY_RUNNER "$CONFIGURATOR" --tools claude --scope global
        ;;
    2)
        echo ""
        echo "[+] Configuring ALL supported AI tools..."
        $PY_RUNNER "$CONFIGURATOR" --tools all --scope global
        ;;
    3)
        echo ""
        $PY_RUNNER "$CONFIGURATOR"
        ;;
    *)
        echo ""
        echo "[+] Configuring ALL supported AI tools..."
        $PY_RUNNER "$CONFIGURATOR" --tools all --scope global
        ;;
esac

# Optional vulture install
echo ""
read -r -p "[?] Install optional 'vulture' package for unused code detection (used in --level full audits)? [y/N]: " inst_vulture
case "$inst_vulture" in
    [Yy]*)
        if command -v uv >/dev/null 2>&1; then
            uv tool install vulture || echo "[!] Could not install vulture automatically."
        else
            pip install vulture || echo "[!] Could not install vulture automatically."
        fi
        ;;
    *)
        echo "[=] Skipped vulture installation."
        ;;
esac

# Global terminal shortcuts
echo ""
read -r -p "[?] Install global shortcuts into ~/.local/bin? [Y/n]: " inst_shortcuts
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
echo "Setup finished. Selected AI tools configured."
