import asyncio
import os
import time
from datetime import datetime, date
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from proactive.conversation_state import ConversationState
from proactive.queue import ProactiveQueue
from proactive.briefing import should_brief, generate_briefing
from proactive.patterns import run_pattern_scan
from proactive.anomalies import check_cpu_anomaly, check_ram_anomaly, check_app_anomaly
from proactive.suggestions import evaluate_suggestions
from core.context_collector import gather_proactive_context, get_active_window
from core.daemon import SystemHealthDaemon
from core.logger import get_logger

log = get_logger(__name__)

PAUSE_SECONDS = int(os.getenv("PROACTIVE_PAUSE_SECONDS", "5"))
PATTERN_SCAN_INTERVAL = int(os.getenv("PROACTIVE_PATTERN_SCAN_INTERVAL", "3600"))
SUGGESTION_COOLDOWN = int(os.getenv("PROACTIVE_SUGGESTION_COOLDOWN", "1800"))
ANOMALY_CHECK_INTERVAL = int(os.getenv("PROACTIVE_ANOMALY_CHECK_INTERVAL", "60"))


class ProactiveEngine:
    def __init__(
        self,
        conv_state: ConversationState,
        queue: ProactiveQueue,
        health_daemon: SystemHealthDaemon | None = None,
        speak_fn=None,
        write_log_fn=None,
    ):
        self._conv_state = conv_state
        self._queue = queue
        self._health = health_daemon
        self._speak_fn = speak_fn
        self._write_log_fn = write_log_fn
        self._last_pattern_scan = 0.0
        self._last_suggestion_check = 0.0
        self._last_anomaly_check = 0.0
        self._session_start = time.time()

    async def run(self):
        try:
            await self._initial_briefing()
            self._last_pattern_scan = time.time()
            while True:
                await asyncio.sleep(5)
                now = time.time()
                if now - self._last_pattern_scan >= PATTERN_SCAN_INTERVAL:
                    await self._do_pattern_scan()
                    self._last_pattern_scan = now
                if now - self._last_suggestion_check >= 60:
                    await self._check_suggestions()
                    self._last_suggestion_check = now
                if now - self._last_anomaly_check >= ANOMALY_CHECK_INTERVAL:
                    await self._check_anomalies()
                    self._last_anomaly_check = now
        except asyncio.CancelledError:
            log.info("engine_cancelled")
        except Exception as e:
            log.error("engine_error", exc_info=True)

    async def _initial_briefing(self):
        try:
            if not should_brief():
                return
            await asyncio.sleep(4)
            text = generate_briefing(health_daemon=self._health)
            if text and len(text) > 10:
                if self._speak_fn:
                    self._speak_fn(text)
                if self._write_log_fn:
                    self._write_log_fn(f"[PROACTIVE] {text}")
                log.info("briefing_spoken", preview=text[:60])
                from proactive.briefing import mark_briefed
                mark_briefed()
        except Exception as e:
            log.error("briefing_failed", exc_info=True)

    async def _do_pattern_scan(self):
        try:
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, run_pattern_scan)
        except Exception as e:
            log.error("pattern_scan_failed", exc_info=True)

    async def _check_suggestions(self):
        try:
            ctx = gather_proactive_context()
            ctx["active_window"] = get_active_window()
            suggestion = evaluate_suggestions(ctx)
            if suggestion:
                self._queue.put_nowait(suggestion)
                log.info("suggestion_queued", preview=suggestion[:60])
        except Exception as e:
            log.error("suggestion_check_failed", exc_info=True)

    async def _check_anomalies(self):
        try:
            if self._health is None:
                return
            snap = self._health.get_health_snapshot()
            if not snap:
                return
            from memory.memory_manager import load_patterns
            baseline = load_patterns().get("baseline", {})
            hour = datetime.now().strftime("%H:00")
            alerts = []
            cpu = snap.get("cpu_percent")
            if cpu is not None:
                cpu_bl = baseline.get(hour, {}) if isinstance(baseline, dict) else {}
                cpu_msg = check_cpu_anomaly(float(cpu), {"cpu_baseline": cpu_bl})
                if cpu_msg:
                    alerts.append(cpu_msg)
            ram = snap.get("ram_percent")
            if ram is not None:
                ram_bl = baseline.get(hour, {}) if isinstance(baseline, dict) else {}
                ram_msg = check_ram_anomaly(float(ram), {"ram_baseline": ram_bl})
                if ram_msg:
                    alerts.append(ram_msg)
            # TODO(app-anomaly): disabled — compute_baseline() tracks
            # tool usage (tools_used), not active window titles, so
            # "typical_app" here is a tool name like "browser_control"
            # while the live value is a window title like "Firefox".
            # These will essentially never match, so this would misfire
            # as a false anomaly almost every time it ran. Re-enable once
            # baseline tracks real window history — see
            # core/context_collector.py log_window_change /
            # get_daily_aggregation, which already collects this but
            # isn't wired into patterns.py yet.
            for msg in alerts:
                self._queue.put_nowait(msg)
                log.info("anomaly_queued", preview=msg[:60])
        except Exception as e:
            log.error("anomaly_check_failed", exc_info=True)
