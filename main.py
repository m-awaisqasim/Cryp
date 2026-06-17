import asyncio
import atexit
import os
import re
import sys
import threading
import time
import traceback
import warnings
from collections import deque
from datetime import datetime
from pathlib import Path

from config.settings import GEMINI_API_KEY

warnings.filterwarnings(
    "ignore",
    message="Specified provider 'CUDAExecutionProvider' is not in available provider names",
    category=UserWarning,
)


def _reexec_with_local_venv() -> None:
    if getattr(sys, "frozen", False):
        return

    base_dir = Path(__file__).resolve().parent
    try:
        invoked_path = Path(sys.argv[0]).resolve()
    except Exception:
        return
    if invoked_path != Path(__file__).resolve():
        return

    if os.name == "nt":
        venv_python = base_dir / ".venv" / "Scripts" / "python.exe"
    else:
        venv_python = base_dir / ".venv" / "bin" / "python"

    if not venv_python.exists():
        return

    current = Path(sys.executable).resolve()
    target = venv_python.resolve()
    if current != target:
        os.execv(str(target), [str(target), *sys.argv])


_reexec_with_local_venv()

from core.cryp_live import CrypLive, get_logger
from core.ui_web import WebCrypUI as CrypUI
try:
    from dashboard.event_bus import DashboardEventBus
    from dashboard.server import start_dashboard
except ImportError:
    DashboardEventBus = None
    start_dashboard = None

log = get_logger(__name__)


def main():
    from core.logger import setup_logging
    from dashboard.server import set_ui, start_dashboard

    ui = CrypUI("face.png")

    event_bus = DashboardEventBus() if DashboardEventBus is not None else None
    setup_logging(event_bus=event_bus if DashboardEventBus is not None else None)

    set_ui(ui)
    if event_bus is not None and start_dashboard is not None:
        start_dashboard(event_bus)

    def runner():
        ui.wait_for_api_key()
        cryp = CrypLive(ui, event_bus=event_bus)
        try:
            asyncio.run(cryp.run())
        except KeyboardInterrupt:
            log.info("shutting_down")
        finally:
            if hasattr(cryp, '_hotword') and cryp._hotword and cryp._hotword.is_running():
                cryp._hotword.stop()
            sys.exit(0)

    threading.Thread(target=runner, daemon=True).start()
    import time
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        log.info("shutting_down")
        sys.exit(0)


if __name__ == "__main__":
    main()
