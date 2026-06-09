#!/usr/bin/env bash
set -euo pipefail

CRYP_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VENV_PYTHON="$CRYP_DIR/.venv/bin/python3"

echo "=== Checking Cryp Dependencies ==="

if ! command -v python3 &> /dev/null; then
    echo "python3 not found"
    exit 1
fi
echo "python3 found: $(python3 --version)"

if [ ! -f "$VENV_PYTHON" ]; then
    echo "Virtual environment not found at .venv/"
    echo "Run: python3 -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt"
    exit 1
fi
echo "Virtual environment found"

MISSING=()
for cmd in xdotool xclip pactl; do
    if ! command -v $cmd &> /dev/null; then
        MISSING+=($cmd)
    fi
done

if [ ${#MISSING[@]} -ne 0 ]; then
    echo "Missing system packages: ${MISSING[*]}"
    echo "Install with: sudo apt install ${MISSING[*]}"
else
    echo "System packages (xdotool, xclip, pactl) found"
fi

echo "Checking Python dependencies..."
$VENV_PYTHON -c "
import sys
missing = []
for pkg in ['google.genai', 'PyQt6', 'fastapi', 'uvicorn', 'structlog', 'psutil', 'openwakeword', 'tenacity', 'pyperclip']:
    try:
        __import__(pkg)
    except ImportError:
        missing.append(pkg)
if missing:
    print(f'Missing Python packages: {\" \".join(missing)}')
    sys.exit(1)
else:
    print('All Python dependencies installed')
"

echo ""
echo "=== Dependency Check Complete ==="
