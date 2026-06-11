import asyncio
import json
import queue
import threading
import time
from pathlib import Path

try:
    import numpy as np
except ImportError:
    np = None


class AudioAnalyzer:
    def __init__(self):
        self._lock = threading.Lock()
        self._running = True
        self._queue = queue.Queue(maxsize=120)
        self._spectrum = [0.0] * 38
        self._volume = 0.0
        self._beat = False
        self._bass_hist = [0.0] * 43
        self._bass_idx = 0
        t = threading.Thread(target=self._loop, daemon=True)
        t.start()

    def feed(self, data):
        try:
            self._queue.put_nowait(data)
        except queue.Full:
            pass

    def _loop(self):
        if np is None:
            return
        buf = np.array([], dtype=np.int16)
        window = np.hanning(2048)
        sr = 16000
        fft_bins = np.fft.rfftfreq(2048, 1.0 / sr)
        num_bands = 38
        band_edges = np.logspace(np.log10(50), np.log10(4000), num_bands + 1)
        band_indices = [
            np.where((fft_bins >= band_edges[i]) & (fft_bins < band_edges[i + 1]))[0]
            for i in range(num_bands)
        ]
        while self._running:
            try:
                while True:
                    chunk = self._queue.get_nowait()
                    buf = np.append(buf, chunk)
            except queue.Empty:
                pass
            if len(buf) < 2048:
                time.sleep(0.01)
                continue
            data = buf[:2048].astype(np.float32)
            buf = buf[2048:]
            spec = np.abs(np.fft.rfft(data * window))
            binned = np.array([
                float(np.mean(spec[idx])) if len(idx) > 0 else 0.0
                for idx in band_indices
            ])
            mx = np.max(binned)
            if mx > 0:
                binned = binned / mx
            rms = float(np.sqrt(np.mean(data ** 2)))
            vol = min(1.0, rms / 5000.0)
            bass = float(np.mean(binned[:5]))
            self._bass_hist[self._bass_idx] = bass
            self._bass_idx = (self._bass_idx + 1) % len(self._bass_hist)
            avg_bass = float(np.mean(self._bass_hist))
            beat = bass > avg_bass * 1.5 and avg_bass > 0.05
            with self._lock:
                self._spectrum = binned.tolist()
                self._volume = vol
                self._beat = beat

    def get_spectrum(self):
        with self._lock:
            return list(self._spectrum)

    def get_volume(self):
        with self._lock:
            return self._volume

    def get_beat(self):
        with self._lock:
            return self._beat


class WebJarvisUI:
    """
    Drop-in replacement for PyQt6 JarvisUI.
    Same interface, routes everything to WebSocket.
    """

    def __init__(self, face_path=None, size=None):
        self._muted = False
        self._state = "idle"
        self._loop = None
        self._ws_clients = set()
        self.on_text_command = None
        self.current_file = None
        self._log_buffer = []
        self.audio_analyzer = AudioAnalyzer()

    @property
    def muted(self) -> bool:
        return self._muted

    @muted.setter
    def muted(self, value: bool):
        self._muted = value
        self._broadcast({"type": "mute", "value": value})

    def write_log(self, text: str) -> None:
        """Replaces PyQt6 LogWidget.append()"""
        entry = {"type": "transcript", "text": text}
        self._log_buffer.append(entry)
        if len(self._log_buffer) > 200:
            self._log_buffer = self._log_buffer[-200:]
        self._broadcast(entry)

    def set_state(self, state: str) -> None:
        """Replaces PyQt6 HudCanvas state change"""
        self._state = state
        self._broadcast({"type": "state", "state": state})

    def start_speaking(self) -> None:
        self.set_state("speaking")

    def stop_speaking(self) -> None:
        self.set_state("idle")

    def speak(self, text: str) -> None:
        self.write_log(f"Jarvis: {text}")

    def register_client(self, ws) -> None:
        self._ws_clients.add(ws)
        asyncio.create_task(ws.send_json({
            "type": "init",
            "state": self._state,
            "muted": self._muted,
            "log": self._log_buffer[-50:],
        }))

    def unregister_client(self, ws) -> None:
        self._ws_clients.discard(ws)

    def _broadcast(self, data: dict) -> None:
        if not self._ws_clients:
            return
        msg = json.dumps(data)
        dead = set()
        for ws in self._ws_clients.copy():
            try:
                asyncio.create_task(ws.send_text(msg))
            except Exception:
                dead.add(ws)
        self._ws_clients -= dead

    def set_event_loop(self, loop) -> None:
        self._loop = loop

    def show(self): pass
    def hide(self): pass
    def close(self): pass
    def update_metrics(self, *args): pass

    def wait_for_api_key(self):
        pass