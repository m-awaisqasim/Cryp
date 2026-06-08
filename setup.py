import subprocess
import sys

from core.logger import get_logger

log = get_logger(__name__)

log.info("installing_requirements")
subprocess.run([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"], check=True)

log.info("skipping_playwright_download")
log.info("browser_automation_note")

log.info("setup_complete")

# Proactive Engine Configuration (all optional)
# PROACTIVE_PAUSE_SECONDS=5                     # Silence before proactive speech (default: 5)
# PROACTIVE_SUGGESTION_COOLDOWN=1800            # Min seconds between suggestions (default: 1800)
# PROACTIVE_PATTERN_SCAN_INTERVAL=3600          # Pattern scan interval (default: 3600)
# PROACTIVE_ANOMALY_COOLDOWN=1800               # Min seconds between anomaly alerts (default: 1800)
# PROACTIVE_BRIEFING_ENABLED=true               # Enable/disable daily briefing (default: true)