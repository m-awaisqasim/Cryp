import subprocess
import sys

print("Installing requirements...")
subprocess.run([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"], check=True)

print("Skipping Playwright browser download on unsupported hosts.")
print("If you need browser automation, use a system-installed browser on this OS.")

print("\nSetup complete! Run 'python main.py' to start Cryp.")

# Proactive Engine Configuration (all optional)
# PROACTIVE_PAUSE_SECONDS=5                     # Silence before proactive speech (default: 5)
# PROACTIVE_SUGGESTION_COOLDOWN=1800            # Min seconds between suggestions (default: 1800)
# PROACTIVE_PATTERN_SCAN_INTERVAL=3600          # Pattern scan interval (default: 3600)
# PROACTIVE_ANOMALY_COOLDOWN=1800               # Min seconds between anomaly alerts (default: 1800)
# PROACTIVE_BRIEFING_ENABLED=true               # Enable/disable daily briefing (default: true)