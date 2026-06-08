import sys
import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from actions.jarvis_status import (
    jarvis_status, _get_version, _get_memory_stats,
    _get_full_status, _get_today_activity, _get_uptime,
    _get_capabilities,
)


class TestGetVersion(unittest.TestCase):

    def test_returns_non_empty_string(self):
        result = _get_version()
        self.assertIsInstance(result, str)
        self.assertTrue(len(result) > 0)

    def test_contains_mark_and_thirty_nine(self):
        result = _get_version()
        self.assertIn("Mark", result)
        self.assertIn("Thirty-Nine", result)


class TestGetMemoryStats(unittest.TestCase):

    @patch("memory.memory_manager.load_memory")
    @patch("memory.memory_manager.load_recent_episodes")
    def test_returns_non_empty_string(self, mock_episodes, mock_memory):
        mock_memory.return_value = {"identity": {"name": {"value": "Awais"}}}
        mock_episodes.return_value = [{"summary": "test"}]
        result = _get_memory_stats()
        self.assertIsInstance(result, str)
        self.assertTrue(len(result) > 0)
        self.assertIn("stored facts", result)

    @patch("memory.memory_manager.load_memory")
    def test_never_raises(self, mock_memory):
        mock_memory.side_effect = Exception("boom")
        result = _get_memory_stats()
        self.assertIsInstance(result, str)
        self.assertIn("unavailable", result)


class TestGetFullStatus(unittest.TestCase):

    @patch("actions.jarvis_status.psutil")
    @patch("memory.memory_manager.load_memory")
    def test_returns_non_empty_string(self, mock_memory, mock_psutil):
        mock_psutil.cpu_percent.return_value = 30
        mock_psutil.virtual_memory.return_value.percent = 50
        mock_psutil.disk_usage.return_value.percent = 40
        mock_psutil.sensors_battery.return_value = None
        mock_memory.return_value = {"identity": {"name": {"value": "Awais"}}}
        result = _get_full_status()
        self.assertIsInstance(result, str)
        self.assertTrue(len(result) > 0)
        self.assertIn("operational", result)

    @patch("actions.jarvis_status.psutil")
    def test_never_raises(self, mock_psutil):
        mock_psutil.cpu_percent.side_effect = Exception("boom")
        result = _get_full_status()
        self.assertIsInstance(result, str)
        self.assertIn("Status check failed", result)

    @patch("actions.jarvis_status.psutil")
    @patch("memory.memory_manager.load_memory")
    def test_includes_battery(self, mock_memory, mock_psutil):
        mock_psutil.cpu_percent.return_value = 30
        mock_psutil.virtual_memory.return_value.percent = 50
        mock_psutil.disk_usage.return_value.percent = 40
        bat = MagicMock()
        bat.percent = 85
        bat.power_plugged = True
        mock_psutil.sensors_battery.return_value = bat
        mock_memory.return_value = {}
        result = _get_full_status()
        self.assertIn("Battery", result)
        self.assertIn("charging", result)


class TestGetTodayActivity(unittest.TestCase):

    @patch("memory.memory_manager.load_recent_episodes")
    def test_returns_no_activity_when_empty(self, mock_episodes):
        mock_episodes.return_value = []
        result = _get_today_activity()
        self.assertIsInstance(result, str)
        self.assertIn("No activity recorded today", result)

    @patch("memory.memory_manager.load_recent_episodes")
    def test_never_raises(self, mock_episodes):
        mock_episodes.side_effect = Exception("boom")
        result = _get_today_activity()
        self.assertIsInstance(result, str)
        self.assertIn("unavailable", result)

    @patch("memory.memory_manager.load_recent_episodes")
    def test_shows_today_tools(self, mock_episodes):
        from datetime import date
        today = str(date.today())
        mock_episodes.return_value = [
            {"started_at": today + "T10:00:00", "tools_used": ["web_search", "open_app"], "user_turns": 5},
        ]
        result = _get_today_activity()
        self.assertIn("web_search", result)
        self.assertIn("open_app", result)


