import subprocess
import sys

print("Installing requirements...")
subprocess.run([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"], check=True)

print("Skipping Playwright browser download on unsupported hosts.")
print("If you need browser automation, use a system-installed browser on this OS.")

print("\nSetup complete! Run 'python main.py' to start Cryp.")

