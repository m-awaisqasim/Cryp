import json
import os
import shutil
import sys
import tempfile
import time
import unittest
from datetime import date, datetime, timedelta
from pathlib import Path
from unittest.mock import patch, MagicMock

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from memory.memory_manager import (
    query_patterns, update_memory, load_memory,
    EpisodicStore, _EPISODIC_STORE,
)
from proactive.conversation_state import ConversationState
from proactive.queue import ProactiveQueue
from proactive.patterns import detect_time_patterns, detect_frequency_patterns, compute_baseline
from proactive.anomalies import check_cpu_anomaly, check_ram_anomaly, check_app_anomaly
from proactive.suggestions import evaluate_suggestions, SUGGESTION_COOLDOWN
from proactive.briefing import generate_briefing, should_brief, BRIEFING_FILE


class QueryPatternsTest(unittest.TestCase):

    YESTERDAY = (date.today() - timedelta(days=1)).isoformat()
    THREE_DAYS_AGO = (date.today() - timedelta(days=3)).isoformat()

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="cryp_qp_"))
        self.store = EpisodicStore(base_dir=self.tmp)

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)
        global _EPISODIC_STORE
        _EPISODIC_STORE = None

    def test_returns_empty_when_no_episodes(self):
        with patch("memory.memory_manager._EPISODIC_STORE", self.store):
            result = query_patterns(days_back=7)
        self.assertEqual(result, [])

    def test_aggregates_tool_usage_and_topics(self):
        self.store.save_episode({
            "timestamp": f"{self.YESTERDAY}T10:00:00",
            "summary": "Worked on websocket bug",
            "tools_used": ["web_search", "file_controller"],
            "topics": ["websocket", "debugging"],
            "goal": "fix connection bug",
        })
        with patch("memory.memory_manager._EPISODIC_STORE", self.store):
            result = query_patterns(days_back=7)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["tools_used"], ["web_search", "file_controller"])
        self.assertEqual(result[0]["topics"], ["websocket", "debugging"])
        self.assertEqual(result[0]["goal"], "fix connection bug")

    def test_returns_newest_first(self):
        self.store.save_episode({"timestamp": f"{self.YESTERDAY}T10:00:00", "summary": "newer"})
        self.store.save_episode({"timestamp": f"{self.THREE_DAYS_AGO}T10:00:00", "summary": "older"})
        with patch("memory.memory_manager._EPISODIC_STORE", self.store):
            result = query_patterns(days_back=30)
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]["summary"], "newer")


class ConversationStateTest(unittest.TestCase):

    def setUp(self):
        self.state = ConversationState()

    def test_starts_inactive(self):
        self.assertFalse(self.state.is_active)
        self.assertFalse(self.state.is_speaking)

    def test_set_active(self):
        self.state.set_active(True)
        self.assertTrue(self.state.is_active)
        self.state.set_active(False)
        self.assertFalse(self.state.is_active)

    def test_set_speaking_updates_last_audio_end(self):
        self.state.set_speaking(True)
        self.assertTrue(self.state.is_speaking)
        t1 = self.state.last_audio_end
        self.state.set_speaking(False)
        self.assertFalse(self.state.is_speaking)
        self.assertGreater(self.state.last_audio_end, t1)


class ProactiveQueueTest(unittest.TestCase):

    def setUp(self):
        self.q = ProactiveQueue()

    def test_put_and_get(self):
        import asyncio
        loop = asyncio.new_event_loop()
        loop.run_until_complete(self.q.put("hello"))
        result = loop.run_until_complete(self.q.get())
        self.assertEqual(result, "hello")

    def test_put_nowait_and_get_nowait(self):
        self.q.put_nowait("world")
        self.assertFalse(self.q.empty())
        result = self.q.get_nowait()
        self.assertEqual(result, "world")
        self.assertTrue(self.q.empty())

    def test_empty_by_default(self):
        self.assertTrue(self.q.empty())
        self.assertEqual(self.q.qsize(), 0)


class PatternDetectionTest(unittest.TestCase):

    def test_detect_time_patterns_finds_repeated_tool(self):
        sessions = []
        for day in range(5):
            dt = datetime(2026, 6, 1 + day, 9, 0)
            sessions.append({
                "started_at": dt.isoformat(),
                "tools_used": ["Chrome"],
                "summary": f"day {day}",
            })
        patterns = detect_time_patterns(sessions)
        self.assertGreaterEqual(len(patterns), 1)
        self.assertEqual(patterns[0]["tool"], "Chrome")
        self.assertGreaterEqual(patterns[0]["frequency"], 3)

    def test_detect_time_patterns_ignores_low_frequency(self):
        sessions = [{
            "started_at": "2026-06-01T09:00:00",
            "tools_used": ["Chrome"],
        }]
        patterns = detect_time_patterns(sessions)
        self.assertEqual(len(patterns), 0)

    def test_detect_frequency_patterns(self):
        sessions = []
        for i, tool in enumerate(["Chrome"] * 10 + ["VS Code"] * 5 + ["Terminal"] * 3):
            day = (i % 7) + 1
            sessions.append({
                "started_at": f"2026-06-{day:02d}T10:00:00",
                "tools_used": [tool],
            })
        freq = detect_frequency_patterns(sessions)
        self.assertIn("morning", freq)
        self.assertEqual(freq["morning"][0], "Chrome")

    def test_compute_baseline(self):
        sessions = []
        for day in range(5):
            sessions.append({
                "started_at": f"2026-06-{day + 1:02d}T09:00:00",
                "tools_used": ["Chrome"],
            })
        baseline = compute_baseline(sessions)
        self.assertIn("09:00", baseline)
        self.assertEqual(baseline["09:00"]["typical_app"], "Chrome")


