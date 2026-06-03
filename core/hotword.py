import logging
import threading

import sounddevice as sd

try:
    from openwakeword.model import Model as _OWWModel
    _HAVE_OWW = True
except ImportError:
    _OWWModel = None
    _HAVE_OWW = False

logger = logging.getLogger(__name__)


def _find_model_path() -> str | None:
    if not _HAVE_OWW:
        return None
    try:
        import openwakeword
        from pathlib import Path
        p = Path(openwakeword.__file__).parent / "resources" / "models" / "hey_jarvis_v0.1.onnx"
        return str(p) if p.exists() else None
    except Exception:
        return None


class HotwordDetector:
    def __init__(
        self,
        threshold: float = 0.5,
        sample_rate: int = 16000,
        chunk_size: int = 1280,
    ):
        self.threshold = threshold
        self.sample_rate = sample_rate
        self.chunk_size = chunk_size
        self._thread: threading.Thread | None = None
        self._stop_event = threading.Event()
        self._model = None
        self._on_detected = None

    def _load_model(self):
        if not _HAVE_OWW:
            logger.warning("openWakeWord not installed")
            self._model = None
            return
        model_path = _find_model_path()
        if model_path is None:
            logger.warning("hey_jarvis model file not found")
            self._model = None
            return
        try:
            self._model = _OWWModel(wakeword_model_paths=[model_path])
        except Exception as e:
            logger.warning("Failed to load openWakeWord model: %s", e)
            self._model = None

    def _audio_callback(self, indata, frames, time_info, status):
        if self._stop_event.is_set():
            raise sd.CallbackAbort
        audio_flat = indata.flatten()
        prediction = self._model.predict(audio_flat)
        for word, score in prediction.items():
            if score >= self.threshold:
                self._model.reset()
                if self._on_detected:
                    self._on_detected()
                break

    def _listen_loop(self):
        self._load_model()
        if self._model is None:
            logger.warning("Hotword detector disabled (model unavailable)")
            return

        try:
            with sd.InputStream(
                samplerate=self.sample_rate,
                channels=1,
                dtype="int16",
                blocksize=self.chunk_size,
                callback=self._audio_callback,
            ):
                self._stop_event.wait()
        except sd.CallbackAbort:
            pass
        except Exception as e:
            logger.warning("Hotword detector stream error: %s", e)

    def start(self, on_detected):
        self._on_detected = on_detected
        self._stop_event.clear()
        self._thread = threading.Thread(
            target=self._listen_loop,
            daemon=True,
        )
        self._thread.start()

    def stop(self):
        self._stop_event.set()

    def is_running(self):
        return self._thread is not None and self._thread.is_alive()
