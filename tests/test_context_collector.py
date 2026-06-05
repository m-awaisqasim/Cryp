import unittest
from unittest.mock import patch, MagicMock
from core.context_collector import (
    get_active_window, get_clipboard, get_battery,
    get_cpu_usage, get_ram_usage, gather_live_context,
)


class TestGetActiveWindow(unittest.TestCase):
    @patch("core.context_collector.subprocess.check_output")
    def test_returns_window_title(self, mock_check_output):
        mock_check_output.return_value = "Firefox\n"
        result = get_active_window()
        self.assertEqual(result, "Firefox")

    @patch("core.context_collector.subprocess.check_output", side_effect=Exception)
    def test_returns_none_on_failure(self, mock_check_output):
        result = get_active_window()
        self.assertIsNone(result)

    @patch("core.context_collector.subprocess.check_output")
    @patch("core.context_collector.sys.platform", "win32")
    def test_returns_none_on_non_linux(self, mock_check_output):
        result = get_active_window()
        self.assertIsNone(result)


class TestGetClipboard(unittest.TestCase):
    @patch("core.context_collector.pyperclip.paste", return_value="hello world")
    def test_returns_clipboard_text(self, mock_paste):
        result = get_clipboard()
        self.assertEqual(result, "hello world")

    @patch("core.context_collector.pyperclip.paste", return_value="")
    def test_returns_none_on_empty(self, mock_paste):
        result = get_clipboard()
        self.assertIsNone(result)

    @patch("core.context_collector.pyperclip.paste", side_effect=Exception)
    def test_returns_none_on_failure(self, mock_paste):
        result = get_clipboard()
        self.assertIsNone(result)

    @patch("core.context_collector.pyperclip.paste")
    def test_truncates_to_200_chars(self, mock_paste):
        mock_paste.return_value = "a" * 300
        result = get_clipboard()
        self.assertEqual(len(result), 203)
        self.assertTrue(result.endswith("..."))

    @patch("core.context_collector.pyperclip.paste")
    def test_sanitizes_newlines(self, mock_paste):
        mock_paste.return_value = "line1\nline2\rline3"
        result = get_clipboard()
        self.assertNotIn("\n", result)
        self.assertNotIn("\r", result)


class TestGetBattery(unittest.TestCase):
    @patch("core.context_collector.psutil.sensors_battery")
    def test_returns_none_when_no_battery(self, mock_battery):
        mock_battery.return_value = None
        result = get_battery()
        self.assertIsNone(result)

    @patch("core.context_collector.psutil.sensors_battery", side_effect=Exception)
    def test_returns_none_on_failure(self, mock_battery):
        result = get_battery()
        self.assertIsNone(result)


class TestGetCpuUsage(unittest.TestCase):
    @patch("core.context_collector.psutil.cpu_percent", return_value=42.5)
    def test_returns_cpu_percent(self, mock_cpu):
        result = get_cpu_usage()
        self.assertEqual(result, "42.5%")

    @patch("core.context_collector.psutil.cpu_percent", side_effect=Exception)
    def test_returns_none_on_failure(self, mock_cpu):
        result = get_cpu_usage()
        self.assertIsNone(result)


class TestGetRamUsage(unittest.TestCase):
    @patch("core.context_collector.psutil.virtual_memory")
    def test_returns_ram_string(self, mock_mem):
        mock_mem.return_value = MagicMock(percent=75.0, used=12_000_000_000, total=16_000_000_000)
        result = get_ram_usage()
        self.assertIn("75.0%", result)
        self.assertIn("GB", result)

    @patch("core.context_collector.psutil.virtual_memory", side_effect=Exception)
    def test_returns_none_on_failure(self, mock_mem):
        result = get_ram_usage()
        self.assertIsNone(result)


class TestGatherLiveContext(unittest.TestCase):
    @patch("core.context_collector.get_active_window", return_value="Terminal")
    @patch("core.context_collector.get_clipboard", return_value="code")
    @patch("core.context_collector.get_battery", return_value="75%")
    @patch("core.context_collector.get_cpu_usage", return_value="30%")
    @patch("core.context_collector.get_ram_usage", return_value="50% (8.0 / 16.0 GB)")
    @patch("core.context_collector.datetime")
    def test_returns_formatted_string(self, mock_dt, mock_ram, mock_cpu, mock_bat, mock_clip, mock_win):
        mock_dt.now.return_value.strftime.return_value = "Friday 05 June 2026 — 17:00:00"
        result = gather_live_context()
        self.assertIn("[LIVE CONTEXT]", result)
        self.assertIn("Active Window : Terminal", result)
        self.assertIn("Clipboard     : code", result)
        self.assertIn("CPU           : 30%", result)
        self.assertIn("Time          : Friday 05 June 2026 — 17:00:00", result)

    @patch("core.context_collector.get_active_window", return_value=None)
    @patch("core.context_collector.get_clipboard", return_value=None)
    @patch("core.context_collector.get_battery", return_value=None)
    @patch("core.context_collector.get_cpu_usage", return_value=None)
    @patch("core.context_collector.get_ram_usage", return_value=None)
    @patch("core.context_collector.datetime")
    def test_omits_none_fields(self, mock_dt, mock_ram, mock_cpu, mock_bat, mock_clip, mock_win):
        mock_dt.now.return_value.strftime.return_value = "Friday 05 June 2026 — 17:00:00"
        result = gather_live_context()
        self.assertNotIn("Active Window", result)
        self.assertNotIn("Clipboard", result)
        self.assertNotIn("Battery", result)
        self.assertNotIn("CPU", result)
        self.assertNotIn("RAM", result)
        self.assertIn("Time", result)

    def test_never_raises_with_all_failures(self):
        with (
            patch("core.context_collector.get_active_window", return_value=None),
            patch("core.context_collector.get_clipboard", return_value=None),
            patch("core.context_collector.get_battery", return_value=None),
            patch("core.context_collector.get_cpu_usage", return_value=None),
            patch("core.context_collector.get_ram_usage", return_value=None),
        ):
            result = gather_live_context()
            self.assertIsInstance(result, str)
            self.assertIn("Time", result)

    def test_never_raises(self):
        result = gather_live_context()
        self.assertIsInstance(result, str)
