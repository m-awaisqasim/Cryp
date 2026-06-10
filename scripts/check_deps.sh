#!/usr/bin/env bash
# Run before install to verify all dependencies

CRYP_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VENV_PYTHON="$CRYP_DIR/.venv/bin/python3"

echo "=== Cryp Dependency Check ==="
PASS=0
FAIL=0

check() {
    local name="$1"
    local cmd="$2"
    if eval "$cmd" &>/dev/null; then
        echo "✓ $name"
        ((PASS++))
    else
        echo "✗ $name — MISSING"
        ((FAIL++))
    fi
}

check "Python 3.11+"     "python3 --version | grep -E '3\.(1[1-9]|[2-9][0-9])'"
check "Virtual env"      "[ -f '$VENV_PYTHON' ]"
check "xdotool"          "which xdotool"
check "xclip"            "which xclip"
check "systemd (user)"   "systemctl --user status 2>/dev/null || true"
check ".env exists"      "[ -f '$CRYP_DIR/.env' ]"
check "GEMINI_API_KEY"   "grep -q '^GEMINI_API_KEY=' '$CRYP_DIR/.env' 2>/dev/null"
check "openWakeWord"     "$VENV_PYTHON -c 'import openwakeword'"
check "PyQt6"            "$VENV_PYTHON -c 'import PyQt6'"
check "FastAPI"          "$VENV_PYTHON -c 'import fastapi'"
check "structlog"        "$VENV_PYTHON -c 'import structlog'"
check "psutil"           "$VENV_PYTHON -c 'import psutil'"
check "pyperclip"        "$VENV_PYTHON -c 'import pyperclip'"
check "playwright"       "$VENV_PYTHON -c 'import playwright'"
check "tenacity"         "$VENV_PYTHON -c 'import tenacity'"

echo ""
echo "Results: $PASS passed, $FAIL failed"
if [ $FAIL -gt 0 ]; then
    echo "Run: pip install -r requirements.txt"
    exit 1
else
    echo "All dependencies satisfied. Ready to install."
fi
