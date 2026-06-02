import asyncio
import sys
import threading
import types
import unittest
from unittest.mock import patch

_FAKE_GOOGLE = types.ModuleType("google")
_FAKE_GENAI = types.ModuleType("google.generativeai")
_FAKE_GENAI.GenerativeModel = object  # placeholder so patch() can find the attr
_FAKE_GENAI.configure = lambda **_kw: None
_FAKE_GOOGLE.generativeai = _FAKE_GENAI
sys.modules["google"] = _FAKE_GOOGLE
sys.modules["google.generativeai"] = _FAKE_GENAI
# Make sure planner_layer picks up our fakes by clearing any cached state
import agent.planner_layer as _pl
_pl._genai_ready = True  # skip the real configure() call in tests

from agent.config import PlannerConfig
from agent.planner_layer import (
    PLANNER_PROMPT,
    PlannerLayer,
    generate_plan,
    is_complex_goal,
    truncate_plan,
)


def _cfg(**overrides):
    defaults = dict(
        enabled=True,
        model_name="gemini-2.0-flash",
        speak_wait_seconds=0.0,
        min_goal_chars=40,
        coordination_words=(" and ", " then ", " after ", ";", " plus "),
        max_plan_chars=800,
        planner_always_on=False,
    )
    defaults.update(overrides)
    return PlannerConfig(**defaults)


class FakeModel:
    def __init__(self, text="Step 1: do thing\nStep 2: finish"):
        self.text = text

    def generate_content(self, _prompt):
        return self


class TestIsComplexGoal(unittest.TestCase):

    def test_short_goal_is_simple(self):
        self.assertFalse(is_complex_goal("open clock", _cfg()))

    def test_long_goal_is_complex(self):
        goal = "research mechanical engineering history and write a report about it"
        self.assertTrue(is_complex_goal(goal, _cfg()))

    def test_coordination_word_makes_complex(self):
        self.assertTrue(is_complex_goal("search the web and save the result", _cfg()))

    def test_always_on_overrides_heuristic(self):
        cfg = _cfg(planner_always_on=True)
        self.assertTrue(is_complex_goal("open clock", cfg))

    def test_empty_goal_is_simple(self):
        self.assertFalse(is_complex_goal("", _cfg()))

    def test_semicolon_triggers_complex(self):
        self.assertTrue(is_complex_goal("task a; task b", _cfg()))


class TestTruncatePlan(unittest.TestCase):

    def test_short_plan_unchanged(self):
        self.assertEqual(truncate_plan("hi", 100), "hi")

    def test_long_plan_clipped_with_marker(self):
        plan = "x" * 500
        out = truncate_plan(plan, 50)
        self.assertLessEqual(len(out), 50)
        self.assertTrue(out.endswith("…"))

    def test_zero_max_returns_input(self):
        self.assertEqual(truncate_plan("hello", 0), "hello")

    def test_empty_plan(self):
        self.assertEqual(truncate_plan("", 100), "")


class TestGeneratePlan(unittest.TestCase):

    def test_returns_text_on_success(self):
        with patch("google.generativeai.GenerativeModel", return_value=FakeModel("Step 1: search\nStep 2: finish")):
            plan = asyncio.run(generate_plan("research something and write it up", _cfg()))
        self.assertEqual(plan, "Step 1: search\nStep 2: finish")

    def test_returns_none_on_empty_output(self):
        with patch("google.generativeai.GenerativeModel", return_value=FakeModel("")):
            plan = asyncio.run(generate_plan("research and write", _cfg()))
        self.assertIsNone(plan)

    def test_returns_none_on_whitespace_only(self):
        with patch("google.generativeai.GenerativeModel", return_value=FakeModel("   \n  ")):
            plan = asyncio.run(generate_plan("research and write", _cfg()))
        self.assertIsNone(plan)

    def test_returns_none_on_exception(self):
        def boom(*_a, **_kw):
            raise RuntimeError("api down")

        with patch("google.generativeai.GenerativeModel", side_effect=boom):
            plan = asyncio.run(generate_plan("research and write", _cfg()))
        self.assertIsNone(plan)

    def test_strips_code_fences(self):
        with patch("google.generativeai.GenerativeModel", return_value=FakeModel("```Step 1: x\nStep 2: y```")):
            plan = asyncio.run(generate_plan("research and write", _cfg()))
        self.assertEqual(plan, "Step 1: x\nStep 2: y")

    def test_uses_configured_model(self):
        with patch("google.generativeai.GenerativeModel", return_value=FakeModel("ok")) as gm:
            asyncio.run(generate_plan("research and write", _cfg(model_name="gemini-2.5-pro")))
        self.assertEqual(gm.call_args.kwargs["model_name"], "gemini-2.5-pro")


