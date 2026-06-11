#!/usr/bin/env bash
set -euo pipefail

SERVICE_NAME="cryp"
SYSTEMD_DIR="$HOME/.config/systemd/user"
SERVICE_FILE="$SYSTEMD_DIR/$SERVICE_NAME.service"
CLI_SCRIPT="$HOME/.local/bin/cryp"

echo "=== Cryp CRYP Uninstaller ==="

systemctl --user stop "$SERVICE_NAME" 2>/dev/null || true
systemctl --user disable "$SERVICE_NAME" 2>/dev/null || true

[ -f "$SERVICE_FILE" ] && rm "$SERVICE_FILE" \
    && echo "✓ Service file removed"
[ -f "$CLI_SCRIPT" ] && rm "$CLI_SCRIPT" \
    && echo "✓ CLI wrapper removed"

systemctl --user daemon-reload
echo "✓ Systemd reloaded"
echo ""
echo "=== Uninstall Complete ==="
echo "Cryp has been removed from auto-start."
