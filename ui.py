from __future__ import annotations

import math
import os
import platform
import queue
import random
import subprocess
import sys
import threading
import time
from pathlib import Path

from config.settings import GEMINI_API_KEY, OS_SYSTEM

import psutil

from PyQt6.QtCore import (
    QEasingCurve, QMimeData, QObject, QPointF, QRectF, QSize, Qt,
    QTimer, QUrl, pyqtSignal,
)
from PyQt6.QtGui import (
    QAction, QBrush, QColor, QDragEnterEvent, QDropEvent, QFont,
    QFontDatabase, QKeySequence, QLinearGradient, QPainter, QPainterPath,
    QPen, QPixmap, QRadialGradient, QShortcut,
)
from PyQt6.QtWidgets import (
    QApplication, QFileDialog, QFrame, QHBoxLayout, QLabel, QLineEdit,
    QMainWindow, QMenu, QPushButton, QScrollArea, QSizePolicy,
    QStyle, QSystemTrayIcon, QTextEdit, QVBoxLayout, QWidget,
    QProgressBar,
)

def _base_dir() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).parent
    return Path(__file__).resolve().parent

BASE_DIR   = _base_dir()
CONFIG_DIR = BASE_DIR / "config"

_DEFAULT_W, _DEFAULT_H = 980, 700
_MIN_W,     _MIN_H     = 820, 580
_LEFT_W  = 148
_RIGHT_W = 340

_OS = platform.system()  # "Windows" | "Darwin" | "Linux"


class C:
    BG        = "#00060a"
    BG_GRAD   = "#001018"
    PANEL     = "#010d14"
    PANEL2    = "#010f18"
    BORDER    = "#0d3347"
    BORDER_B  = "#1a5c7a"
    BORDER_A  = "#0f4060"
    PRI       = "#00d4ff"
    PRI_LIGHT = "#66e8ff"
    PRI_DIM   = "#007a99"
    PRI_GHO   = "#001f2e"
    ACC       = "#ff6b00"
    ACC_DIM   = "#993d00"
    ACC2      = "#ffcc00"
    ACC2_DIM  = "#997700"
    GREEN     = "#00ff88"
    GREEN_D   = "#00aa55"
    GREEN_DIM = "#005533"
    RED       = "#ff3355"
    RED_DIM   = "#991e33"
    MUTED_C   = "#ff3366"
    TEXT      = "#8ffcff"
    TEXT_DIM  = "#3a8a9a"
    TEXT_MED  = "#5ab8cc"
    WHITE     = "#d8f8ff"
    DARK      = "#000d14"
    BAR_BG    = "#011520"
    GLOW_PRI  = "#00d4ff20"
    GLOW_ACC  = "#ff6b0015"
    GLOW_GRN  = "#00ff8815"


def qcol(h: str, a: int = 255) -> QColor:
    c = QColor(h); c.setAlpha(a); return c

class _SysMetrics:
    def __init__(self):
        self.cpu  = 0.0
        self.mem  = 0.0
        self.net  = 0.0   
        self.gpu  = -1.0  
        self.tmp  = -1.0  
        self._lock = threading.Lock()
        self._last_net = psutil.net_io_counters()
        self._last_net_t = time.time()
        self._running = True
        t = threading.Thread(target=self._loop, daemon=True)
        t.start()

    def _loop(self):
        while self._running:
            try:
                self._update()
            except Exception:
                pass
            time.sleep(1.5)

    def _update(self):
        cpu = psutil.cpu_percent(interval=None)
        mem = psutil.virtual_memory().percent

        nc  = psutil.net_io_counters()
        now = time.time()
        dt  = now - self._last_net_t
        if dt > 0:
            sent = (nc.bytes_sent - self._last_net.bytes_sent) / dt
            recv = (nc.bytes_recv - self._last_net.bytes_recv) / dt
            net  = (sent + recv) / (1024 * 1024)
        else:
            net = 0.0
        self._last_net   = nc
        self._last_net_t = now

        gpu = self._get_gpu()

        tmp = self._get_temp()

        with self._lock:
            self.cpu = cpu
            self.mem = mem
            self.net = net
            self.gpu = gpu
            self.tmp = tmp

    def _get_gpu(self) -> float:
        # NVIDIA
        try:
            r = subprocess.run(
                ["nvidia-smi", "--query-gpu=utilization.gpu",
                 "--format=csv,noheader,nounits"],
                capture_output=True, text=True, timeout=2
            )
            if r.returncode == 0:
                vals = [float(v.strip()) for v in r.stdout.strip().split("\n") if v.strip()]
                if vals:
                    return sum(vals) / len(vals)
        except Exception:
            pass

        # AMD (Linux)
        if _OS == "Linux":
            try:
                r = subprocess.run(
                    ["rocm-smi", "--showuse", "--csv"],
                    capture_output=True, text=True, timeout=2
                )
                if r.returncode == 0:
                    for line in r.stdout.strip().split("\n"):
                        parts = line.split(",")
                        if len(parts) >= 2:
                            try:
                                return float(parts[1].strip().replace("%", ""))
                            except ValueError:
                                pass
            except Exception:
                pass

            # Intel GPU (Linux)
            try:
                r = subprocess.run(
                    ["intel_gpu_top", "-J", "-s", "500"],
                    capture_output=True, text=True, timeout=1
                )
                if r.returncode == 0 and "Render/3D" in r.stdout:
                    import re
                    m = re.search(r'"busy":\s*([\d.]+)', r.stdout)
                    if m:
                        return float(m.group(1))
            except Exception:
                pass

        # macOS — powermetrics (GPU Engine)
        if _OS == "Darwin":
            try:
                r = subprocess.run(
                    ["sudo", "-n", "powermetrics", "-n", "1", "-i", "500",
                     "--samplers", "gpu_power"],
                    capture_output=True, text=True, timeout=2
                )
                if r.returncode == 0 and "GPU" in r.stdout:
                    import re
                    m = re.search(r'GPU\s+Active:\s+([\d.]+)%', r.stdout)
                    if m:
                        return float(m.group(1))
            except Exception:
                pass

        return -1.0

    def _get_temp(self) -> float:
        try:
            temps = psutil.sensors_temperatures()
            candidates = ["coretemp", "k10temp", "cpu_thermal", "acpitz",
                          "cpu-thermal", "zenpower", "it8688"]
            for name in candidates:
                if name in temps:
                    entries = temps[name]
                    if entries:
                        return entries[0].current
            for entries in temps.values():
                if entries:
                    return entries[0].current
        except Exception:
            pass
        if _OS == "Darwin":
            try:
                r = subprocess.run(
                    ["osx-cpu-temp"], capture_output=True, text=True, timeout=2
                )
                if r.returncode == 0:
                    import re
                    m = re.search(r"([\d.]+)", r.stdout)
                    if m:
                        return float(m.group(1))
            except Exception:
                pass

        if _OS == "Windows":
            try:
                r = subprocess.run(
                    ["powershell", "-Command",
                     "(Get-WmiObject MSAcpi_ThermalZoneTemperature -Namespace root/wmi).CurrentTemperature"],
                    capture_output=True, text=True, timeout=3
                )
                if r.returncode == 0 and r.stdout.strip():
                    raw = float(r.stdout.strip().split("\n")[0])
                    return (raw / 10.0) - 273.15
            except Exception:
                pass

        return -1.0

    def snapshot(self) -> dict:
        with self._lock:
            return {
                "cpu": self.cpu,
                "mem": self.mem,
                "net": self.net,
                "gpu": self.gpu,
                "tmp": self.tmp,
            }


_metrics = _SysMetrics()

class AudioAnalyzer:
    def __init__(self):
        self._lock = threading.Lock()
        self._running = True
        self._queue: queue.Queue = queue.Queue(maxsize=120)
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
        import numpy as np
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


