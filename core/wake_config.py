import os


class WakeConfig:
    def __init__(self):
        self.enabled: bool = os.getenv("JARVIS_HOTWORD", "1") == "1"
        self.threshold: float = float(os.getenv("JARVIS_HOTWORD_THRESHOLD", "0.05"))
        self.wake_words: list = ["hey jarvis"]
        self.silence_timeout: float = float(os.getenv("JARVIS_SILENCE_TIMEOUT", "10.0"))