class TestAnnounce(unittest.TestCase):

    def test_speaks_and_logs_and_returns_plan(self):
        cfg = _cfg(speak_wait_seconds=0.0)
        layer = PlannerLayer(cfg)
        speaks = []
        logs = []

        def speak(t):
            speaks.append(t)

        def write_log(t):
            logs.append(t)

        with patch("agent.planner_layer.generate_plan", AsyncReturn("Step 1: a\nStep 2: b")):
            plan = asyncio.run(layer.announce(
                goal="research X and save it",
                speak=speak, write_log=write_log, cancel_flag=None,
            ))
        self.assertEqual(plan, "Step 1: a\nStep 2: b")
        self.assertEqual(speaks, ["Step 1: a\nStep 2: b"])
        self.assertEqual(len(logs), 1)
        self.assertIn("Step 1: a", logs[0])

    def test_skips_when_disabled(self):
        layer = PlannerLayer(_cfg(enabled=False))
        speaks = []
        logs = []

        with patch("agent.planner_layer.generate_plan", AsyncReturn("plan")):
            plan = asyncio.run(layer.announce(
                goal="research X and save it",
                speak=lambda t: speaks.append(t),
                write_log=lambda t: logs.append(t),
            ))
        self.assertIsNone(plan)
        self.assertEqual(speaks, [])
        self.assertEqual(logs, [])

    def test_skips_when_goal_is_simple(self):
        layer = PlannerLayer(_cfg(speak_wait_seconds=0.0))
        speaks, logs = [], []

        with patch("agent.planner_layer.generate_plan", AsyncReturn("plan")):
            plan = asyncio.run(layer.announce(
                goal="open clock",
                speak=lambda t: speaks.append(t),
                write_log=lambda t: logs.append(t),
            ))
        self.assertIsNone(plan)
        self.assertEqual(speaks, [])
        self.assertEqual(logs, [])

    def test_returns_none_when_generate_plan_fails(self):
        layer = PlannerLayer(_cfg(speak_wait_seconds=0.0))
        speaks, logs = [], []

        with patch("agent.planner_layer.generate_plan", AsyncReturn(None)):
            plan = asyncio.run(layer.announce(
                goal="research X and save it",
                speak=lambda t: speaks.append(t),
                write_log=lambda t: logs.append(t),
            ))
        self.assertIsNone(plan)
        self.assertEqual(speaks, [])
        self.assertEqual(logs, [])

    def test_returns_none_when_speak_raises(self):
        layer = PlannerLayer(_cfg(speak_wait_seconds=0.0))

        def boom(_t):
            raise RuntimeError("tts down")

        with patch("agent.planner_layer.generate_plan", AsyncReturn("plan")):
            plan = asyncio.run(layer.announce(
                goal="research X and save it",
                speak=boom, write_log=lambda _t: None,
            ))
        self.assertIsNone(plan)

    def test_speaks_exactly_once(self):
        layer = PlannerLayer(_cfg(speak_wait_seconds=0.0))
        speak_calls = []

        with patch("agent.planner_layer.generate_plan", AsyncReturn("Step 1: x")):
            asyncio.run(layer.announce(
                goal="research X and save it",
                speak=lambda t: speak_calls.append(t),
                write_log=lambda _t: None,
            ))
        self.assertEqual(len(speak_calls), 1)

    def test_writes_log_once(self):
        layer = PlannerLayer(_cfg(speak_wait_seconds=0.0))
        log_calls = []

        with patch("agent.planner_layer.generate_plan", AsyncReturn("Step 1: x")):
            asyncio.run(layer.announce(
                goal="research X and save it",
                speak=lambda _t: None,
                write_log=lambda t: log_calls.append(t),
            ))
        self.assertEqual(len(log_calls), 1)

    def test_sleeps_for_wait_seconds(self):
        layer = PlannerLayer(_cfg(speak_wait_seconds=0.05))

        real_sleep = asyncio.sleep

        async def fake_sleep(seconds):
            self.assertEqual(seconds, 0.05)
            await real_sleep(0)

        with patch("agent.planner_layer.generate_plan", AsyncReturn("Step 1: x")):
            with patch("agent.planner_layer.asyncio.sleep", side_effect=fake_sleep):
                asyncio.run(layer.announce(
                    goal="research X and save it",
                    speak=lambda _t: None,
                    write_log=lambda _t: None,
                ))

    def test_cancellation_before_call(self):
        layer = PlannerLayer(_cfg(speak_wait_seconds=0.0))
        cancel = threading.Event()
        cancel.set()

        with patch("agent.planner_layer.generate_plan") as gp:
            plan = asyncio.run(layer.announce(
                goal="research X and save it",
                speak=lambda _t: None,
                write_log=lambda _t: None,
                cancel_flag=cancel,
            ))
        self.assertIsNone(plan)
        gp.assert_not_called()

    def test_cancellation_during_wait(self):
        layer = PlannerLayer(_cfg(speak_wait_seconds=0.05))
        cancel = threading.Event()

        async def cancel_during_sleep(_seconds):
            cancel.set()

        with patch("agent.planner_layer.generate_plan", AsyncReturn("Step 1: x")):
            with patch("agent.planner_layer.asyncio.sleep", side_effect=cancel_during_sleep):
                plan = asyncio.run(layer.announce(
                    goal="research X and save it",
                    speak=lambda _t: None,
                    write_log=lambda _t: None,
                    cancel_flag=cancel,
                ))
        self.assertIsNone(plan)

    def test_never_raises_on_any_failure(self):
        layer = PlannerLayer(_cfg(speak_wait_seconds=0.0))

        def boom_speak(_t):
            raise RuntimeError("boom")

        def boom_log(_t):
            raise RuntimeError("boom")

        with patch("agent.planner_layer.generate_plan", side_effect=RuntimeError("nope")):
            plan = asyncio.run(layer.announce(
                goal="research X and save it",
                speak=boom_speak, write_log=boom_log,
            ))
        self.assertIsNone(plan)


class AsyncReturn:
    def __init__(self, value):
        self.value = value

    def __call__(self, *args, **kwargs):
        async def coro():
            return self.value
        return coro()


class TestPlannerPrompt(unittest.TestCase):

    def test_prompt_mentions_numbered_prose(self):
        self.assertIn("numbered", PLANNER_PROMPT.lower())
        self.assertIn("prose", PLANNER_PROMPT.lower())


if __name__ == "__main__":
    unittest.main()
