import os
import unittest

from core.retry import is_transient_error, is_transient_result, make_retry_decorator
from agent.config import RetryConfig


class TestIsTransientError(unittest.TestCase):

    def test_timeout_is_transient(self):
        self.assertTrue(is_transient_error(TimeoutError("connection timed out")))

    def test_503_is_transient(self):
        self.assertTrue(is_transient_error(RuntimeError("HTTP 503 Service Unavailable")))

    def test_connection_error_is_transient(self):
        self.assertTrue(is_transient_error(ConnectionError("Connection refused")))

    def test_deadline_exceeded_is_transient(self):
        self.assertTrue(is_transient_error(RuntimeError("deadline exceeded")))

    def test_value_error_is_not_transient(self):
        self.assertFalse(is_transient_error(ValueError("invalid argument")))

    def test_bad_selector_is_not_transient(self):
        self.assertFalse(is_transient_error(Exception("No element found for selector")))

    def test_auth_failure_is_not_transient(self):
        self.assertFalse(is_transient_error(PermissionError("permission denied")))

    def test_429_is_transient(self):
        self.assertTrue(is_transient_error(RuntimeError("429 Too Many Requests")))

    def test_broken_pipe_is_transient(self):
        self.assertTrue(is_transient_error(BrokenPipeError("broken pipe")))

    def test_reset_by_peer_is_transient(self):
        self.assertTrue(is_transient_error(ConnectionResetError("connection reset by peer")))

    def test_unavailable_is_transient(self):
        self.assertTrue(is_transient_error(RuntimeError("service unavailable")))

    def test_connectionerror_lowercase(self):
        self.assertTrue(is_transient_error(Exception("connectionerror")))

    def test_timeouterror_lowercase(self):
        self.assertTrue(is_transient_error(Exception("timeouterror")))


class TestIsTransientResult(unittest.TestCase):

    def test_result_with_timeout(self):
        self.assertTrue(is_transient_result("request timeout after 30 seconds"))

    def test_result_with_503(self):
        self.assertTrue(is_transient_result("HTTP error 503 backend unavailable"))

    def test_result_with_connection(self):
        self.assertTrue(is_transient_result("connection lost to server"))

    def test_normal_result_not_transient(self):
        self.assertFalse(is_transient_result("Search completed: found 10 results"))

    def test_error_result_not_transient(self):
        self.assertFalse(is_transient_result("Error: invalid query syntax"))

    def test_none_result_not_transient(self):
        self.assertFalse(is_transient_result(None))

    def test_non_string_result_not_transient(self):
        self.assertFalse(is_transient_result({"error": "timeout"}))

    def test_result_with_unavailable(self):
        self.assertTrue(is_transient_result("service is currently unavailable"))

    def test_result_with_broken_pipe(self):
        self.assertTrue(is_transient_result("broken pipe error occurred"))

    def test_case_insensitive_match(self):
        self.assertTrue(is_transient_result("Connection Timeout"))


class TestMakeRetryDecorator(unittest.TestCase):

    def test_returns_callable(self):
        cfg = RetryConfig()
        decorator = make_retry_decorator(cfg)
        self.assertTrue(callable(decorator))

    def test_applies_to_function(self):
        cfg = RetryConfig()
        decorator = make_retry_decorator(cfg)

        call_count = 0

        @decorator
        def succeeds():
            nonlocal call_count
            call_count += 1
            return "ok"

        result = succeeds()
        self.assertEqual(result, "ok")
        self.assertEqual(call_count, 1)

    def test_transient_then_success(self):
        cfg = RetryConfig()
        decorator = make_retry_decorator(cfg)
        call_count = 0

        @decorator
        def flaky():
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise ConnectionError("connection reset by peer")
            return "recovered"

        result = flaky()
        self.assertEqual(result, "recovered")
        self.assertEqual(call_count, 2)

    def test_permanent_error_not_retried(self):
        cfg = RetryConfig()
        decorator = make_retry_decorator(cfg)
        call_count = 0

        @decorator
        def always_fails():
            nonlocal call_count
            call_count += 1
            raise ValueError("bad argument")

        with self.assertRaises(ValueError):
            always_fails()
        self.assertEqual(call_count, 1)

    def test_transient_result_retried(self):
        cfg = RetryConfig()
        decorator = make_retry_decorator(cfg)
        call_count = 0

        @decorator
        def returns_timeout():
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                return "timeout error occurred"
            return "success"

        result = returns_timeout()
        self.assertEqual(result, "success")
        self.assertEqual(call_count, 2)


class TestRetryConfig(unittest.TestCase):

    def setUp(self):
        for key in ["RETRY_MAX_ATTEMPTS", "RETRY_BASE_DELAY", "RETRY_JITTER", "RETRY_MAX_DELAY"]:
            os.environ.pop(key, None)

    def test_default_values(self):
        cfg = RetryConfig()
        self.assertEqual(cfg.max_attempts, 3)
        self.assertEqual(cfg.base_delay, 1.0)
        self.assertEqual(cfg.jitter, 0.5)
        self.assertEqual(cfg.max_delay, 10.0)

    def test_env_override(self):
        os.environ["RETRY_MAX_ATTEMPTS"] = "5"
        os.environ["RETRY_BASE_DELAY"] = "2.0"
        os.environ["RETRY_JITTER"] = "1.0"
        os.environ["RETRY_MAX_DELAY"] = "30.0"
        cfg = RetryConfig()
        self.assertEqual(cfg.max_attempts, 5)
        self.assertEqual(cfg.base_delay, 2.0)
        self.assertEqual(cfg.jitter, 1.0)
        self.assertEqual(cfg.max_delay, 30.0)

    def test_invalid_env_falls_back_to_default(self):
        os.environ["RETRY_MAX_ATTEMPTS"] = "not-a-number"
        cfg = RetryConfig()
        self.assertEqual(cfg.max_attempts, 3)


if __name__ == "__main__":
    unittest.main()