class AnomalyDetectionTest(unittest.TestCase):

    def test_cpu_anomaly_detected(self):
        baseline = {"cpu_baseline": {"mean": 30, "std": 5}}
        msg = check_cpu_anomaly(95, baseline)
        self.assertIsNotNone(msg)
        self.assertIn("CPU", msg)

    def test_cpu_normal_no_anomaly(self):
        baseline = {"cpu_baseline": {"mean": 30, "std": 5}}
        msg = check_cpu_anomaly(35, baseline)
        self.assertIsNone(msg)

    def test_ram_anomaly_detected(self):
        baseline = {"ram_baseline": {"mean": 40, "std": 5}}
        msg = check_ram_anomaly(90, baseline)
        self.assertIsNotNone(msg)
        self.assertIn("memory", msg.lower())

    def test_debounce_suppresses_repeat(self):
        from proactive.anomalies import _last_alert_times
        _last_alert_times.clear()
        baseline = {"cpu_baseline": {"mean": 30, "std": 5}}
        msg1 = check_cpu_anomaly(95, baseline)
        self.assertIsNotNone(msg1)
        msg2 = check_cpu_anomaly(95, baseline)
        self.assertIsNone(msg2)


class SuggestionEngineTest(unittest.TestCase):

    def test_terminal_rule_matches(self):
        from proactive.suggestions import _last_suggestion_time
        _last_suggestion_time = 0.0
        context = {
            "active_window": "Terminal - user@host: ~/projects",
            "clipboard": "",
        }
        suggestion = evaluate_suggestions(context)
        # Should match terminal_updates if within 08:00-10:00
        now = datetime.now()
        if 8 <= now.hour < 10 and now.weekday() < 5:
            self.assertIsNotNone(suggestion)
            self.assertIn("Sir", suggestion)

    def test_git_conflict_rule_matches(self):
        from proactive.suggestions import _last_suggestion_time
        _last_suggestion_time = 0.0
        context = {
            "active_window": "VS Code",
            "clipboard": "CONFLICT in main.py\n<<<<<<< HEAD",
        }
        suggestion = evaluate_suggestions(context)
        self.assertIsNotNone(suggestion)
        self.assertIn("merge conflict", suggestion.lower())

    def test_no_match_returns_none(self):
        from proactive.suggestions import _last_suggestion_time
        _last_suggestion_time = 0.0
        context = {
            "active_window": "Settings",
            "clipboard": "nothing special",
        }
        suggestion = evaluate_suggestions(context)
        self.assertIsNone(suggestion)


class BriefingTest(unittest.TestCase):

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="cryp_brf_"))

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_should_brief_when_no_file(self):
        with patch("proactive.briefing.BRIEFING_FILE", self.tmp / "last_briefing_date.txt"):
            self.assertTrue(should_brief())

    def test_should_not_brief_when_same_day(self):
        path = self.tmp / "last_briefing_date.txt"
        path.write_text(datetime.now().strftime("%Y-%m-%d"), encoding="utf-8")
        with patch("proactive.briefing.BRIEFING_FILE", path):
            self.assertFalse(should_brief())

    def test_generate_briefing_returns_text(self):
        result = generate_briefing(health_daemon=None)
        self.assertIsNotNone(result)
        self.assertIn("sir", result.lower())

    def test_generate_briefing_includes_greeting(self):
        result = generate_briefing()
        now = datetime.now()
        if now.hour < 12:
            self.assertIn("morning", result.lower())
        elif now.hour < 18:
            self.assertIn("afternoon", result.lower())
        else:
            self.assertIn("evening", result.lower())


class PatternsNamespaceTest(unittest.TestCase):

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="cryp_pn_"))

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    @patch("memory.memory_manager.BASE_DIR")
    def test_patterns_stored_and_loaded(self, mock_base):
        mock_base.return_value = self.tmp
        update_memory({"patterns": {"test_pattern": {"value": "test_value"}}})
        mem = load_memory()
        self.assertIn("patterns", mem)
        self.assertEqual(
            mem["patterns"].get("test_pattern", {}).get("value"),
            "test_value",
        )


class DailyAggregationTest(unittest.TestCase):

    def setUp(self):
        from core.context_collector import _daily_agg_date, _daily_agg_data
        _daily_agg_date = None
        _daily_agg_data.clear()

    def test_log_app_launch(self):
        from core.context_collector import log_app_launch, get_daily_aggregation
        log_app_launch("Chrome")
        agg = get_daily_aggregation()
        self.assertEqual(len(agg["app_launches"]), 1)
        self.assertEqual(agg["app_launches"][0]["app_name"], "Chrome")

    def test_multiple_launches(self):
        from core.context_collector import log_app_launch, get_daily_aggregation
        log_app_launch("Chrome")
        log_app_launch("VS Code")
        agg = get_daily_aggregation()
        self.assertEqual(len(agg["app_launches"]), 2)

    def test_aggregation_isolation(self):
        from core.context_collector import log_window_change, get_daily_aggregation
        log_window_change("Terminal")
        agg = get_daily_aggregation()
        self.assertEqual(len(agg["window_changes"]), 1)
        self.assertEqual(agg["window_changes"][0]["window_title"], "Terminal")


if __name__ == "__main__":
    unittest.main()
