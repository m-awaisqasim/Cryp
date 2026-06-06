import threading
import time


class ConversationState:
    def __init__(self):
        self._lock = threading.Lock()
        self._is_active = False
        self._is_speaking = False
        self._last_audio_end = 0.0

    def set_active(self, active: bool):
        with self._lock:
            self._is_active = active

    @property
    def is_active(self) -> bool:
        with self._lock:
            return self._is_active

    def set_speaking(self, speaking: bool):
        with self._lock:
            self._is_speaking = speaking
            if not speaking:
                self._last_audio_end = time.time()

    @property
    def is_speaking(self) -> bool:
        with self._lock:
            return self._is_speaking

    @property
    def last_audio_end(self) -> float:
        with self._lock:
            return self._last_audio_end
