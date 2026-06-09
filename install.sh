#!/usr/bin/env bash
set -euo pipefail

CRYP_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SERVICE_NAME="cryp"
SYSTEMD_DIR="$HOME/.config/systemd/user"
SERVICE_FILE="$SYSTEMD_DIR/$SERVICE_NAME.service"
BIN_DIR="$HOME/.local/bin"
CLI_SCRIPT="$BIN_DIR/cryp"
VENV_DIR="$HOME/.local/share/cryp/venv"
VENV_PYTHON="$VENV_DIR/bin/python3"
CONFIG_DIR="$HOME/.config/cryp"

echo "=== Cryp Installer ==="
echo "Directory: $CRYP_DIR"

# Check dependencies
for cmd in python3 systemctl; do
    if ! command -v "$cmd" &> /dev/null; then
        echo "ERROR: $cmd not found. Install it first."
        exit 1
    fi
done

# Check Python venv module directly (most reliable method)
if ! python3 -c "import venv" &> /dev/null; then
    echo "ERROR: python3-venv module is not available."
    echo "Run: sudo apt install python3-venv"
    exit 1
fi

# Check pip module directly
if ! python3 -c "import pip" &> /dev/null; then
    echo "ERROR: python3-pip is not available."
    echo "Run: sudo apt install python3-pip"
    exit 1
fi
echo "Dependencies OK"

# Idempotency check
if [ -f "$SERVICE_FILE" ] || [ -f "$CLI_SCRIPT" ]; then
    echo "Cryp appears to be already installed."
    read -rp "Reinstall? (y/N) " REPLY
    if [[ ! "$REPLY" =~ ^[Yy]$ ]]; then
        echo "Aborted."
        exit 0
    fi
fi

# Create virtualenv
mkdir -p "$VENV_DIR"
python3 -m venv --upgrade-deps "$VENV_DIR"
echo "Virtualenv created: $VENV_DIR"

# Install Python dependencies
"$VENV_PYTHON" -m pip install -r "$CRYP_DIR/requirements.txt"
echo "Python dependencies installed"

# Create config directory
mkdir -p "$CONFIG_DIR"
if [ -f "$CRYP_DIR/config/api_keys.json" ]; then
    cp "$CRYP_DIR/config/api_keys.json" "$CONFIG_DIR/api_keys.json"
    echo "Config files copied to $CONFIG_DIR"
else
    echo "Config directory created at $CONFIG_DIR"
fi

# Create systemd user service directory
mkdir -p "$SYSTEMD_DIR"

# Write systemd service file
sed -e "s|__VENV_PYTHON__|$VENV_PYTHON|g" \
    -e "s|__CRYP_DIR__|$CRYP_DIR|g" \
    "$CRYP_DIR/cryp.service" > "$SERVICE_FILE"
echo "Service file written: $SERVICE_FILE"

systemctl --user daemon-reload
systemctl --user enable "$SERVICE_NAME"
echo "Service enabled (starts on login)"

# Create cryp CLI wrapper
mkdir -p "$BIN_DIR"
cat > "$CLI_SCRIPT" << 'CLIFILE'
#!/usr/bin/env bash
SERVICE="cryp"
case "${1:-}" in
    start)   systemctl --user start "$SERVICE" ;;
    stop)    systemctl --user stop "$SERVICE" ;;
    restart) systemctl --user restart "$SERVICE" ;;
    status)  systemctl --user status "$SERVICE" ;;
    logs)    journalctl --user -u "$SERVICE" -f --no-pager ;;
    enable)  systemctl --user enable "$SERVICE" ;;
    disable) systemctl --user disable "$SERVICE" ;;
    "")
        echo "Usage: cryp {start|stop|restart|status|logs|enable|disable}"
        exit 1
        ;;
    *)
        echo "Unknown command: $1"
        echo "Usage: cryp {start|stop|restart|status|logs|enable|disable}"
        exit 1
        ;;
esac
CLIFILE

chmod +x "$CLI_SCRIPT"
echo "CLI wrapper installed: $CLI_SCRIPT"

# Ensure ~/.local/bin is in PATH
if ! echo "$PATH" | grep -q "$BIN_DIR"; then
    echo ""
    echo "NOTE: Add to your ~/.bashrc or ~/.zshrc:"
    echo "  export PATH=\"\$HOME/.local/bin:\$PATH\""
fi

echo ""
echo "=== Installation Complete ==="
echo "Commands:"
echo "  cryp start    — start Cryp now"
echo "  cryp stop     — stop Cryp"
echo "  cryp status   — check if running"
echo "  cryp logs     — follow live logs"
echo "  cryp restart  — restart Cryp"
echo ""
echo "Cryp will auto-start on next login."
echo "To start now: cryp start"
