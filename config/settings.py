from pathlib import Path
from dotenv import load_dotenv
import os

_ENV_PATH = Path(__file__).parent.parent / ".env"
if not _ENV_PATH.exists():
    raise FileNotFoundError(
        f".env file not found at {_ENV_PATH}. "
        "Copy .env.example to .env and fill in your values."
    )
load_dotenv(_ENV_PATH)

GEMINI_API_KEY: str = os.environ.get("GEMINI_API_KEY", "")
if not GEMINI_API_KEY:
    raise ValueError(
        "GEMINI_API_KEY is not set in .env. "
        "Add: GEMINI_API_KEY=your_key_here"
    )
OS_SYSTEM: str = os.environ.get("OS_SYSTEM", "windows").lower()

CRYP_HOTWORD: bool = os.environ.get("CRYP_HOTWORD", "1") == "1"
CRYP_HOTWORD_THRESHOLD: float = float(os.environ.get("CRYP_HOTWORD_THRESHOLD", "0.5"))
CRYP_SILENCE_TIMEOUT: int = int(os.environ.get("CRYP_SILENCE_TIMEOUT", "300"))

PROACTIVE_BRIEFING_ENABLED: bool = os.environ.get("PROACTIVE_BRIEFING_ENABLED", "1") == "1"
PROACTIVE_PAUSE_SECONDS: int = int(os.environ.get("PROACTIVE_PAUSE_SECONDS", "5"))
PROACTIVE_SUGGESTION_COOLDOWN: int = int(os.environ.get("PROACTIVE_SUGGESTION_COOLDOWN", "1800"))
PROACTIVE_PATTERN_SCAN_INTERVAL: int = int(os.environ.get("PROACTIVE_PATTERN_SCAN_INTERVAL", "3600"))
PROACTIVE_ANOMALY_COOLDOWN: int = int(os.environ.get("PROACTIVE_ANOMALY_COOLDOWN", "1800"))

HEALTH_CHECK_INTERVAL: int = int(os.environ.get("HEALTH_CHECK_INTERVAL", "60"))
HEALTH_CPU_THRESHOLD: float = float(os.environ.get("HEALTH_CPU_THRESHOLD", "90"))
HEALTH_RAM_THRESHOLD: float = float(os.environ.get("HEALTH_RAM_THRESHOLD", "85"))
HEALTH_DISK_THRESHOLD: float = float(os.environ.get("HEALTH_DISK_THRESHOLD", "90"))
HEALTH_BATTERY_THRESHOLD: float = float(os.environ.get("HEALTH_BATTERY_THRESHOLD", "20"))
HEALTH_DEBOUNCE_SECONDS: int = int(os.environ.get("HEALTH_DEBOUNCE_SECONDS", "300"))

RETRY_MAX_ATTEMPTS: int = int(os.environ.get("RETRY_MAX_ATTEMPTS", "3"))
RETRY_BASE_DELAY: float = float(os.environ.get("RETRY_BASE_DELAY", "1.0"))
RETRY_JITTER: float = float(os.environ.get("RETRY_JITTER", "0.5"))
RETRY_MAX_DELAY: float = float(os.environ.get("RETRY_MAX_DELAY", "10.0"))

LOG_LEVEL: str = os.environ.get("LOG_LEVEL", "INFO")
DASHBOARD_PORT: int = int(os.environ.get("DASHBOARD_PORT", "7073"))
EPISODIC_RECENT_COUNT: int = int(os.environ.get("EPISODIC_RECENT_COUNT", "5"))
ENABLE_RECALL_TOOL: bool = os.environ.get("ENABLE_RECALL_TOOL", "0") == "1"
