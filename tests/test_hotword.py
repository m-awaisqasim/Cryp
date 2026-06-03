import os
import time
import unittest
from unittest.mock import patch, MagicMock, PropertyMock

from core.wake_config import WakeConfig


class TestWakeConfig(unittest.TestCase):
    def test_defaults(self):
        cfg = WakeConfig()
        self.assertTrue(cfg.enabled)
        self.assertAlmostEqual(cfg.threshold, 0.5)
        self.assertEqual(cfg.wake_words, ["hey jarvis"])
        self.assertAlmostEqual(cfg.silence_timeout, 10.0)

    def test_disabled_via_env(self):
        with patch.dict(os.environ, {"JARVIS_HOTWORD": "0"}, clear=False):
            cfg = WakeConfig()
            self.assertFalse(cfg.enabled)

    def test_custom_threshold_env(self):
        with patch.dict(os.environ, {"JARVIS_HOTWORD_THRESHOLD": "0.8"}, clear=False):
            cfg = WakeConfig()
            self.assertAlmostEqual(cfg.threshold, 0.8)

    def test_custom_timeout_env(self):
        with patch.dict(os.environ, {"JARVIS_SILENCE_TIMEOUT": "30"}, clear=False):
            cfg = WakeConfig()
            self.assertAlmostEqual(cfg.silence_timeout, 30.0)


def _make_mock_stream(read_return):
    mock_stream = MagicMock()
    mock_stream.__enter__.return_value = mock_stream
    mock_stream.read.return_value = read_return
    return mock_stream


def _make_stream_mock(read_return=None):
    import numpy as np
    m = MagicMock()
    m.__enter__.return_value = m
    if read_return is None:
        read_return = (np.zeros(1280, dtype=np.int16), None)
    m.read.return_value = read_return
    return m


class TestHotwordDetector(unittest.TestCase):
    def setUp(self):
        import core.hotword as ch
        self._ch = ch
        self._sd_patch = patch.object(ch.sd, "InputStream")
        self._sd_mock = self._sd_patch.start()
        self._sd_mock.return_value = _make_stream_mock()
        self._oww_patch = patch.object(ch, "_OWWModel")
        self._oww_patch.start()
        self._have_patch = patch.object(ch, "_HAVE_OWW", True)
        self._have_patch.start()
        self.addCleanup(self._sd_patch.stop)
        self.addCleanup(self._oww_patch.stop)
        self.addCleanup(self._have_patch.stop)

    def test_start_launches_daemon_thread(self):
        detector = self._ch.HotwordDetector()
        detector.start(lambda: None)
        self.assertIsNotNone(detector._thread)
        self.assertTrue(detector._thread.daemon)
        detector.stop()

    def test_stop_sets_event(self):
        detector = self._ch.HotwordDetector()
        detector._model = MagicMock()
        detector.start(lambda: None)
        detector.stop()
        self.assertTrue(detector._stop_event.is_set())

    def test_is_running_returns_false_before_start(self):
        detector = self._ch.HotwordDetector()
        self.assertFalse(detector.is_running())

    def test_is_running_returns_true_after_start(self):
        detector = self._ch.HotwordDetector()
        detector.start(lambda: None)
        time.sleep(0.05)
        self.assertTrue(detector.is_running())
        detector.stop()

    def test_on_detected_called_above_threshold(self):
        import numpy as np
        mock_model = MagicMock()
        mock_model.predict.return_value = {"hey_jarvis": 0.9}

        detector = self._ch.HotwordDetector(threshold=0.5)
        detector._model = mock_model
        callback = MagicMock()
        detector._on_detected = callback

        fake_audio = np.zeros((1280, 1), dtype=np.int16)
        detector._audio_callback(fake_audio, 1280, None, None)
        callback.assert_called_once()

    def test_on_detected_not_called_below_threshold(self):
        import numpy as np
        mock_model = MagicMock()
        mock_model.predict.return_value = {"hey_jarvis": 0.1}

        detector = self._ch.HotwordDetector(threshold=0.5)
        detector._model = mock_model
        callback = MagicMock()
        detector._on_detected = callback

        fake_audio = np.zeros((1280, 1), dtype=np.int16)
        detector._audio_callback(fake_audio, 1280, None, None)
        callback.assert_not_called()


if __name__ == "__main__":
    unittest.main()
