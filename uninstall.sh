#!/usr/bin/env bash
set -euo pipefail

SERVICE_NAME="cryp"
SYSTEMD_DIR="$HOME/.config/systemd/user"
SERVICE_FILE="$SYSTEMD_DIR/$SERVICE_NAME.service"
CLI_SCRIPT="$HOME/.local/bin/cryp"
VENV_DIR="$HOME/.local/share/cryp/venv"
CONFIG_DIR="$HOME/.config/cryp"

echo "=== Cryp Uninstaller ==="

systemctl --user stop "$SERVICE_NAME" 2>/dev/null || true
systemctl --user disable "$SERVICE_NAME" 2>/dev/null || true
echo "Service stopped and disabled"

[ -f "$SERVICE_FILE" ] && rm "$SERVICE_FILE" && echo "Service file removed"
[ -f "$CLI_SCRIPT" ] && rm "$CLI_SCRIPT" && echo "CLI wrapper removed"

systemctl --user daemon-reload
echo "Systemd reloaded"

read -rp "Remove virtualenv at $VENV_DIR? (y/N) " REPLY
if [[ "$REPLY" =~ ^[Yy]$ ]]; then
    rm -rf "$VENV_DIR"
    echo "Virtualenv removed"
fi

read -rp "Remove config at $CONFIG_DIR? (y/N) " REPLY
if [[ "$REPLY" =~ ^[Yy]$ ]]; then
    rm -rf "$CONFIG_DIR"
    echo "Config removed"
fi

echo ""
echo "=== Uninstall Complete ==="
echo "Project source at $(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd) was not removed."
echo "To remove it manually: rm -rf that directory."