class TestGetUptime(unittest.TestCase):

    @patch("actions.jarvis_status.psutil")
    def test_contains_hours_minutes(self, mock_psutil):
        mock_psutil.boot_time.return_value = 1000.0
        import time as real_time
        start = real_time.time()
        result = _get_uptime()
        self.assertIsInstance(result, str)
        self.assertIn("hours", result)
        self.assertIn("minutes", result)

    @patch("actions.jarvis_status.psutil", None)
    def test_never_raises_when_no_psutil(self):
        result = _get_uptime()
        self.assertIsInstance(result, str)
        self.assertIn("unavailable", result)

    def test_never_raises_on_error(self):
        with patch("actions.jarvis_status.psutil") as mock_p:
            mock_p.boot_time.side_effect = Exception("boom")
            result = _get_uptime()
            self.assertIsInstance(result, str)
            self.assertIn("unavailable", result)


class TestGetCapabilities(unittest.TestCase):

    def test_lists_key_capabilities(self):
        result = _get_capabilities()
        self.assertIn("Kimi WebBridge", result)
        self.assertIn("ReAct", result)
        self.assertIn("proactive", result)


class TestJarvisStatusRouting(unittest.TestCase):

    @patch("actions.jarvis_status._get_full_status")
    def test_defaults_to_full_status(self, mock_full):
        mock_full.return_value = "full status"
        result = jarvis_status({})
        self.assertEqual(result, "full status")

    @patch("actions.jarvis_status._get_version")
    def test_routes_version_query(self, mock_version):
        mock_version.return_value = "version info"
        result = jarvis_status({"query": "version"})
        self.assertEqual(result, "version info")

    @patch("actions.jarvis_status._get_version")
    def test_routes_mark_query(self, mock_version):
        mock_version.return_value = "version info"
        result = jarvis_status({"query": "what mark are you"})
        self.assertEqual(result, "version info")

    @patch("actions.jarvis_status._get_memory_stats")
    def test_routes_memory_query(self, mock_mem):
        mock_mem.return_value = "memory stats"
        result = jarvis_status({"query": "memory"})
        self.assertEqual(result, "memory stats")

    @patch("actions.jarvis_status._get_memory_stats")
    def test_routes_remember_query(self, mock_mem):
        mock_mem.return_value = "memory stats"
        result = jarvis_status({"query": "what do you remember"})
        self.assertEqual(result, "memory stats")

    @patch("actions.jarvis_status._get_full_status")
    def test_routes_status_query(self, mock_full):
        mock_full.return_value = "full status"
        result = jarvis_status({"query": "status"})
        self.assertEqual(result, "full status")

    @patch("actions.jarvis_status._get_full_status")
    def test_routes_health_query(self, mock_full):
        mock_full.return_value = "full status"
        result = jarvis_status({"query": "health"})
        self.assertEqual(result, "full status")

    @patch("actions.jarvis_status._get_today_activity")
    def test_routes_activity_query(self, mock_act):
        mock_act.return_value = "today's activity"
        result = jarvis_status({"query": "activity"})
        self.assertEqual(result, "today's activity")

    @patch("actions.jarvis_status._get_today_activity")
    def test_routes_today_query(self, mock_act):
        mock_act.return_value = "today's activity"
        result = jarvis_status({"query": "what did you do today"})
        self.assertEqual(result, "today's activity")

    @patch("actions.jarvis_status._get_uptime")
    def test_routes_uptime_query(self, mock_up):
        mock_up.return_value = "uptime info"
        result = jarvis_status({"query": "uptime"})
        self.assertEqual(result, "uptime info")

    @patch("actions.jarvis_status._get_uptime")
    def test_routes_running_query(self, mock_up):
        mock_up.return_value = "uptime info"
        result = jarvis_status({"query": "how long have you been running"})
        self.assertEqual(result, "uptime info")

    @patch("actions.jarvis_status._get_capabilities")
    def test_routes_capability_query(self, mock_cap):
        mock_cap.return_value = "capabilities"
        result = jarvis_status({"query": "capabilities"})
        self.assertEqual(result, "capabilities")

    @patch("actions.jarvis_status._get_capabilities")
    def test_routes_what_can_query(self, mock_cap):
        mock_cap.return_value = "capabilities"
        result = jarvis_status({"query": "what can you do"})
        self.assertEqual(result, "capabilities")

    @patch("actions.jarvis_status._get_full_status")
    def test_routes_unknown_query_to_default(self, mock_full):
        mock_full.return_value = "full status"
        result = jarvis_status({"query": "foobar"})
        self.assertEqual(result, "full status")


if __name__ == "__main__":
    unittest.main()
