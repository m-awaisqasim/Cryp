import asyncio
import os
import time
import unittest
from unittest.mock import patch, MagicMock, PropertyMock

try:
    import psutil
except ImportError:
    psutil = None

from core.daemon import SystemHealthDaemon


class TestSystemHealthDaemonInit(unittest.TestCase):

    def setUp(self):
        for key in [
            "HEALTH_CHECK_INTERVAL", "HEALTH_CPU_THRESHOLD",
            "HEALTH_RAM_THRESHOLD", "HEALTH_DISK_THRESHOLD",
            "HEALTH_BATTERY_THRESHOLD", "HEALTH_DEBOUNCE_SECONDS",
        ]:
            os.environ.pop(key, None)

    def test_default_config(self):
        speak = MagicMock()
        log = MagicMock()
        d = SystemHealthDaemon(speak, log)
        self.assertEqual(d._interval, 60)
        self.assertEqual(d._cpu_threshold, 90)
        self.assertEqual(d._ram_threshold, 85)
        self.assertEqual(d._disk_threshold, 90)
        self.assertEqual(d._battery_threshold, 20)
        self.assertEqual(d._debounce_seconds, 300)

    def test_env_overrides(self):
        os.environ["HEALTH_CHECK_INTERVAL"] = "30"
        os.environ["HEALTH_CPU_THRESHOLD"] = "95"
        os.environ["HEALTH_RAM_THRESHOLD"] = "80"
        os.environ["HEALTH_DISK_THRESHOLD"] = "85"
        os.environ["HEALTH_BATTERY_THRESHOLD"] = "15"
        os.environ["HEALTH_DEBOUNCE_SECONDS"] = "600"
        d = SystemHealthDaemon(MagicMock(), MagicMock())
        self.assertEqual(d._interval, 30)
        self.assertEqual(d._cpu_threshold, 95)
        self.assertEqual(d._ram_threshold, 80)
        self.assertEqual(d._disk_threshold, 85)
        self.assertEqual(d._battery_threshold, 15)
        self.assertEqual(d._debounce_seconds, 600)

    def test_stores_callbacks(self):
        speak = MagicMock()
        log = MagicMock()
        d = SystemHealthDaemon(speak, log)
        self.assertIs(d._speak, speak)
        self.assertIs(d._write_log, log)


class TestSystemHealthDaemonCPU(unittest.TestCase):

    def setUp(self):
        self.speak = MagicMock()
        self.log = MagicMock()
        self.d = SystemHealthDaemon(self.speak, self.log)
        self.d._cpu_threshold = 90

    def test_below_threshold_resets_count(self):
        with patch("core.daemon.psutil.cpu_percent", return_value=50):
            self.d._check_cpu()
        self.assertEqual(self.d._consecutive["cpu"], 0)
        self.speak.assert_not_called()

    def test_above_threshold_single_check_no_alert(self):
        with patch("core.daemon.psutil.cpu_percent", return_value=95):
            self.d._check_cpu()
        self.assertEqual(self.d._consecutive["cpu"], 1)
        self.speak.assert_not_called()

    def test_above_threshold_two_checks_triggers_alert(self):
        with patch("core.daemon.psutil.cpu_percent", return_value=95):
            self.d._check_cpu()  # 1st
            self.d._check_cpu()  # 2nd consecutive
        self.speak.assert_called_once()
        self.log.assert_called_with("ALERT: CPU at 95%")

    def test_alert_has_correct_text(self):
        with patch("core.daemon.psutil.cpu_percent", return_value=95):
            self.d._check_cpu()
            self.d._check_cpu()
        self.speak.assert_called_with("Sir, CPU is at 95 percent.")

    def test_debounce_suppresses_repeat_alert(self):
        with patch("core.daemon.psutil.cpu_percent", return_value=95):
            self.d._check_cpu()
            self.d._check_cpu()  # alert fires
            self.d._check_cpu()  # debounced
        self.speak.assert_called_once()

    def test_debounce_expires_after_timeout(self):
        with patch("core.daemon.psutil.cpu_percent", return_value=95):
            self.d._check_cpu()
            self.d._check_cpu()  # alert fires
        self.d._last_alert_time["cpu"] = time.time() - 301
        with patch("core.daemon.psutil.cpu_percent", return_value=95):
            self.d._check_cpu()  # should re-fire
        self.assertEqual(self.speak.call_count, 2)

    def test_recovery_resets_count(self):
        with patch("core.daemon.psutil.cpu_percent", return_value=95):
            self.d._check_cpu()
            self.d._check_cpu()  # alert
        self.assertEqual(self.speak.call_count, 1)
        with patch("core.daemon.psutil.cpu_percent", return_value=50):
            self.d._check_cpu()  # recovers
        self.assertEqual(self.d._consecutive["cpu"], 0)


