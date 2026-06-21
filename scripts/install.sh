#!/usr/bin/env bash
set -euo pipefail

REPO_URL="https://github.com/m-awaisqasim/Cryp.git"
SERVICE_NAME="cryp"
SYSTEMD_DIR="$HOME/.config/systemd/user"
SERVICE_FILE="$SYSTEMD_DIR/$SERVICE_NAME.service"
BIN_DIR="$HOME/.local/bin"
CLI_SCRIPT="$BIN_DIR/cryp"

echo "=== Cryp CRYP Installer ==="

# ---- Resolve install directory ----
if [ -f "main.py" ] && [ -f "requirements.txt" ]; then
    CRYP_DIR="$(pwd)"
    echo "✓ Running from repo: $CRYP_DIR"
else
    CRYP_DIR="${CRYP_DIR:-$HOME/Cryp}"
    if [ ! -d "$CRYP_DIR" ]; then
        echo "Cloning Cryp to $CRYP_DIR ..."
        git clone "$REPO_URL" "$CRYP_DIR"
    else
        echo "✓ Found existing repo at $CRYP_DIR"
        if command -v git &>/dev/null; then
            echo "Pulling latest changes..."
            cd "$CRYP_DIR" && git pull 2>/dev/null || true
        fi
    fi
    cd "$CRYP_DIR"
fi

VENV_PYTHON="$CRYP_DIR/.venv/bin/python3"

# ---- 1. Create / verify Python venv ----
if [ ! -f "$VENV_PYTHON" ]; then
    echo "Creating Python virtual environment..."
    python3 -m venv "$CRYP_DIR/.venv"
    echo "✓ Virtual environment created"
fi

echo "Installing Python dependencies..."
"$VENV_PYTHON" -m pip install --quiet --upgrade pip
"$VENV_PYTHON" -m pip install --quiet -r "$CRYP_DIR/requirements.txt"
echo "✓ Dependencies installed"

# ---- 2. Create systemd user service directory ----
mkdir -p "$SYSTEMD_DIR"

# ---- 3. Write systemd service file ----
cat > "$SERVICE_FILE" << EOF
[Unit]
Description=Cryp — CRYP AI Assistant (Cry V2)
After=network.target

[Service]
Type=simple
WorkingDirectory=$CRYP_DIR
ExecStart=$VENV_PYTHON $CRYP_DIR/main.py
Restart=on-failure
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=default.target
EOF

echo "✓ Service file written: $SERVICE_FILE"

# ---- 4. Reload systemd and enable service ----
systemctl --user daemon-reload
systemctl --user enable "$SERVICE_NAME"
echo "✓ Service enabled (starts on login)"

# ---- 5. Create cryp CLI wrapper ----
mkdir -p "$BIN_DIR"
cat > "$CLI_SCRIPT" << 'CLIFILE'
#!/usr/bin/env bash
SERVICE="cryp"
case "${1:-}" in
  start)
    systemctl --user start "$SERVICE"
    echo "Cryp started"
    ;;
  stop)
    systemctl --user stop "$SERVICE"
    echo "Cryp stopped"
    ;;
  restart)
    systemctl --user restart "$SERVICE"
    echo "Cryp restarted"
    ;;
  status)
    if systemctl --user is-active --quiet "$SERVICE"; then
      echo "Cryp is running"
    else
      echo "Cryp is stopped"
    fi
    systemctl --user status "$SERVICE"
    ;;
  logs)
    n="${2:-}"
    if [ "$n" = "-n" ] && [ -n "${3:-}" ]; then
      journalctl --user -u "$SERVICE" -n "$3" --no-pager
    else
      journalctl --user -u "$SERVICE" -f --no-pager
    fi
    ;;
  enable)
    systemctl --user enable "$SERVICE"
    echo "Cryp will start automatically on login"
    ;;
  disable)
    systemctl --user disable "$SERVICE"
    echo "Cryp will no longer start automatically"
    ;;
  ""|help)
    echo "Cryp CRYP — Cry V2"
    echo ""
    echo "Usage: cryp <command>"
    echo ""
    echo "Commands:"
    echo "  start    Start Cryp service"
    echo "  stop     Stop Cryp service"
    echo "  restart  Restart Cryp service"
    echo "  status   Show service status"
    echo "  logs     Follow live logs (use -n N for last N lines)"
    echo "  enable   Enable auto-start on login"
    echo "  disable  Disable auto-start on login"
    echo "  help     Show this help"
    ;;
  *)
    echo "Unknown command: $1"
    echo "Usage: cryp {start|stop|restart|status|logs|enable|disable|help}"
    exit 1
    ;;
esac
CLIFILE
chmod +x "$CLI_SCRIPT"
echo "✓ CLI wrapper installed: $CLI_SCRIPT"

# ---- 6. Ensure ~/.local/bin is in PATH ----
if ! echo "$PATH" | grep -q "$BIN_DIR"; then
    echo ""
    echo "NOTE: Add to your ~/.bashrc or ~/.zshrc:"
    echo "  export PATH=\"\$HOME/.local/bin:\$PATH\""
fi

echo ""
echo "=== Installation Complete ==="
echo ""
echo "  cryp start    — start Cryp now"
echo "  cryp stop     — stop Cryp"
echo "  cryp status   — check if running"
echo "  cryp logs     — follow live logs"
echo "  cryp restart  — restart Cryp"
echo ""
echo "Cryp will auto-start on next login."
echo "To start now: cryp start"
