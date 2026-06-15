import os


class WakeConfig:
    def __init__(self):
        self.enabled: bool = os.getenv("CRYP_HOTWORD", "1") == "1"
        self.threshold: float = float(os.getenv("CRYP_HOTWORD_THRESHOLD", "0.5"))
        self.wake_words: list = ["hey jarvis"]
        self.silence_timeout: float = float(os.getenv("CRYP_SILENCE_TIMEOUT", "10.0"))