class TestSystemHealthDaemonRAM(unittest.TestCase):

    def setUp(self):
        self.speak = MagicMock()
        self.log = MagicMock()
        self.d = SystemHealthDaemon(self.speak, self.log)
        self.d._ram_threshold = 85

    def test_triggers_alert(self):
        with patch.object(psutil, "virtual_memory") as m:
            m.return_value.percent = 92
            self.d._check_ram()
            self.d._check_ram()
        self.speak.assert_called_once()
        self.log.assert_called_with("ALERT: RAM at 92%")

    def test_speak_text(self):
        with patch.object(psutil, "virtual_memory") as m:
            m.return_value.percent = 92
            self.d._check_ram()
            self.d._check_ram()
        self.speak.assert_called_with("Sir, memory is at 92 percent.")


class TestSystemHealthDaemonDisk(unittest.TestCase):

    def setUp(self):
        self.speak = MagicMock()
        self.log = MagicMock()
        self.d = SystemHealthDaemon(self.speak, self.log)
        self.d._disk_threshold = 90

    def test_triggers_alert(self):
        with patch.object(psutil, "disk_usage") as m:
            m.return_value.percent = 95
            self.d._check_disk()
            self.d._check_disk()
        self.speak.assert_called_once()
        self.log.assert_called_with("ALERT: DISK at 95%")

    def test_speak_text(self):
        with patch.object(psutil, "disk_usage") as m:
            m.return_value.percent = 95
            self.d._check_disk()
            self.d._check_disk()
        self.speak.assert_called_with("Sir, disk is at 95 percent.")


class TestSystemHealthDaemonBattery(unittest.TestCase):

    def setUp(self):
        self.speak = MagicMock()
        self.log = MagicMock()
        self.d = SystemHealthDaemon(self.speak, self.log)
        self.d._battery_threshold = 20

    def test_skipped_when_no_battery(self):
        with patch.object(psutil, "sensors_battery", return_value=None):
            self.d._check_battery()
        self.speak.assert_not_called()

    def test_skipped_when_plugged_in(self):
        bat = MagicMock()
        bat.percent = 10
        bat.power_plugged = True
        with patch.object(psutil, "sensors_battery", return_value=bat):
            self.d._check_battery()
        self.speak.assert_not_called()

    def test_low_battery_triggers_alert(self):
        bat = MagicMock()
        bat.percent = 10
        bat.power_plugged = False
        with patch.object(psutil, "sensors_battery", return_value=bat):
            self.d._check_battery()
        self.speak.assert_called_once()
        self.log.assert_called_with("ALERT: Battery at 10%")

    def test_speak_text(self):
        bat = MagicMock()
        bat.percent = 10
        bat.power_plugged = False
        with patch.object(psutil, "sensors_battery", return_value=bat):
            self.d._check_battery()
        self.speak.assert_called_with("Sir, battery is at 10 percent.")

    def test_above_threshold_skipped(self):
        bat = MagicMock()
        bat.percent = 50
        bat.power_plugged = False
        with patch.object(psutil, "sensors_battery", return_value=bat):
            self.d._check_battery()
        self.speak.assert_not_called()


class TestSystemHealthDaemonRun(unittest.TestCase):

    def test_run_returns_cleanly_on_cancel(self):
        d = SystemHealthDaemon(MagicMock(), MagicMock())
        async def _test():
            task = asyncio.create_task(d.run())
            await asyncio.sleep(0.05)
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass
        asyncio.run(_test())

    def test_run_skipped_when_no_psutil(self):
        log = MagicMock()
        d = SystemHealthDaemon(MagicMock(), log)
        with patch("core.daemon.psutil", None):
            async def _test():
                await d.run()
            asyncio.run(_test())
        log.assert_called_once()


class TestSystemHealthDaemonErrorHandling(unittest.TestCase):

    def test_speak_failure_does_not_crash(self):
        def failing_speak(text):
            raise RuntimeError("no session")
        d = SystemHealthDaemon(failing_speak, MagicMock())
        d._last_alert_time["cpu"] = 0
        with patch("core.daemon.psutil.cpu_percent", return_value=95):
            d._consecutive["cpu"] = 2
            d._check_cpu()  # should not raise
        d._alert_speak("test")  # explicit call also safe

    def test_psutil_exception_does_not_crash(self):
        d = SystemHealthDaemon(MagicMock(), MagicMock())
        with patch("core.daemon.psutil.cpu_percent", side_effect=Exception("boom")):
            d._check_cpu()  # should not raise
        self.assertEqual(d._consecutive["cpu"], 0)


if __name__ == "__main__":
    unittest.main()