class HudCanvas(QWidget):
    def __init__(self, face_path: str, analyzer=None, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_OpaquePaintEvent)
        self.setMinimumSize(300, 300)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        self._analyzer   = analyzer
        self.muted       = False
        self.speaking    = False
        self.state       = "INITIALISING"

        self._tick       = 0
        self._scale      = 1.0
        self._tgt_scale  = 1.0
        self._halo       = 55.0
        self._tgt_halo   = 55.0
        self._last_t     = time.time()
        self._scan       = 0.0
        self._scan2      = 180.0
        self._rings      = [0.0, 120.0, 240.0]
        self._pulses: list[float] = [0.0, 50.0, 100.0]
        self._blink      = True
        self._blink_tick = 0
        self._particles: list[list[float]] = []
        self._data_bits: list[list[float]] = []
        self._sparkles: list[list[float]] = []
        self._face_px: QPixmap | None = None
        self._load_face(face_path)
        self._bg_grid_offset = 0.0
        self._glow_pulse = 0.0
        self._audio_fft: list[float] = [0.0] * 38
        self._audio_volume = 0.0
        self._beat = False
        self._beat_flash = 1.0
        self._sleep_t = 0.0
        self._target_sleep = False

        self._tmr = QTimer(self)
        self._tmr.timeout.connect(self._step)
        self._tmr.start(16)

    def set_sleeping(self, val: bool):
        self._target_sleep = val

    def _load_face(self, path: str):
        try:
            from PIL import Image, ImageDraw
            import io
            img = Image.open(path).convert("RGBA")
            sz  = min(img.size)
            img = img.resize((sz, sz), Image.Resampling.LANCZOS)
            mk  = Image.new("L", (sz, sz), 0)
            ImageDraw.Draw(mk).ellipse((2, 2, sz - 2, sz - 2), fill=255)
            img.putalpha(mk)
            buf = io.BytesIO()
            img.save(buf, format="PNG")
            px = QPixmap(); px.loadFromData(buf.getvalue())
            self._face_px = px
        except Exception:
            self._face_px = None

    def _step(self):
        self._tick += 1

        # smooth sleep transition
        SLEEP_RATE = 1.0 / 60
        if self._target_sleep and self._sleep_t < 1.0:
            self._sleep_t = min(1.0, self._sleep_t + SLEEP_RATE)
        elif not self._target_sleep and self._sleep_t > 0.0:
            self._sleep_t = max(0.0, self._sleep_t - SLEEP_RATE)
        sf = 1.0 - self._sleep_t  # 1 = fully awake, 0 = fully asleep

        now = time.time()
        dt_scale = (1.0 if self.speaking else 0.35) * (0.05 + 0.95 * sf)

        if now - self._last_t > (0.12 if self.speaking else 0.5):
            if self.speaking:
                self._tgt_scale = random.uniform(1.06, 1.14)
                self._tgt_halo  = random.uniform(155, 200)
            elif self.muted:
                self._tgt_scale = random.uniform(0.998, 1.002)
                self._tgt_halo  = random.uniform(15, 28)
            else:
                sine_mod = 1.0 + 0.06 * math.sin(self._tick * 0.025)
                self._tgt_scale = 1.002 * sine_mod
                self._tgt_halo  = random.uniform(50, 72) * sine_mod
            self._last_t = now

        # dim halo target when sleeping
        if self._sleep_t > 0:
            self._tgt_halo *= (1.0 - self._sleep_t * 0.7)

        sp = 0.38 if self.speaking else 0.15
        self._scale += (self._tgt_scale - self._scale) * sp
        self._halo  += (self._tgt_halo  - self._halo)  * sp

        speeds_base = [1.5, -1.1, 2.2] if self.speaking else [0.55, -0.35, 0.9]
        speeds = [s * (0.05 + 0.95 * sf) for s in speeds_base]
        for i, spd in enumerate(speeds):
            self._rings[i] = (self._rings[i] + spd) % 360

        scan_spd = (3.5 if self.speaking else 1.3) * (0.05 + 0.95 * sf)
        self._scan  = (self._scan  + scan_spd) % 360
        scan2_spd = (-2.4 if self.speaking else -0.75) * (0.05 + 0.95 * sf)
        self._scan2 = (self._scan2 + scan2_spd) % 360

        fw  = min(self.width(), self.height())
        lim = fw * 0.74
        spd = (4.8 if self.speaking else 2.0) * (0.05 + 0.95 * sf)
        self._pulses = [r + spd for r in self._pulses if r + spd < lim]
        pulse_prob = (0.09 if self.speaking else 0.025) * (0.05 + 0.95 * sf)
        if len(self._pulses) < 3 and random.random() < pulse_prob:
            self._pulses.append(0.0)

        glow_spd = (0.04 if self.speaking else 0.015) * (0.05 + 0.95 * sf)
        self._glow_pulse = (self._glow_pulse + glow_spd) % (2 * math.pi)

        # speaking particles (burst)
        if self.speaking and random.random() < 0.32 * (0.05 + 0.95 * sf):
            cx, cy = self.width() / 2, self.height() / 2
            ang = random.uniform(0, 2 * math.pi)
            r_s = fw * 0.28
            self._particles.append([
                cx + math.cos(ang) * r_s, cy + math.sin(ang) * r_s,
                math.cos(ang) * random.uniform(0.9, 2.4),
                math.sin(ang) * random.uniform(0.9, 2.4) - 0.4, 1.0,
            ])
        self._particles = [
            [p[0]+p[2], p[1]+p[3], p[2]*0.97, p[3]*0.97, p[4]-0.028]
            for p in self._particles if p[4] > 0
        ]

        # floating data bits (hex snippets) - always active
        data_prob = (0.04 if self.speaking else 0.015) * (0.05 + 0.95 * sf)
        if random.random() < data_prob:
            cx, cy = self.width() / 2, self.height() / 2
            ang = random.uniform(0, 2 * math.pi)
            dist = fw * random.uniform(0.3, 0.55)
            self._data_bits.append([
                cx + math.cos(ang) * dist,
                cy + math.sin(ang) * dist,
                math.cos(ang) * random.uniform(0.15, 0.4),
                math.sin(ang) * random.uniform(0.15, 0.4) - 0.1,
                1.0,
                random.choice(["0x", "A1", "7F", "E4", "1B", "FF", "3C", "D9", "8A", "52"]),
            ])
        self._data_bits = [
            [d[0]+d[2], d[1]+d[3], d[2]*0.99, d[3]*0.99-0.002, d[4]-0.006, d[5]]
            for d in self._data_bits if d[4] > 0
        ]

        # sparkles
        sparkle_prob = (0.08 if self.speaking else 0.03) * (0.05 + 0.95 * sf)
        if random.random() < sparkle_prob:
            W, H = self.width(), self.height()
            self._sparkles.append([
                random.uniform(0, W), random.uniform(0, H),
                random.uniform(-0.2, 0.2), random.uniform(-0.2, 0.2),
                1.0, random.uniform(1.5, 3.5),
            ])
        self._sparkles = [
            [s[0]+s[2], s[1]+s[3], s[2]*0.98, s[3]*0.98, s[4]-0.018, s[5]]
            for s in self._sparkles if s[4] > 0
        ]

        # audio FFT — poll analyzer every 4 ticks
        if self._analyzer and self._tick % 4 == 0:
            self._audio_fft = self._analyzer.get_spectrum()
            self._audio_volume = self._analyzer.get_volume()
            if self._analyzer.get_beat() and len(self._pulses) < 5:
                self._pulses.append(0.0)

        # beat flash decay
        self._beat_flash = max(0.5, self._beat_flash - 0.04)

        # voice volume drives halo when speaking
        if self.speaking and self._analyzer:
            vol = self._audio_volume
            self._tgt_halo = 100 + 100 * vol

        # animated background grid
        self._bg_grid_offset = (self._bg_grid_offset + 0.12) % 48

        # blink toggle
        self._blink_tick += 1
        if self._blink_tick >= 38:
            self._blink = not self._blink
            self._blink_tick = 0

        self.update()

    def paintEvent(self, _):
        try:
            p = QPainter(self)
            p.setRenderHint(QPainter.RenderHint.Antialiasing)
            p.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)

            W, H = self.width(), self.height()
            cx, cy = W / 2, H / 2
            fw = min(W, H)

            # radial background gradient
            bg_rad = QRadialGradient(cx, cy, fw * 0.7, cx, cy)
            bg_rad.setColorAt(0.0, qcol("#001824"))
            bg_rad.setColorAt(0.6, qcol(C.BG))
            bg_rad.setColorAt(1.0, qcol(C.BG))
            p.fillRect(self.rect(), QBrush(bg_rad))

            # animated grid dots with alpha pulse
            gp = qcol(C.PRI_GHO)
            gp_a = int(80 + 40 * math.sin(self._tick * 0.015))
            gp.setAlpha(gp_a)
            p.setPen(QPen(gp, 1))
            off = self._bg_grid_offset
            for x in range(int(-off) % 48, W, 48):
                for y in range(int(-off) % 48, H, 48):
                    dx = abs(x - cx)
                    dy = abs(y - cy)
                    if dx > fw * 0.55 or dy > fw * 0.55:
                        p.drawPoint(x, y)

            ring_color = C.MUTED_C if self.muted else C.PRI
            glow_pulse_val = 0.85 + 0.15 * math.sin(self._glow_pulse)
            r_face = fw * 0.31

            # halo glow with gradient
            for i in range(12):
                r   = r_face * (1.9 - i * 0.07)
                frc = 1.0 - i / 12
                a   = max(0, min(255, int(self._halo * 0.09 * frc * glow_pulse_val)))
                col = qcol(ring_color, a)
                p.setPen(QPen(col, 1.8 - i * 0.1)); p.setBrush(Qt.BrushStyle.NoBrush)
                p.drawEllipse(QRectF(cx - r, cy - r, r * 2, r * 2))

            # pulse rings with gradient
            for pr in self._pulses:
                a   = max(0, int(230 * (1.0 - pr / (fw * 0.74))))
                col = qcol(ring_color, a)
                pen = QPen(col, 1.8)
                p.setPen(pen); p.setBrush(Qt.BrushStyle.NoBrush)
                p.drawEllipse(QRectF(cx - pr, cy - pr, pr * 2, pr * 2))

            # spinning arc rings with varied thickness
            bf = self._beat_flash
            for idx, (r_frac, w_r, arc_l, gap) in enumerate(
                [(0.50, 3.5, 120, 75), (0.42, 2.5, 82, 53), (0.34, 1.5, 60, 38)]
            ):
                ring_r = fw * r_frac
                base   = self._rings[idx]
                a_val  = max(0, min(255, int(self._halo * (1.0 - idx * 0.18) * glow_pulse_val * bf)))
                col    = qcol(ring_color, a_val)
                p.setPen(QPen(col, w_r * bf)); p.setBrush(Qt.BrushStyle.NoBrush)
                angle = base
                rect  = QRectF(cx - ring_r, cy - ring_r, ring_r * 2, ring_r * 2)
                while angle < base + 360:
                    p.drawArc(rect, int(angle * 16), int(arc_l * 16))
                    angle += arc_l + gap

            # scanner arcs with glow trail
            sr = fw * 0.52
            sa = min(255, int(self._halo * 1.6 * glow_pulse_val))
            ex = 80 if self.speaking else 44
            scan_color = C.MUTED_C if self.muted else C.PRI
            srect = QRectF(cx - sr, cy - sr, sr * 2, sr * 2)

            # trail behind primary scanner
            for ti in range(3, 0, -1):
                trail_a = sa // (ti * 3)
                trail_w = 2.5 - ti * 0.4
                if trail_a > 5 and trail_w > 0.5:
                    p.setPen(QPen(qcol(scan_color, trail_a), trail_w))
                    p.setBrush(Qt.BrushStyle.NoBrush)
                    p.drawArc(srect, int((self._scan - ti * 8) * 16), int(ex * 16))

            p.setPen(QPen(qcol(scan_color, sa), 3.0))
            p.setBrush(Qt.BrushStyle.NoBrush)
            p.drawArc(srect, int(self._scan * 16), int(ex * 16))
            p.setPen(QPen(qcol(C.ACC, sa // 2), 1.8))
            p.drawArc(srect, int(self._scan2 * 16), int(ex * 16))

            # tick marks animated
            t_out, t_in = fw * 0.508, fw * 0.483
            for deg in range(0, 360, 5):
                rad = math.radians(deg)
                if deg % 30 == 0:
                    tick_col = qcol(C.PRI_LIGHT if not self.muted else C.MUTED_C, 180)
                    t_w = 1.8
                    inn = t_in
                elif deg % 15 == 0:
                    tick_col = qcol(C.PRI if not self.muted else C.MUTED_C, 120)
                    t_w = 1.3
                    inn = t_in + 4
                else:
                    tick_col = qcol(C.PRI_DIM if not self.muted else "#661933", 80)
                    t_w = 1.0
                    inn = t_in + 8
                p.setPen(QPen(tick_col, t_w))
                p.drawLine(
                    QPointF(cx + t_out * math.cos(rad), cy - t_out * math.sin(rad)),
                    QPointF(cx + inn  * math.cos(rad), cy - inn  * math.sin(rad)),
                )

            # crosshair with glow
            ch_r, gap_h = fw * 0.52, fw * 0.16
            ch_a = int(self._halo * 0.5 * glow_pulse_val)
            p.setPen(QPen(qcol(ring_color, ch_a), 1.2))
            p.drawLine(QPointF(cx - ch_r, cy), QPointF(cx - gap_h, cy))
            p.drawLine(QPointF(cx + gap_h, cy), QPointF(cx + ch_r, cy))
            p.drawLine(QPointF(cx, cy - ch_r), QPointF(cx, cy - gap_h))
            p.drawLine(QPointF(cx, cy + gap_h), QPointF(cx, cy + ch_r))

            # corner brackets with glow
            bl = 26
            bc = qcol(ring_color, 210)
            hl, hr = cx - fw // 2, cx + fw // 2
            ht, hb = cy - fw // 2, cy + fw // 2
            p.setPen(QPen(bc, 2.5))
            for bx, by, dx, dy in [(hl,ht,1,1),(hr,ht,-1,1),(hl,hb,1,-1),(hr,hb,-1,-1)]:
                p.drawLine(QPointF(bx, by), QPointF(bx + dx * bl, by))
                p.drawLine(QPointF(bx, by), QPointF(bx, by + dy * bl))

            # face
            if self._face_px:
                fsz    = int(fw * 0.62 * self._scale)
                scaled = self._face_px.scaled(
                    fsz, fsz,
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation,
                )
                p.drawPixmap(int(cx - fsz / 2), int(cy - fsz / 2), scaled)
            else:
                orb_r = int(fw * 0.27 * self._scale)
                oc    = (200, 0, 50) if self.muted else (0, 60, 110)
                for i in range(8, 0, -1):
                    r2  = int(orb_r * i / 8)
                    frc = i / 8
                    a   = max(0, min(255, int(self._halo * 1.1 * frc)))
                    p.setBrush(QBrush(QColor(int(oc[0]*frc), int(oc[1]*frc), int(oc[2]*frc), a)))
                    p.setPen(Qt.PenStyle.NoPen)
                    p.drawEllipse(QRectF(cx - r2, cy - r2, r2 * 2, r2 * 2))
                p.setPen(QPen(qcol(C.PRI, min(255, int(self._halo * 2))), 1.5))
                p.setFont(QFont("Courier New", 14, QFont.Weight.Bold))
                p.drawText(QRectF(cx - 80, cy - 14, 160, 28),
                           Qt.AlignmentFlag.AlignCenter, "J.A.R.V.I.S")

            # particles
            for pt in self._particles:
                a = max(0, min(255, int(pt[4] * 255)))
                p.setPen(Qt.PenStyle.NoPen)
                p.setBrush(QBrush(qcol(ring_color, a)))
                p.drawEllipse(QPointF(pt[0], pt[1]), 2.5, 2.5)

            # data bits
            for d in self._data_bits:
                a = max(0, min(255, int(d[4] * 200)))
                p.setFont(QFont("Courier New", 7, QFont.Weight.Bold))
                p.setPen(QPen(qcol(ring_color, a), 1))
                p.drawText(QRectF(d[0] - 12, d[1] - 6, 24, 12),
                           Qt.AlignmentFlag.AlignCenter, d[5])

            # sparkles
            for s in self._sparkles:
                a = max(0, min(255, int(s[4] * 220)))
                p.setPen(Qt.PenStyle.NoPen)
                col = qcol(C.WHITE if random.random() > 0.5 else ring_color, a)
                p.setBrush(QBrush(col))
                sz_s = s[5] * s[4]
                p.drawEllipse(QPointF(s[0], s[1]), sz_s, sz_s)

            # status text with glow
            sy = cy + fw * 0.42
            if self.muted:
                txt, col = "⊘  MUTED",     qcol(C.MUTED_C)
            elif self.speaking:
                txt, col = "●  SPEAKING",  qcol(C.ACC)
            elif self.state == "THINKING":
                sym = "◈" if self._blink else "◇"
                txt, col = f"{sym}  THINKING",   qcol(C.ACC2)
            elif self.state == "PROCESSING":
                sym = "▷" if self._blink else "▶"
                txt, col = f"{sym}  PROCESSING", qcol(C.ACC2)
            elif self.state == "LISTENING":
                sym = "●" if self._blink else "○"
                txt, col = f"{sym}  LISTENING",  qcol(C.GREEN)
            else:
                sym = "●" if self._blink else "○"
                txt, col = f"{sym}  {self.state}", qcol(C.PRI)

            p.setPen(QPen(col, 1))
            p.setFont(QFont("Courier New", 11, QFont.Weight.Bold))
            p.drawText(QRectF(0, sy - 2, W, 26), Qt.AlignmentFlag.AlignCenter, txt)

            # circular waveform — radial bars around face
            N_circ = 36
            r_inner = fw * 0.33
            r_outer = fw * 0.47
            for i in range(N_circ):
                angle_rad = math.radians(i * (360 / N_circ) - 90)
                if self.speaking:
                    mag = min(1.0, self._audio_fft[i] * 1.5) if i < len(self._audio_fft) else 0.0
                elif self.muted:
                    mag = 0.01
                else:
                    mag = 0.04 + 0.02 * math.sin(self._tick * 0.05 + i * 0.4)
                bar_len = max(2, mag * (r_outer - r_inner))
                r_end = r_inner + bar_len
                x1 = cx + r_inner * math.cos(angle_rad)
                y1 = cy + r_inner * math.sin(angle_rad)
                x2 = cx + r_end * math.cos(angle_rad)
                y2 = cy + r_end * math.sin(angle_rad)
                if mag > 0.5:
                    cl = qcol(C.ACC, 200)
                elif mag > 0.25:
                    cl = qcol(C.PRI, 180)
                else:
                    cl = qcol(C.PRI_DIM, 100)
                p.setPen(QPen(cl, 2.5))
                p.drawLine(QPointF(x1, y1), QPointF(x2, y2))
        except Exception:
            pass

class MetricBar(QWidget):

    def __init__(self, label: str, color: str = C.PRI, parent=None):
        super().__init__(parent)
        self._label = label
        self._color = color
        self._value = 0.0
        self._display_value = 0.0
        self._text  = "--"
        self._prev_text = "--"
        self._text_flash = 0
        self.setFixedHeight(38)
        self.setMinimumWidth(80)

    def set_value(self, pct: float, text: str):
        self._value = max(0.0, min(100.0, pct))
        if text != self._text:
            self._prev_text = self._text
            self._text = text
            self._text_flash = 8

    def paintEvent(self, _):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        W, H = self.width(), self.height()

        # smooth animate display value toward target
        diff = self._value - self._display_value
        self._display_value += diff * 0.18
        if abs(diff) < 0.1:
            self._display_value = self._value
        dv = self._display_value

        p.setBrush(QBrush(qcol(C.PANEL2)))
        p.setPen(QPen(qcol(C.BORDER_A), 1))
        p.drawRoundedRect(QRectF(1, 1, W - 2, H - 2), 4, 4)

        bar_h   = 5
        bar_y   = H - bar_h - 5
        bar_w   = W - 14
        bar_x   = 7
        fill_w  = int(bar_w * dv / 100)

        # bar background
        p.setBrush(QBrush(qcol(C.BAR_BG)))
        p.setPen(Qt.PenStyle.NoPen)
        p.drawRoundedRect(QRectF(bar_x, bar_y, bar_w, bar_h), 2, 2)

        if dv > 85:
            bar_col = qcol(C.RED)
        elif dv > 65:
            bar_col = qcol(C.ACC)
        else:
            bar_col = qcol(self._color)

        # fill bar with subtle gradient effect
        if fill_w > 2:
            grad = QLinearGradient(bar_x, bar_y, bar_x + fill_w, bar_y)
            grad.setColorAt(0.0, bar_col)
            grad.setColorAt(1.0, QColor(bar_col.red(), bar_col.green(), bar_col.blue(), 200))
            p.setBrush(QBrush(grad))
            p.setPen(Qt.PenStyle.NoPen)
            p.drawRoundedRect(QRectF(bar_x, bar_y, fill_w, bar_h), 2, 2)

            # glow dot at end of bar
            if fill_w > 10 and dv > 10:
                glow_a = min(200, 60 + int(dv * 1.4))
                p.setBrush(QBrush(QColor(bar_col.red(), bar_col.green(), bar_col.blue(), glow_a)))
                p.setPen(Qt.PenStyle.NoPen)
                p.drawEllipse(QPointF(bar_x + fill_w, bar_y + bar_h / 2), bar_h * 0.8, bar_h * 0.8)

        if self._text_flash > 0:
            self._text_flash -= 1
            flash_col = qcol(C.WHITE, 200)
        else:
            flash_col = bar_col if self._text != "--" else qcol(C.TEXT_DIM)

        p.setFont(QFont("Courier New", 7, QFont.Weight.Bold))
        p.setPen(QPen(qcol(C.TEXT_DIM), 1))
        p.drawText(QRectF(8, 5, 50, 14), Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter, self._label)

        p.setFont(QFont("Courier New", 9, QFont.Weight.Bold))
        p.setPen(QPen(flash_col, 1))
        p.drawText(QRectF(0, 4, W - 6, 16), Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter, self._text)

class LogWidget(QTextEdit):
    _sig = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setReadOnly(True)
        self.setFont(QFont("Courier New", 9))
        self.setStyleSheet(f"""
            QTextEdit {{
                background: {C.PANEL};
                color: {C.TEXT};
                border: 1px solid {C.BORDER};
                border-radius: 6px;
                padding: 8px;
                selection-background-color: {C.PRI_GHO};
            }}
            QScrollBar:vertical {{
                background: {C.BG};
                width: 6px;
                border: none;
            }}
            QScrollBar::handle:vertical {{
                background: {C.BORDER_B};
                border-radius: 3px;
                min-height: 20px;
            }}
            QScrollBar::handle:vertical:hover {{
                background: {C.PRI_DIM};
            }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
                height: 0;
            }}
        """)
        self._queue: list[str] = []
        self._typing  = False
        self._text    = ""
        self._pos     = 0
        self._tag     = "sys"
        self._cursor_visible = True
        self._cursor_tick = 0
        self._tmr = QTimer(self)
        self._tmr.timeout.connect(self._step)
        self._cursor_tmr = QTimer(self)
        self._cursor_tmr.timeout.connect(self._blink_cursor)
        self._sig.connect(self._enqueue)

    def _blink_cursor(self):
        self._cursor_visible = not self._cursor_visible
        if self._typing:
            vp = self.viewport()
            if vp: vp.update()

    def append_log(self, text: str):
        self._sig.emit(text)

    def _enqueue(self, text: str):
        self._queue.append(text)
        if not self._typing:
            self._next()

    def _next(self):
        if not self._queue:
            self._typing = False
            self._cursor_tmr.stop()
            self._cursor_visible = False
            vp = self.viewport()
            if vp: vp.update()
            return
        self._typing = True
        self._text   = self._queue.pop(0)
        self._pos    = 0
        self._cursor_visible = True
        self._cursor_tmr.start(400)
        tl = self._text.lower()
        if   tl.startswith("you:"):    self._tag = "you"
        elif tl.startswith("jarvis:"): self._tag = "ai"
        elif tl.startswith("file:"):   self._tag = "file"
        elif "err" in tl:              self._tag = "err"
        else:                          self._tag = "sys"
        self._tmr.start(8)

    def _step(self):
        if self._pos < len(self._text):
            ch  = self._text[self._pos]
            cur = self.textCursor()
            fmt = cur.charFormat()
            col = {
                "you":  qcol(C.WHITE),
                "ai":   qcol(C.PRI),
                "err":  qcol(C.RED),
                "file": qcol(C.GREEN),
                "sys":  qcol(C.ACC2),
            }.get(self._tag, qcol(C.TEXT))
            fmt.setForeground(QBrush(col))
            cur.movePosition(cur.MoveOperation.End)
            cur.insertText(ch, fmt)
            self.setTextCursor(cur)
            self.ensureCursorVisible()
            self._pos += 1
        else:
            self._tmr.stop()
            cur = self.textCursor()
            cur.movePosition(cur.MoveOperation.End)
            cur.insertText("\n")
            self.setTextCursor(cur)
            self.ensureCursorVisible()
            QTimer.singleShot(30, self._next)

_FILE_ICONS = {
    "image":   ("🖼", "#00d4ff"), "video":   ("🎬", "#ff6b00"),
    "audio":   ("🎵", "#cc44ff"), "pdf":     ("📄", "#ff4444"),
    "word":    ("📝", "#4488ff"), "excel":   ("📊", "#44bb44"),
    "code":    ("💻", "#ffcc00"), "archive": ("📦", "#ff8844"),
    "pptx":    ("📊", "#ff6622"), "text":    ("📃", "#aaaaaa"),
    "data":    ("🔧", "#88ddff"), "unknown": ("📎", "#888888"),
}
_EXT_TO_CAT = {
    **dict.fromkeys(["jpg","jpeg","png","gif","webp","bmp","tiff","svg","ico"], "image"),
    **dict.fromkeys(["mp4","avi","mov","mkv","wmv","flv","webm","m4v"],         "video"),
    **dict.fromkeys(["mp3","wav","ogg","m4a","aac","flac","wma","opus"],        "audio"),
    **dict.fromkeys(["pdf"],                                                     "pdf"),
    **dict.fromkeys(["doc","docx"],                                              "word"),
    **dict.fromkeys(["xls","xlsx","ods"],                                        "excel"),
    **dict.fromkeys(["ppt","pptx"],                                              "pptx"),
    **dict.fromkeys(["py","js","ts","jsx","tsx","html","css","java","c","cpp",
                     "cs","go","rs","rb","php","swift","kt","sh","sql","lua"],   "code"),
    **dict.fromkeys(["zip","rar","tar","gz","7z","bz2","xz"],                   "archive"),
    **dict.fromkeys(["txt","md","rst","log"],                                    "text"),
    **dict.fromkeys(["csv","tsv","json","xml"],                                  "data"),
}

def _file_category(path: Path) -> str:
    return _EXT_TO_CAT.get(path.suffix.lower().lstrip("."), "unknown")

def _fmt_size(size: int) -> str:
    if   size < 1024:    return f"{size} B"
    elif size < 1024**2: return f"{size/1024:.1f} KB"
    elif size < 1024**3: return f"{size/1024**2:.1f} MB"
    else:                return f"{size/1024**3:.1f} GB"


class FileDropZone(QWidget):
    file_selected = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAcceptDrops(True)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFixedHeight(100)
        self._current_file: str | None = None
        self._hovering  = False
        self._drag_over = False
        self._dash_offset = 0.0
        self._bounce = 0.0
        self._pulse_glow = 0.0
        self._anim_tmr = QTimer(self)
        self._anim_tmr.timeout.connect(self._animate)
        self._anim_tmr.start(30)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        self._canvas = _DropCanvas(self)
        layout.addWidget(self._canvas)

    def _animate(self):
        self._dash_offset = (self._dash_offset + 1.2) % 24
        if self._hovering and not self._current_file:
            self._bounce = 1.0 + 0.06 * math.sin(time.time() * 4)
        else:
            self._bounce = 0.0
        self._pulse_glow = (self._pulse_glow + 0.04) % (2 * math.pi)
        self._canvas.update()

    def dragEnterEvent(self, e: QDragEnterEvent):
        md = e.mimeData()
        if md and md.hasUrls():
            e.acceptProposedAction()
            self._drag_over = True; self._canvas.update()

    def dragLeaveEvent(self, e):
        self._drag_over = False; self._canvas.update()

    def dropEvent(self, e: QDropEvent):
        self._drag_over = False
        md = e.mimeData()
        if md:
            urls = md.urls()
            if urls:
                path = urls[0].toLocalFile()
                if path and Path(path).is_file():
                    self._set_file(path)
        self._canvas.update()

    def mousePressEvent(self, e):
        if e.button() == Qt.MouseButton.LeftButton:
            self._browse()

    def enterEvent(self, e):
        self._hovering = True; self._canvas.update()

    def leaveEvent(self, e):
        self._hovering = False; self._bounce = 0.0; self._canvas.update()

    def current_file(self) -> str | None:
        return self._current_file

    def clear_file(self):
        self._current_file = None; self._canvas.update()

    def _browse(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Select a file for JARVIS", str(Path.home()),
            "All Files (*.*);;"
            "Images (*.jpg *.jpeg *.png *.gif *.webp *.bmp *.svg);;"
            "Documents (*.pdf *.docx *.txt *.md *.pptx);;"
            "Data (*.csv *.xlsx *.json *.xml);;"
            "Code (*.py *.js *.ts *.html *.css *.java *.cpp *.go);;"
            "Audio (*.mp3 *.wav *.ogg *.m4a *.aac *.flac);;"
            "Video (*.mp4 *.avi *.mov *.mkv *.wmv *.webm);;"
            "Archives (*.zip *.rar *.tar *.gz *.7z)",
        )
        if path:
            self._set_file(path)

    def _set_file(self, path: str):
        self._current_file = path
        self._canvas.update()
        self.file_selected.emit(path)


class _DropCanvas(QWidget):
    def __init__(self, zone: FileDropZone):
        super().__init__(zone)
        self._z = zone

    def paintEvent(self, _):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        z    = self._z
        W, H = self.width(), self.height()
        pad  = 6
        rect = QRectF(pad, pad, W - pad * 2, H - pad * 2)
        pulse = 0.85 + 0.15 * math.sin(z._pulse_glow)

        bg_col = qcol("#001a24" if z._drag_over else ("#001218" if z._hovering else C.PANEL))
        if z._drag_over:
            glow_a = int(60 * pulse)
            bg_col2 = qcol(C.PRI_GHO, glow_a)
            bg = QBrush(bg_col)
        else:
            bg = QBrush(bg_col)
        p.setBrush(bg); p.setPen(Qt.PenStyle.NoPen)
        p.drawRoundedRect(rect, 6, 6)

        if z._current_file:   border_col = qcol(C.GREEN, int(200 * pulse))
        elif z._drag_over:
            bc = qcol(C.PRI)
            border_col = QColor(bc.red(), bc.green(), bc.blue(), int(230 * pulse))
        elif z._hovering:     border_col = qcol(C.BORDER_B, int(200 * pulse))
        else:                 border_col = qcol(C.BORDER, 160)

        pen = QPen(border_col, 1.8 if z._drag_over else 1.5, Qt.PenStyle.DashLine)
        pen.setDashOffset(z._dash_offset)
        p.setPen(pen); p.setBrush(Qt.BrushStyle.NoBrush)

        # glow under border on drag
        if z._drag_over:
            glow_pen = QPen(qcol(C.PRI, int(40 * pulse)), 4)
            p.setPen(glow_pen)
            p.drawRoundedRect(rect, 6, 6)

        p.setPen(pen)
        p.drawRoundedRect(rect, 6, 6)

        if z._current_file:   self._paint_file(p, W, H, pulse)
        elif z._drag_over:    self._paint_drag_over(p, W, H, pulse)
        else:                 self._paint_idle(p, W, H, z._hovering, pulse)

    def _paint_idle(self, p, W, H, hover, pulse):
        cx, cy = W / 2, H / 2
        bounce = self._z._bounce if hover else 1.0
        col = qcol(C.PRI_DIM if not hover else C.PRI)
        col_a = int(180 * pulse) if not hover else 255
        col.setAlpha(col_a)
        p.setPen(QPen(col, int(2 * bounce))); p.setBrush(Qt.BrushStyle.NoBrush)
        # arrow icon with bounce
        arrow_y_off = -2 if hover else 0
        p.drawLine(QPointF(cx, cy - 14 + arrow_y_off), QPointF(cx, cy + 4 + arrow_y_off))
        p.drawLine(QPointF(cx - 8, cy - 6 + arrow_y_off), QPointF(cx, cy - 14 + arrow_y_off))
        p.drawLine(QPointF(cx + 8, cy - 6 + arrow_y_off), QPointF(cx, cy - 14 + arrow_y_off))
        p.drawLine(QPointF(cx - 14, cy + 4 + arrow_y_off), QPointF(cx + 14, cy + 4 + arrow_y_off))
        p.setFont(QFont("Courier New", 8))
        p.setPen(QPen(qcol(C.PRI_DIM if not hover else C.TEXT, int(200 * pulse)), 1))
        p.drawText(QRectF(0, cy + 8, W, 16), Qt.AlignmentFlag.AlignCenter,
                   "Drop file here  or  Click to Browse")
        p.setFont(QFont("Courier New", 7))
        p.setPen(QPen(qcol("#1a4a5a"), 1))
        p.drawText(QRectF(0, cy + 24, W, 14), Qt.AlignmentFlag.AlignCenter,
                   "Images · Video · Audio · PDF · Docs · Code · Data")

    def _paint_drag_over(self, p, W, H, pulse):
        cx, cy = W / 2, H / 2
        bounce = 1.0 + 0.1 * math.sin(time.time() * 6)
        p.setFont(QFont("Courier New", int(24 * bounce)))
        p.setPen(QPen(qcol(C.PRI, int(255 * pulse)), 1))
        p.drawText(QRectF(0, cy - 28, W, 36), Qt.AlignmentFlag.AlignCenter, "⬇")
        p.setFont(QFont("Courier New", 8, QFont.Weight.Bold))
        p.setPen(QPen(qcol(C.PRI, int(220 * pulse)), 1))
        p.drawText(QRectF(0, cy + 14, W, 18), Qt.AlignmentFlag.AlignCenter, "Release to load")

    def _paint_file(self, p, W, H, pulse):
        f = self._z._current_file
        if not f: return
        path = Path(f)
        cat  = _file_category(path)
        icon, icon_col = _FILE_ICONS.get(cat, _FILE_ICONS["unknown"])
        size_str = _fmt_size(path.stat().st_size)
        ext_str  = path.suffix.upper().lstrip(".") or "FILE"

        block_x, block_w = 10, 60
        p.setFont(QFont("Segoe UI Emoji", 22) if _OS == "Windows" else QFont("Arial", 22))
        p.setPen(QPen(qcol(icon_col, int(255 * pulse)), 1))
        p.drawText(QRectF(block_x, 0, block_w, H), Qt.AlignmentFlag.AlignCenter, icon)

        tx = block_x + block_w + 6
        tw = W - tx - 38

        p.setFont(QFont("Courier New", 8, QFont.Weight.Bold))
        p.setPen(QPen(qcol(C.WHITE, int(255 * pulse)), 1))
        name = path.name if len(path.name) <= 34 else path.name[:31] + "..."
        p.drawText(QRectF(tx, H * 0.18, tw, 16),
                   Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter, name)

        p.setFont(QFont("Courier New", 7))
        p.setPen(QPen(qcol(C.TEXT_DIM, int(200 * pulse)), 1))
        p.drawText(QRectF(tx, H * 0.18 + 18, tw, 14),
                   Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter,
                   f"{ext_str}  ·  {size_str}")

        p.setFont(QFont("Courier New", 6))
        p.setPen(QPen(qcol("#1e5c6a", int(180 * pulse)), 1))
        par = str(path.parent)
        if len(par) > 42: par = "…" + par[-41:]
        p.drawText(QRectF(tx, H * 0.18 + 34, tw, 12),
                   Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter, par)

        p.setFont(QFont("Courier New", 9, QFont.Weight.Bold))
        p.setPen(QPen(qcol(C.RED, int(180 * pulse)), 1))
        p.drawText(QRectF(W - 34, 0, 28, H), Qt.AlignmentFlag.AlignCenter, "✕")

    def mousePressEvent(self, e):
        z = self._z
        if z._current_file and e.pos().x() > self.width() - 34:
            z.clear_file()
        else:
            z.mousePressEvent(e)


class SetupOverlay(QWidget):
    done = pyqtSignal(str, str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self._glow_phase = 0.0
        self.setStyleSheet(f"""
            SetupOverlay {{
                background: qlineargradient(x1:0,y1:0,x2:1,y2:1,
                    stop:0 #010a10, stop:1 #00060a);
                border: 1px solid {C.BORDER_B};
                border-radius: 8px;
            }}
        """)

        detected = {"darwin": "mac", "windows": "windows"}.get(
            _OS.lower(), "linux"
        )
        self._sel_os = detected

        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 22, 30, 22)
        layout.setSpacing(8)

        def _lbl(txt, font_size=9, bold=False, color=C.PRI,
                 align=Qt.AlignmentFlag.AlignCenter):
            w = QLabel(txt)
            w.setAlignment(align)
            w.setFont(QFont("Courier New", font_size,
                            QFont.Weight.Bold if bold else QFont.Weight.Normal))
            w.setStyleSheet(f"color: {color}; background: transparent;")
            return w

        layout.addWidget(_lbl("◈  INITIALISATION REQUIRED", 13, True))
        layout.addWidget(_lbl("Configure J.A.R.V.I.S. before first boot.", 9, color=C.PRI_DIM))
        layout.addSpacing(6)

        sep = QFrame(); sep.setFrameShape(QFrame.Shape.HLine)
        sep.setStyleSheet(f"color: {C.BORDER_A};"); layout.addWidget(sep)
        layout.addSpacing(4)

        layout.addWidget(_lbl("GEMINI API KEY", 8, color=C.TEXT_DIM,
                               align=Qt.AlignmentFlag.AlignLeft))
        self._key_input = QLineEdit()
        self._key_input.setEchoMode(QLineEdit.EchoMode.Password)
        self._key_input.setPlaceholderText("AIza…")
        self._key_input.setFont(QFont("Courier New", 10))
        self._key_input.setFixedHeight(32)
        self._key_input.setStyleSheet(f"""
            QLineEdit {{
                background: #000d12; color: {C.TEXT};
                border: 1px solid {C.BORDER}; border-radius: 4px; padding: 4px 8px;
            }}
            QLineEdit:focus {{ border: 1px solid {C.PRI};
                background: #001118; }}
        """)
        layout.addWidget(self._key_input)
        layout.addSpacing(12)

        sep2 = QFrame(); sep2.setFrameShape(QFrame.Shape.HLine)
        sep2.setStyleSheet(f"color: {C.BORDER_A};"); layout.addWidget(sep2)
        layout.addSpacing(4)

        layout.addWidget(_lbl("OPERATING SYSTEM", 8, color=C.TEXT_DIM,
                               align=Qt.AlignmentFlag.AlignLeft))
        det_name = {"windows": "Windows", "mac": "macOS", "linux": "Linux"}[detected]
        det_lbl = _lbl(f"Auto-detected: {det_name}", 8, color=C.ACC2,
                        align=Qt.AlignmentFlag.AlignLeft)
        layout.addWidget(det_lbl)

        os_row = QHBoxLayout(); os_row.setSpacing(6)
        self._os_btns: dict[str, QPushButton] = {}
        for key, label in [("windows","⊞  Windows"),("mac","  macOS"),("linux","🐧  Linux")]:
            btn = QPushButton(label)
            btn.setFont(QFont("Courier New", 9, QFont.Weight.Bold))
            btn.setFixedHeight(34)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.clicked.connect(lambda _, k=key: self._sel(k))
            os_row.addWidget(btn)
            self._os_btns[key] = btn
        layout.addLayout(os_row)
        self._sel(detected)
        layout.addSpacing(12)

        self._init_btn = QPushButton("▸  INITIALISE SYSTEMS")
        self._init_btn.setFont(QFont("Courier New", 10, QFont.Weight.Bold))
        self._init_btn.setFixedHeight(36)
        self._init_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._update_init_btn_style()
        self._init_btn.clicked.connect(self._submit)
        layout.addWidget(self._init_btn)

        # subtle border glow animation
        self._glow_tmr = QTimer(self)
        self._glow_tmr.timeout.connect(self._tick_glow)
        self._glow_tmr.start(50)

    def _tick_glow(self):
        self._glow_phase = (self._glow_phase + 0.03) % (2 * math.pi)
        self._update_init_btn_style()

    def _update_init_btn_style(self):
        pulse = 0.7 + 0.3 * math.sin(self._glow_phase)
        r, g, b = 0, int(212 * pulse), 255
        border_c = QColor(r, g, b).name()
        bg_a = int(30 * pulse)
        self._init_btn.setStyleSheet(f"""
            QPushButton {{
                background: rgba({r}, {g}, {b}, {bg_a});
                color: {C.PRI};
                border: 1px solid {border_c}; border-radius: 4px;
            }}
            QPushButton:hover {{
                background: {C.PRI_GHO}; border: 1px solid {C.PRI_LIGHT};
            }}
        """)

    def _sel(self, key: str):
        self._sel_os = key
        pal = {"windows":(C.PRI,"#001a22"),"mac":(C.ACC2,"#1a1400"),"linux":(C.GREEN,"#001a0d")}
        for k, btn in self._os_btns.items():
            if k == key:
                fg, bg = pal[k]
                btn.setStyleSheet(f"""
                    QPushButton {{
                        background: {fg}; color: {bg};
                        border: none; border-radius: 4px; font-weight: bold;
                    }}
                """)
            else:
                btn.setStyleSheet(f"""
                    QPushButton {{
                        background: #000d12; color: {C.TEXT_DIM};
                        border: 1px solid {C.BORDER}; border-radius: 4px;
                    }}
                    QPushButton:hover {{ color: {C.TEXT}; border: 1px solid {C.BORDER_B}; }}
                """)

    def _submit(self):
        key = self._key_input.text().strip()
        if not key:
            self._key_input.setStyleSheet(
                self._key_input.styleSheet() +
                f" QLineEdit {{ border: 1px solid {C.RED}; }}"
            )
            return
        self.done.emit(key, self._sel_os)


class MainWindow(QMainWindow):
    _log_sig   = pyqtSignal(str)
    _state_sig = pyqtSignal(str)

    def __init__(self, face_path: str, analyzer=None):
        super().__init__()
        self.setWindowTitle(" ")
        self.setMinimumSize(_MIN_W, _MIN_H)
        self.resize(_DEFAULT_W, _DEFAULT_H)

        screen = QApplication.primaryScreen()
        if screen:
            sg = screen.availableGeometry()
            self.move(
                (sg.width()  - _DEFAULT_W) // 2,
                (sg.height() - _DEFAULT_H) // 2,
        )

        self.on_text_command  = None
        self.on_wake_request  = None
        self._muted           = False
        self._current_file: str | None = None

        central = QWidget()
        central.setStyleSheet(f"background: {C.BG};")
        self.setCentralWidget(central)

        root = QVBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)
        root.addWidget(self._build_header())

        body = QHBoxLayout()
        body.setContentsMargins(0, 0, 0, 0)
        body.setSpacing(0)

        self._left_panel = self._build_left_panel()
        body.addWidget(self._left_panel, stretch=0)

        self.hud = HudCanvas(face_path, analyzer=analyzer)
        self.hud.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        body.addWidget(self.hud, stretch=5)

        self._right_panel = self._build_right_panel()
        body.addWidget(self._right_panel, stretch=0)

        root.addLayout(body, stretch=1)
        root.addWidget(self._build_footer())

        self._clock_tmr = QTimer(self)
        self._clock_tmr.timeout.connect(self._tick_clock)
        self._clock_tmr.start(1000)
        self._tick_clock()

        # Metrik güncelleme timer'ı
        self._metric_tmr = QTimer(self)
        self._metric_tmr.timeout.connect(self._update_metrics)
        self._metric_tmr.start(2000)
        self._update_metrics()

        self._log_sig.connect(self._log.append_log)
        self._state_sig.connect(self._apply_state)

        self._overlay: SetupOverlay | None = None
        self._ready = self._check_config()
        if not self._ready:
            self._show_setup()

        sc_mute = QShortcut(QKeySequence("F4"), self)
        sc_mute.activated.connect(self._toggle_mute)
        sc_full = QShortcut(QKeySequence("F11"), self)
        sc_full.activated.connect(self._toggle_fullscreen)
        sc_min = QShortcut(QKeySequence("F12"), self)
        sc_min.activated.connect(self._minimize_to_tray)
        self._setup_tray()
        self._supports_opacity = QApplication.platformName() not in ("wayland",)

    def _set_opacity(self, val: float):
        if self._supports_opacity:
            self.setWindowOpacity(val)

    def _toggle_fullscreen(self):
        if self.isFullScreen():
            self.showNormal()
        else:
            self.showFullScreen()

    def _setup_tray(self):
        self._tray_icon = QSystemTrayIcon(self)
        style = self.style()
        icon = style.standardIcon(QStyle.StandardPixmap.SP_ComputerIcon) if style else QApplication.style().standardIcon(QStyle.StandardPixmap.SP_ComputerIcon)
        self._tray_icon.setIcon(icon)
        self._tray_icon.setToolTip(" ")
        menu = QMenu()
        show_act = QAction("Show JARVIS", self)
        show_act.triggered.connect(self._restore_from_tray)
        menu.addAction(show_act)
        menu.addSeparator()
        quit_act = QAction("Quit", self)
        quit_act.triggered.connect(QApplication.quit)
        menu.addAction(quit_act)
        self._tray_icon.setContextMenu(menu)
        self._tray_icon.activated.connect(
            lambda r: self._restore_from_tray()
            if r == QSystemTrayIcon.ActivationReason.DoubleClick
            else None
        )

    def closeEvent(self, event):
        event.ignore()
        if hasattr(self, '_opacity_tmr') and self._opacity_tmr.isActive():
            self._opacity_tmr.stop()
        if hasattr(self, '_min_tmr') and self._min_tmr.isActive():
            self._min_tmr.stop()
        self._close_phase = 0
        self._close_tmr = QTimer(self)
        self._close_tmr.timeout.connect(self._tick_close)
        self._close_tmr.start(16)

    def _tick_close(self):
        self._close_phase += 1
        p = self._close_phase / 30
        if p >= 1.0:
            self._close_tmr.stop()
            QApplication.quit()
        else:
            self._set_opacity(1.0 - p)
            g = self.geometry()
            cx, cy = g.x() + g.width() / 2, g.y() + g.height() / 2
            sc = 1.0 - p * 0.3
            nw, nh = int(g.width() * sc), int(g.height() * sc)
            self.setGeometry(int(cx - nw / 2), int(cy - nh / 2), nw, nh)

    def _minimize_to_tray(self):
        if hasattr(self, '_opacity_tmr') and self._opacity_tmr.isActive():
            self._opacity_tmr.stop()
        if hasattr(self, '_close_tmr') and self._close_tmr.isActive():
            self._close_tmr.stop()
        self._min_phase = 0
        self._min_tmr = QTimer(self)
        self._min_tmr.timeout.connect(self._tick_minimize)
        self._min_tmr.start(16)

    def _tick_minimize(self):
        self._min_phase += 1
        p = self._min_phase / 20
        if p >= 1.0:
            self._min_tmr.stop()
            self.hide()
            if hasattr(self, '_tray_icon') and self._tray_icon:
                self._tray_icon.show()
        else:
            self._set_opacity(1.0 - p * 0.5)
            g = self.geometry()
            cx, cy = g.x() + g.width() / 2, g.y() + g.height() / 2
            sc = 1.0 - p * 0.5
            nw, nh = int(g.width() * sc), int(g.height() * sc)
            self.setGeometry(int(cx - nw / 2), int(cy - nh / 2), nw, nh)

    def _restore_from_tray(self):
        if hasattr(self, '_min_tmr') and self._min_tmr.isActive():
            self._min_tmr.stop()
        if hasattr(self, '_close_tmr') and self._close_tmr.isActive():
            self._close_tmr.stop()
        if hasattr(self, '_tray_icon') and self._tray_icon:
            self._tray_icon.hide()
        self.showNormal()
        self.activateWindow()
        self._set_opacity(1.0)
        self.resize(_DEFAULT_W, _DEFAULT_H)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if self._overlay and self._overlay.isVisible():
            ow, oh = 460, 390
            cw = self.centralWidget()
            if cw:
                self._overlay.setGeometry(
                    (cw.width()  - ow) // 2,
                    (cw.height() - oh) // 2,
                    ow, oh,
                )

    def _update_metrics(self):
        snap = _metrics.snapshot()

        # CPU
        cpu = snap["cpu"]
        self._bar_cpu.set_value(cpu, f"{cpu:.0f}%")

        # MEM
        mem = snap["mem"]
        self._bar_mem.set_value(mem, f"{mem:.0f}%")

        # NET
        net = snap["net"]
        if net < 1.0:
            net_str = f"{net*1024:.0f}KB/s"
        else:
            net_str = f"{net:.1f}MB/s"
        net_pct = min(100, net * 10)  # 10 MB/s = %100
        self._bar_net.set_value(net_pct, net_str)

        # GPU
        gpu = snap["gpu"]
        if gpu >= 0:
            self._bar_gpu.set_value(gpu, f"{gpu:.0f}%")
        else:
            self._bar_gpu.set_value(0, "N/A")

        # TMP
        tmp = snap["tmp"]
        if tmp >= 0:
            tmp_pct = min(100, (tmp / 100) * 100)
            self._bar_tmp.set_value(tmp_pct, f"{tmp:.0f}°C")
        else:
            self._bar_tmp.set_value(0, "N/A")

        try:
            boot_t  = psutil.boot_time()
            elapsed = time.time() - boot_t
            h = int(elapsed // 3600)
            m = int((elapsed % 3600) // 60)
            self._uptime_lbl.setText(f"UP  {h:02d}:{m:02d}")
        except Exception:
            self._uptime_lbl.setText("UP  --:--")

        try:
            proc_count = len(psutil.pids())
            self._proc_lbl.setText(f"PROC  {proc_count}")
        except Exception:
            self._proc_lbl.setText("PROC  --")


    def _build_header(self) -> QWidget:
        w = QWidget()
        w.setFixedHeight(56)
        w.setStyleSheet(f"""
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 #011520, stop:1 {C.DARK});
            border-bottom: 1px solid {C.BORDER_B};
        """)
        lay = QHBoxLayout(w)
        lay.setContentsMargins(16, 0, 16, 0)

        # glowy status dot
        self._status_dot = QLabel("●")
        self._status_dot.setFont(QFont("Courier New", 10))
        self._status_dot.setStyleSheet(f"color: {C.GREEN}; background: transparent;")
        lay.addWidget(self._status_dot)

        def _badge(txt, color=C.TEXT_MED):
            l = QLabel(txt)
            l.setFont(QFont("Courier New", 8))
            l.setStyleSheet(f"color: {color}; background: transparent;")
            return l

        lay.addSpacing(4)
        lay.addWidget(_badge("Cryp v2", C.PRI_DIM))
        lay.addStretch()

        mid = QVBoxLayout(); mid.setSpacing(1)
        self._title_lbl = QLabel("J.A.R.V.I.S")
        self._title_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._title_lbl.setFont(QFont("Courier New", 17, QFont.Weight.Bold))
        self._title_lbl.setStyleSheet(f"color: {C.PRI}; background: transparent;")
        mid.addWidget(self._title_lbl)
        sub = QLabel("Just A Rather Very Intelligent System")
        sub.setAlignment(Qt.AlignmentFlag.AlignCenter)
        sub.setFont(QFont("Courier New", 7))
        sub.setStyleSheet(f"color: {C.PRI_DIM}; background: transparent;")
        mid.addWidget(sub)
        lay.addLayout(mid)
        lay.addStretch()

        right_col = QVBoxLayout(); right_col.setSpacing(2)
        self._clock_lbl = QLabel("00:00:00")
        self._clock_lbl.setFont(QFont("Courier New", 14, QFont.Weight.Bold))
        self._clock_lbl.setStyleSheet(f"color: {C.PRI}; background: transparent;")
        self._clock_lbl.setAlignment(Qt.AlignmentFlag.AlignRight)
        right_col.addWidget(self._clock_lbl)
        self._date_lbl = QLabel("")
        self._date_lbl.setFont(QFont("Courier New", 7))
        self._date_lbl.setStyleSheet(f"color: {C.TEXT_DIM}; background: transparent;")
        self._date_lbl.setAlignment(Qt.AlignmentFlag.AlignRight)
        right_col.addWidget(self._date_lbl)
        lay.addLayout(right_col)

        # animate status dot via timer
        self._header_tick = 0
        self._header_tmr = QTimer(self)
        self._header_tmr.timeout.connect(self._tick_header)
        self._header_tmr.start(600)
        return w

    def _tick_header(self):
        self._header_tick += 1
        if not hasattr(self, '_status_dot'):
            return
        pulse = 0.6 + 0.4 * math.sin(self._header_tick * 0.5)
        col = C.GREEN if not self._muted else C.MUTED_C
        self._status_dot.setStyleSheet(f"color: {col}; background: transparent;")
        # subtle title glow pulse
        glow = 180 + int(75 * pulse)
        self._title_lbl.setStyleSheet(
            f"color: qlineargradient(x1:0, y1:0, x2:1, y2:0, "
            f"stop:0 {C.PRI_DIM}, stop:0.5 {C.PRI}, stop:1 {C.PRI_DIM}); "
            f"background: transparent;"
        )

    def _tick_clock(self):
        now_str = time.strftime("%H:%M:%S")
        self._clock_lbl.setText(now_str)
        self._date_lbl.setText(time.strftime("%a %d %b %Y"))
        # pulse the colon for visual interest
        if int(time.time()) % 2 == 0:
            self._clock_lbl.setText(now_str.replace(":", " "))

    def _build_left_panel(self) -> QWidget:
        w = QWidget()
        w.setFixedWidth(_LEFT_W)
        w.setStyleSheet(f"""
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                stop:0 {C.DARK}, stop:0.8 #000b14, stop:1 {C.DARK});
            border-right: 1px solid {C.BORDER};
        """)
        lay = QVBoxLayout(w)
        lay.setContentsMargins(8, 10, 8, 10)
        lay.setSpacing(6)

        hdr = QLabel("◈ SYS MONITOR")
        hdr.setFont(QFont("Courier New", 7, QFont.Weight.Bold))
        hdr.setStyleSheet(f"color: {C.PRI}; background: transparent; "
                          f"border-bottom: 1px solid {C.BORDER}; padding-bottom: 4px;")
        lay.addWidget(hdr)
        lay.addSpacing(2)

        self._bar_cpu = MetricBar("CPU", C.PRI)
        self._bar_mem = MetricBar("MEM", C.ACC2)
        self._bar_net = MetricBar("NET", C.GREEN)
        self._bar_gpu = MetricBar("GPU", C.ACC)
        self._bar_tmp = MetricBar("TMP", "#ff6688")

        for bar in [self._bar_cpu, self._bar_mem, self._bar_net,
                    self._bar_gpu, self._bar_tmp]:
            lay.addWidget(bar)

        lay.addSpacing(4)

        info_panel = QWidget()
        info_panel.setStyleSheet(
            f"background: qlineargradient(x1:0,y1:0,x2:1,y2:1,"
            f"stop:0 #021018, stop:1 {C.PANEL2}); "
            f"border: 1px solid {C.BORDER_A}; border-radius: 5px;"
        )
        ip_lay = QVBoxLayout(info_panel)
        ip_lay.setContentsMargins(6, 5, 6, 5)
        ip_lay.setSpacing(3)

        self._uptime_lbl = QLabel("UP  --:--")
        self._uptime_lbl.setFont(QFont("Courier New", 8, QFont.Weight.Bold))
        self._uptime_lbl.setStyleSheet(f"color: {C.GREEN}; background: transparent; border: none;")
        ip_lay.addWidget(self._uptime_lbl)

        self._proc_lbl = QLabel("PROC  --")
        self._proc_lbl.setFont(QFont("Courier New", 8))
        self._proc_lbl.setStyleSheet(f"color: {C.TEXT_MED}; background: transparent; border: none;")
        ip_lay.addWidget(self._proc_lbl)

        os_name = {"Windows": "WIN", "Darwin": "macOS", "Linux": "LINUX"}.get(_OS, _OS.upper())
        os_lbl = QLabel(f"OS  {os_name}")
        os_lbl.setFont(QFont("Courier New", 8))
        os_lbl.setStyleSheet(f"color: {C.ACC2}; background: transparent; border: none;")
        ip_lay.addWidget(os_lbl)

        lay.addWidget(info_panel)
        lay.addStretch()

        for txt, col, glow_col in [
            ("AI CORE\nACTIVE",     C.GREEN,  C.GREEN_DIM),
            ("SEC\nCLEARED",        C.PRI,    C.PRI_GHO),
            ("PROTOCOL\nV2",   C.TEXT_DIM, "#000a14"),
        ]:
            lbl = QLabel(txt)
            lbl.setFont(QFont("Courier New", 7, QFont.Weight.Bold))
            lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            lbl.setStyleSheet(
                f"color: {col}; background: qlineargradient(x1:0,y1:0,x2:0,y2:1,"
                f"stop:0 {C.PANEL2}, stop:1 {glow_col}); "
                f"border: 1px solid {col}; border-radius: 4px; padding: 5px;"
            )
            lay.addWidget(lbl)

        return w
    def _build_right_panel(self) -> QWidget:
        w = QWidget()
        w.setFixedWidth(_RIGHT_W)
        w.setStyleSheet(f"""
            background: qlineargradient(x1:1, y1:0, x2:0, y2:0,
                stop:0 {C.DARK}, stop:0.8 #000b14, stop:1 {C.DARK});
            border-left: 1px solid {C.BORDER};
        """)
        lay = QVBoxLayout(w)
        lay.setContentsMargins(8, 8, 8, 8)
        lay.setSpacing(6)

        def _sec(txt):
            l = QLabel(f"▸ {txt}")
            l.setFont(QFont("Courier New", 7, QFont.Weight.Bold))
            l.setStyleSheet(f"color: {C.TEXT_MED}; background: transparent;")
            return l

        lay.addWidget(_sec("ACTIVITY LOG"))
        self._log = LogWidget()
        lay.addWidget(self._log, stretch=1)

        sep = QFrame(); sep.setFrameShape(QFrame.Shape.HLine)
        sep.setStyleSheet(f"color: {C.BORDER_A}; margin: 2px 0;")
        lay.addWidget(sep)

        lay.addWidget(_sec("FILE UPLOAD"))
        self._drop_zone = FileDropZone()
        self._drop_zone.file_selected.connect(self._on_file_selected)
        lay.addWidget(self._drop_zone)

        self._file_hint = QLabel("No file loaded — drop or click above to upload")
        self._file_hint.setFont(QFont("Courier New", 7))
        self._file_hint.setStyleSheet(f"color: {C.TEXT_MED}; background: transparent;")
        self._file_hint.setWordWrap(True)
        lay.addWidget(self._file_hint)

        sep2 = QFrame(); sep2.setFrameShape(QFrame.Shape.HLine)
        sep2.setStyleSheet(f"color: {C.BORDER_A}; margin: 2px 0;")
        lay.addWidget(sep2)

        lay.addWidget(_sec("COMMAND INPUT"))
        lay.addLayout(self._build_input_row())

        self._mute_btn = QPushButton("🎙  MICROPHONE ACTIVE")
        self._mute_btn.setFixedHeight(30)
        self._mute_btn.setFont(QFont("Courier New", 8, QFont.Weight.Bold))
        self._mute_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._mute_btn.clicked.connect(self._toggle_mute)
        self._style_mute_btn()
        lay.addWidget(self._mute_btn)

        self._wake_btn = QPushButton("🔊  WAKE JARVIS")
        self._wake_btn.setFixedHeight(26)
        self._wake_btn.setFont(QFont("Courier New", 7, QFont.Weight.Bold))
        self._wake_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._wake_btn.clicked.connect(self._click_wake)
        self._style_wake_btn()
        lay.addWidget(self._wake_btn)

        fs_btn = QPushButton("⛶  FULLSCREEN  [F11]")
        fs_btn.setFixedHeight(26)
        fs_btn.setFont(QFont("Courier New", 7))
        fs_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        fs_btn.setStyleSheet(f"""
            QPushButton {{
                background: transparent; color: {C.TEXT_MED};
                border: 1px solid {C.BORDER}; border-radius: 3px;
            }}
            QPushButton:hover {{
                color: {C.PRI}; border: 1px solid {C.PRI_DIM};
                background: {C.PRI_GHO};
            }}
        """)
        fs_btn.clicked.connect(self._toggle_fullscreen)
        lay.addWidget(fs_btn)

        return w

    def _build_input_row(self) -> QHBoxLayout:
        row = QHBoxLayout(); row.setSpacing(5)
        self._input = QLineEdit()
        self._input.setPlaceholderText("Type a command or question…")
        self._input.setFont(QFont("Courier New", 9))
        self._input.setFixedHeight(30)
        self._input.setStyleSheet(f"""
            QLineEdit {{
                background: #000d14; color: {C.WHITE};
                border: 1px solid {C.BORDER}; border-radius: 4px; padding: 3px 8px;
            }}
            QLineEdit:focus {{
                border: 1px solid {C.PRI};
                background: #001118;
            }}
        """)
        self._input.returnPressed.connect(self._send)
        row.addWidget(self._input)

        send = QPushButton("▸")
        send.setFixedSize(30, 30)
        send.setFont(QFont("Courier New", 11, QFont.Weight.Bold))
        send.setCursor(Qt.CursorShape.PointingHandCursor)
        send.setStyleSheet(f"""
            QPushButton {{
                background: {C.PRI_GHO}; color: {C.PRI};
                border: 1px solid {C.PRI_DIM}; border-radius: 4px;
            }}
            QPushButton:hover {{
                background: {C.PRI_DIM}; color: {C.BG};
                border: 1px solid {C.PRI};
            }}
            QPushButton:pressed {{
                background: {C.PRI}; color: {C.BG};
            }}
        """)
        send.clicked.connect(self._send)
        row.addWidget(send)
        return row

    def _build_footer(self) -> QWidget:
        w = QWidget()
        w.setFixedHeight(24)
        w.setStyleSheet(f"""
            background: qlineargradient(x1:0,y1:0,x2:0,y2:1,
                stop:0 {C.DARK}, stop:1 #00060a);
            border-top: 1px solid {C.BORDER_A};
        """)
        lay = QHBoxLayout(w); lay.setContentsMargins(14, 0, 14, 0)

        def _fl(txt, color=C.TEXT_MED):
            l = QLabel(txt); l.setFont(QFont("Courier New", 7))
            l.setStyleSheet(f"color: {color}; background: transparent;")
            return l

        lay.addWidget(_fl("[F4] Mute  ·  [F11] Fullscreen"))
        lay.addStretch()
        lay.addWidget(_fl("Awais Project  ·  Cryp v2  ·  CLASSIFIED", C.TEXT_DIM))
        lay.addStretch()
        lay.addWidget(_fl("© Cryp", C.PRI_DIM))
        return w

    def _on_file_selected(self, path: str):
        self._current_file = path
        p    = Path(path)
        cat  = _file_category(p)
        icon, _ = _FILE_ICONS.get(cat, _FILE_ICONS["unknown"])
        size = _fmt_size(p.stat().st_size)
        self._file_hint.setText(f"{icon}  {p.name}  ·  {size}  ·  Tell JARVIS what to do with it")
        self._log.append_log(f"FILE: {p.name} ({size}) loaded")
        if self.on_text_command:
            msg = (
                f"[FILE_UPLOADED] path={path} | name={p.name} | "
                f"type={p.suffix.lstrip('.')} | size={size} | "
                f"Briefly tell the user you can see the file '{p.name}' "
                f"({size}) has been uploaded and ask what they'd like to do with it."
            )
            threading.Thread(target=self.on_text_command, args=(msg,), daemon=True).start()

    def _toggle_mute(self):
        self._muted = not self._muted
        self.hud.muted = self._muted
        self._style_mute_btn()
        if self._muted:
            self._apply_state("MUTED")
            self._log.append_log("SYS: Microphone muted.")
        else:
            self._apply_state("LISTENING")
            self._log.append_log("SYS: Microphone active.")
        if hasattr(self, '_status_dot'):
            col = C.MUTED_C if self._muted else C.GREEN
            self._status_dot.setStyleSheet(f"color: {col}; background: transparent;")

    def _style_mute_btn(self):
        if self._muted:
            self._mute_btn.setText("🔇  MICROPHONE MUTED")
            self._mute_btn.setStyleSheet(f"""
                QPushButton {{
                    background: qlineargradient(x1:0,y1:0,x2:1,y2:1,
                        stop:0 #1a0008, stop:1 #140006);
                    color: {C.MUTED_C};
                    border: 1px solid {C.MUTED_C}; border-radius: 4px;
                }}
                QPushButton:hover {{
                    background: #22000a;
                    border: 1px solid {C.RED};
                }}
            """)
        else:
            self._mute_btn.setText("🎙  MICROPHONE ACTIVE")
            self._mute_btn.setStyleSheet(f"""
                QPushButton {{
                    background: qlineargradient(x1:0,y1:0,x2:1,y2:1,
                        stop:0 #001f0e, stop:1 #00140a);
                    color: {C.GREEN};
                    border: 1px solid {C.GREEN}; border-radius: 4px;
                }}
                QPushButton:hover {{
                    background: #002a14;
                    border: 1px solid {C.GREEN_D};
                }}
            """)

    def _click_wake(self):
        self._log.append_log("SYS: Manual wake requested.")
        if self.on_wake_request:
            threading.Thread(target=self.on_wake_request, daemon=True).start()

    def _style_wake_btn(self):
        self._wake_btn.setStyleSheet(f"""
            QPushButton {{
                background: qlineargradient(x1:0,y1:0,x2:1,y2:1,
                    stop:0 {C.PRI_GHO}, stop:1 #00122a);
                color: {C.PRI};
                border: 1px solid {C.PRI_DIM}; border-radius: 3px;
            }}
            QPushButton:hover {{
                background: qlineargradient(x1:0,y1:0,x2:1,y2:1,
                    stop:0 #002a44, stop:1 #001a33);
                border: 1px solid {C.PRI};
            }}
        """)

    def _send(self):
        txt = self._input.text().strip()
        if not txt: return
        self._input.clear()
        self._log.append_log(f"You: {txt}")
        if self.on_text_command:
            threading.Thread(target=self.on_text_command, args=(txt,), daemon=True).start()

    def _apply_state(self, state: str):
        self.hud.state    = state
        self.hud.speaking = (state == "SPEAKING")
        self.hud.set_sleeping(state == "SLEEPING")
        if not hasattr(self, '_opacity_tmr'):
            self._opacity_tmr = QTimer(self)
            self._opacity_tmr.timeout.connect(self._tick_opacity)
        self._opacity_target = 0.4 if state == "SLEEPING" else 1.0
        self._opacity_tmr.start(16)

    def _tick_opacity(self):
        if not self._supports_opacity:
            self._opacity_tmr.stop()
            return
        cur = self.windowOpacity()
        tgt = self._opacity_target
        diff = tgt - cur
        if abs(diff) < 0.01:
            self._set_opacity(tgt)
            self._opacity_tmr.stop()
        else:
            self._set_opacity(cur + diff * 0.06)

    def _check_config(self) -> bool:
        return bool(GEMINI_API_KEY) and bool(OS_SYSTEM)

    def _show_setup(self):
        cw = self.centralWidget()
        if not cw:
            return
        ov = SetupOverlay(cw)
        ow, oh = 460, 390
        ov.setGeometry(
            (cw.width()  - ow) // 2,
            (cw.height() - oh) // 2,
            ow, oh,
        )
        ov.done.connect(self._on_setup_done)
        ov.show()
        self._overlay = ov

    def _on_setup_done(self, key: str, os_name: str):
        env_path = BASE_DIR / ".env"
        env_path.write_text(
            f"GEMINI_API_KEY={key}\nOS_SYSTEM={os_name}\n",
            encoding="utf-8",
        )
        self._ready = True
        if self._overlay:
            self._overlay.hide()
            self._overlay = None
        self._apply_state("LISTENING")
        self._log.append_log(f"SYS: Initialised. OS={os_name.upper()}. JARVIS online.")

class _RootShim:
    def __init__(self, app: QApplication):
        self._app = app
    def mainloop(self):
        self._app.exec()
    def protocol(self, *_):
        pass


class JarvisUI:
    def __init__(self, face_path: str, size=None):
        app = QApplication.instance()
        self._app: QApplication = app if isinstance(app, QApplication) else QApplication(sys.argv)
        self._app.setStyle("Fusion")
        self.audio_analyzer = AudioAnalyzer()
        self._win = MainWindow(face_path, analyzer=self.audio_analyzer)
        self._win.show()
        self.root = _RootShim(self._app)

    @property
    def muted(self) -> bool:
        return self._win._muted

    @muted.setter
    def muted(self, v: bool):
        if v != self._win._muted:
            self._win._toggle_mute()

    @property
    def current_file(self) -> str | None:
        return self._win._drop_zone.current_file()

    @property
    def on_text_command(self):
        return self._win.on_text_command

    @on_text_command.setter
    def on_text_command(self, cb):
        self._win.on_text_command = cb

    @property
    def on_wake_request(self):
        return self._win.on_wake_request

    @on_wake_request.setter
    def on_wake_request(self, cb):
        self._win.on_wake_request = cb

    def set_state(self, state: str):
        self._win._state_sig.emit(state)

    def write_log(self, text: str):
        self._win._log_sig.emit(text)

    def wait_for_api_key(self):
        while not self._win._ready:
            time.sleep(0.1)

    def start_speaking(self):
        self.set_state("SPEAKING")

    def stop_speaking(self):
        if not self.muted:
            self.set_state("LISTENING")
