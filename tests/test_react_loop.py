import asyncio
import threading
import unittest

from agent.react_loop import (
    Action,
    Observation,
    ReactAgentLoop,
    REACT_SYSTEM_PROMPT,
    build_tool_registry,
    format_observation,
    format_registry_for_prompt,
    parse_action,
    summarize_parameters,
    truncate_observation,
)


DECLARATIONS = [
    {
        "name": "agent_task",
        "description": "Goal runner",
        "parameters": {"type": "OBJECT", "properties": {"goal": {"type": "STRING"}}, "required": ["goal"]},
    },
    {
        "name": "save_memory",
        "description": "Silent memory tool",
        "parameters": {"type": "OBJECT", "properties": {"key": {"type": "STRING"}}, "required": ["key"]},
    },
    {
        "name": "web_search",
        "description": "Search the web",
        "parameters": {
            "type": "OBJECT",
            "properties": {"query": {"type": "STRING", "description": "q"}},
            "required": ["query"],
        },
    },
    {
        "name": "browser_control",
        "description": "Browser control",
        "parameters": {
            "type": "OBJECT",
            "properties": {"action": {"type": "STRING", "description": "action"}},
            "required": ["action"],
        },
    },
    {
        "name": "internal_helper",
        "description": "internal",
        "parameters": {"type": "OBJECT", "properties": {}, "required": []},
    },
]


class TestParseAction(unittest.TestCase):

    def test_tool_action(self):
        a = parse_action('{"type": "tool", "tool": "web_search", "parameters": {"query": "x"}}')
        self.assertEqual(a.type, "tool")
        self.assertEqual(a.tool, "web_search")
        self.assertEqual(a.parameters, {"query": "x"})
        self.assertIsNone(a.parse_error)

    def test_finish_action(self):
        a = parse_action('{"type": "finish", "answer": "All done, sir."}')
        self.assertEqual(a.type, "finish")
        self.assertEqual(a.answer, "All done, sir.")
        self.assertIsNone(a.parse_error)

    def test_finish_with_non_string_answer(self):
        a = parse_action('{"type": "finish", "answer": 42}')
        self.assertEqual(a.type, "finish")
        self.assertEqual(a.answer, "42")

    def test_markdown_fenced_json(self):
        a = parse_action('```json\n{"type": "tool", "tool": "x", "parameters": {}}\n```')
        self.assertEqual(a.type, "tool")
        self.assertEqual(a.tool, "x")

    def test_json_embedded_in_prose(self):
        a = parse_action('Here you go: {"type": "finish", "answer": "ok"} cheers')
        self.assertEqual(a.type, "finish")
        self.assertEqual(a.answer, "ok")

    def test_malformed_json(self):
        a = parse_action("{not valid json")
        self.assertEqual(a.type, "invalid")
        self.assertIsNotNone(a.parse_error)

    def test_empty_string(self):
        a = parse_action("")
        self.assertEqual(a.type, "invalid")
        self.assertIsNotNone(a.parse_error)

    def test_none(self):
        a = parse_action(None)
        self.assertEqual(a.type, "invalid")
        self.assertIsNotNone(a.parse_error)

    def test_top_level_not_object(self):
        a = parse_action('[1, 2, 3]')
        self.assertEqual(a.type, "invalid")
        self.assertIsNotNone(a.parse_error)

    def test_unknown_type(self):
        a = parse_action('{"type": "wave", "foo": "bar"}')
        self.assertEqual(a.type, "invalid")
        self.assertIn("Unknown action type", a.parse_error)

    def test_tool_missing_name(self):
        a = parse_action('{"type": "tool", "parameters": {}}')
        self.assertEqual(a.type, "invalid")
        self.assertIn("missing 'tool'", a.parse_error)

    def test_tool_with_null_parameters_defaults_to_empty_dict(self):
        a = parse_action('{"type": "tool", "tool": "x", "parameters": null}')
        self.assertEqual(a.type, "tool")
        self.assertEqual(a.parameters, {})

    def test_tool_with_non_dict_parameters_is_invalid(self):
        a = parse_action('{"type": "tool", "tool": "x", "parameters": "oops"}')
        self.assertEqual(a.type, "invalid")
        self.assertIn("must be an object", a.parse_error)

    def test_finish_with_empty_answer_keeps_empty_string(self):
        a = parse_action('{"type": "finish", "answer": ""}')
        self.assertEqual(a.type, "finish")
        self.assertEqual(a.answer, "")


class TestToolRegistry(unittest.TestCase):

    def test_blocks_agent_task_by_default(self):
        registry = build_tool_registry(DECLARATIONS)
        names = [t["name"] for t in registry]
        self.assertNotIn("agent_task", names)
        self.assertNotIn("save_memory", names)

    def test_keeps_normal_tools(self):
        registry = build_tool_registry(DECLARATIONS)
        names = [t["name"] for t in registry]
        self.assertIn("web_search", names)
        self.assertIn("browser_control", names)

    def test_explicit_block_list(self):
        registry = build_tool_registry(DECLARATIONS, blocked=("internal_helper",))
        names = [t["name"] for t in registry]
        self.assertNotIn("internal_helper", names)
        self.assertIn("web_search", names)

    def test_preserves_description_and_parameters(self):
        registry = build_tool_registry(DECLARATIONS)
        ws = next(t for t in registry if t["name"] == "web_search")
        self.assertEqual(ws["description"], "Search the web")
        self.assertIn("query", ws["parameters"]["properties"])

    def test_skips_entries_without_name(self):
        decls = [{"description": "no name"}]
        self.assertEqual(build_tool_registry(decls), [])

    def test_registry_prompt_contains_schemas(self):
        registry = build_tool_registry(DECLARATIONS)
        prompt = format_registry_for_prompt(registry)
        self.assertIn("web_search", prompt)
        self.assertIn("query", prompt)
        self.assertIn("(required)", prompt)

    def test_empty_registry_message(self):
        self.assertEqual(format_registry_for_prompt([]), "(no tools available)")


class TestObservationFormatting(unittest.TestCase):

    def test_truncate_long_text(self):
        text, truncated = truncate_observation("x" * 5000, 100)
        self.assertTrue(truncated)
        self.assertLess(len(text), 300)
        self.assertIn("truncated", text)

    def test_no_truncate_when_short(self):
        text, truncated = truncate_observation("short", 100)
        self.assertFalse(truncated)
        self.assertEqual(text, "short")

    def test_truncate_handles_none(self):
        text, truncated = truncate_observation(None, 100)
        self.assertEqual(text, "")
        self.assertFalse(truncated)

    def test_truncate_zero_max_len_returns_input(self):
        text, truncated = truncate_observation("hello", 0)
        self.assertEqual(text, "hello")
        self.assertFalse(truncated)

    def test_format_observation_prepends_error_label(self):
        text, _ = format_observation("boom", max_len=100, is_error=True)
        self.assertTrue(text.startswith("ERROR:"))

    def test_format_observation_does_not_double_label(self):
        text, _ = format_observation("Error: already labeled", max_len=100, is_error=True)
        self.assertFalse(text.startswith("ERROR:ERROR"))

    def test_summarize_parameters_short(self):
        s = summarize_parameters({"a": 1, "b": "two"})
        self.assertIn('"a"', s)
        self.assertIn('"b"', s)

    def test_summarize_parameters_truncates(self):
        s = summarize_parameters({"x": "y" * 500}, max_len=20)
        self.assertLessEqual(len(s), 21)
        self.assertTrue(s.endswith("…"))


class TestReactIntegration(unittest.TestCase):

    def _registry(self):
        return build_tool_registry(DECLARATIONS)

    def _run(self, model_caller, executor, max_iterations=5, max_parse_retries=2):
        loop = ReactAgentLoop(
            registry=self._registry(),
            model_caller=model_caller,
            max_iterations=max_iterations,
            max_parse_retries=max_parse_retries,
            observation_max_len=1500,
        )
        return asyncio.run(loop.run("test goal", executor))

    def test_finish_on_first_iteration(self):
        async def model(_sys, _user):
            return '{"type": "finish", "answer": "Hello, sir."}'

        async def executor(_t, _p):
            raise AssertionError("executor should not run when finish comes first")

        result = self._run(model, executor)
        self.assertEqual(result.status, "finished")
        self.assertEqual(result.answer, "Hello, sir.")
        self.assertEqual(result.iterations, 1)
        self.assertEqual(result.observations, [])

    def test_tool_then_finish(self):
        calls = []

        async def model(_sys, user):
            calls.append(user)
            if len(calls) == 1:
                return '{"type": "tool", "tool": "web_search", "parameters": {"query": "x"}}'
            return '{"type": "finish", "answer": "result"}'

        async def executor(tool, params):
            return f"RESULT-{tool}-{params.get('query', '?')}"

        result = self._run(model, executor)
        self.assertEqual(result.status, "finished")
        self.assertEqual(result.iterations, 2)
        self.assertEqual(len(result.observations), 1)
        self.assertEqual(result.observations[0].tool, "web_search")
        self.assertIn("RESULT-web_search-x", result.observations[0].result)

    def test_blocked_agent_task_becomes_observation(self):
        calls = []

        async def model(_sys, _user):
            calls.append(1)
            if len(calls) == 1:
                return '{"type": "tool", "tool": "agent_task", "parameters": {"goal": "loop"}}'
            return '{"type": "finish", "answer": "aborted recursive task"}'

        async def executor(_t, _p):
            raise AssertionError("executor must not run for blocked tools")

        result = self._run(model, executor)
        self.assertEqual(result.status, "finished")
        self.assertEqual(len(result.observations), 1)
        self.assertTrue(result.observations[0].blocked)
        self.assertIn("blocked", result.observations[0].result.lower())

    def test_blocked_save_memory_becomes_observation(self):
        calls = []

        async def model(_sys, _user):
            calls.append(1)
            if len(calls) == 1:
                return '{"type": "tool", "tool": "save_memory", "parameters": {"key": "x"}}'
            return '{"type": "finish", "answer": "done"}'

        async def executor(_t, _p):
            raise AssertionError("executor must not run for blocked tools")

        result = self._run(model, executor)
        self.assertEqual(len(result.observations), 1)
        self.assertTrue(result.observations[0].blocked)
        self.assertEqual(result.observations[0].tool, "save_memory")

    def test_unknown_tool_becomes_observation(self):
        calls = []

        async def model(_sys, _user):
            calls.append(1)
            if len(calls) == 1:
                return '{"type": "tool", "tool": "no_such_tool", "parameters": {}}'
            return '{"type": "finish", "answer": "done"}'

        async def executor(_t, _p):
            raise AssertionError("executor must not run for unknown tools")

        result = self._run(model, executor)
        self.assertEqual(len(result.observations), 1)
        self.assertTrue(result.observations[0].is_error)
        self.assertIn("not available", result.observations[0].result)

    def test_malformed_then_valid(self):
        calls = []

        async def model(_sys, _user):
            calls.append(1)
            if len(calls) == 1:
                return "not json at all"
            return '{"type": "finish", "answer": "recovered"}'

        async def executor(_t, _p):
            return "ok"

        result = self._run(model, executor)
        self.assertEqual(result.status, "finished")
        self.assertEqual(len(result.observations), 1)
        self.assertTrue(result.observations[0].is_error)
        self.assertIn("Malformed", result.observations[0].result)

    def test_too_many_malformed_outputs_aborts(self):
        async def model(_sys, _user):
            return "definitely not json"

        async def executor(_t, _p):
            return "ok"

        result = self._run(model, executor, max_parse_retries=2)
        self.assertEqual(result.status, "error")
        self.assertIn("malformed", result.answer.lower())

    def test_max_iterations_returns_clear_message(self):
        async def model(_sys, _user):
            return '{"type": "tool", "tool": "web_search", "parameters": {"query": "x"}}'

        async def executor(_t, _p):
            return "always more to do"

        result = self._run(model, executor, max_iterations=3)
        self.assertEqual(result.status, "max_iterations")
        self.assertIn("did not complete", result.answer)
        self.assertEqual(result.iterations, 3)
        self.assertEqual(len(result.observations), 3)

    def test_cancellation_before_model_call(self):
        cancel = threading.Event()
        cancel.set()

        async def model(_sys, _user):
            raise AssertionError("model must not be called when cancelled")

        async def executor(_t, _p):
            return "ok"

        registry = self._registry()
        loop = ReactAgentLoop(registry=registry, model_caller=model, max_iterations=5)
        result = asyncio.run(loop.run("goal", executor, cancel_flag=cancel))
        self.assertEqual(result.status, "cancelled")
        self.assertEqual(result.iterations, 0)
        self.assertEqual(result.observations, [])

    def test_cancellation_during_iterations(self):
        cancel = threading.Event()
        call_count = {"n": 0}

        async def model(_sys, _user):
            call_count["n"] += 1
            if call_count["n"] == 2:
                cancel.set()
            return '{"type": "tool", "tool": "web_search", "parameters": {"query": "x"}}'

        async def executor(_t, _p):
            return "ok"

        registry = self._registry()
        loop = ReactAgentLoop(registry=registry, model_caller=model, max_iterations=10)
        result = asyncio.run(loop.run("goal", executor, cancel_flag=cancel))
        self.assertEqual(result.status, "cancelled")
        self.assertLessEqual(result.iterations, 3)

    def test_executor_exception_becomes_error_observation(self):
        async def model(_sys, _user):
            return '{"type": "tool", "tool": "web_search", "parameters": {"query": "x"}}'

        async def executor(_t, _p):
            raise RuntimeError("boom")

        registry = self._registry()
        loop = ReactAgentLoop(registry=registry, model_caller=model, max_iterations=3)
        result = asyncio.run(loop.run("goal", executor))
        self.assertEqual(result.status, "max_iterations")
        self.assertTrue(result.observations[0].is_error)
        self.assertIn("boom", result.observations[0].result)

    def test_observation_truncation_during_run(self):
        async def model(_sys, _user):
            return '{"type": "tool", "tool": "web_search", "parameters": {"query": "x"}}'

        async def executor(_t, _p):
            return "L" * 10_000

        registry = self._registry()
        loop = ReactAgentLoop(
            registry=registry,
            model_caller=model,
            max_iterations=2,
            observation_max_len=200,
        )
        result = asyncio.run(loop.run("goal", executor))
        self.assertEqual(len(result.observations), 2)
        self.assertTrue(result.observations[0].truncated)
        self.assertLess(len(result.observations[0].result), 1000)

    def test_observation_summary_includes_iteration_and_tool(self):
        async def model(_sys, _user):
            return '{"type": "tool", "tool": "web_search", "parameters": {"query": "x"}}'

        async def executor(_t, _p):
            return "ok"

        registry = self._registry()
        loop = ReactAgentLoop(registry=registry, model_caller=model, max_iterations=2)
        result = asyncio.run(loop.run("goal", executor))
        obs = result.observations[0]
        prompt_repr = obs.to_prompt()
        self.assertIn("Iteration 1", prompt_repr)
        self.assertIn("web_search", prompt_repr)

    def test_react_system_prompt_contains_registry(self):
        registry = self._registry()
        prompt = REACT_SYSTEM_PROMPT.format(tool_registry=format_registry_for_prompt(registry))
        self.assertIn("web_search", prompt)
        self.assertIn("browser_control", prompt)
        self.assertIn("save_memory", prompt)
        self.assertIn("finish", prompt)
        self.assertIn("agent_task", prompt)


class TestPlanContext(unittest.TestCase):

    def _registry(self):
        return build_tool_registry(DECLARATIONS)

    def _loop(self, model_caller, **kwargs):
        return ReactAgentLoop(
            registry=self._registry(),
            model_caller=model_caller,
            max_iterations=kwargs.pop("max_iterations", 3),
            max_parse_retries=kwargs.pop("max_parse_retries", 2),
            observation_max_len=1500,
        )

    def test_plan_context_appears_in_first_user_message(self):
        captured = []

        async def model(_sys, user):
            captured.append(user)
            return '{"type": "finish", "answer": "ok"}'

        async def executor(_t, _p):
            return "x"

        loop = self._loop(model)
        asyncio.run(loop.run(
            "test goal",
            executor,
            plan_context="Step 1: search\nStep 2: finish",
        ))
        self.assertEqual(len(captured), 1)
        self.assertIn("PLANNED APPROACH", captured[0])
        self.assertIn("Step 1: search", captured[0])
        self.assertIn("USER GOAL", captured[0])

    def test_no_plan_context_keeps_existing_format(self):
        captured = []

        async def model(_sys, user):
            captured.append(user)
            return '{"type": "finish", "answer": "ok"}'

        async def executor(_t, _p):
            return "x"

        loop = self._loop(model)
        asyncio.run(loop.run("test goal", executor))
        self.assertEqual(len(captured), 1)
        self.assertNotIn("PLANNED APPROACH", captured[0])
        self.assertIn("USER GOAL", captured[0])

    def test_empty_plan_context_does_not_prepend_block(self):
        captured = []

        async def model(_sys, user):
            captured.append(user)
            return '{"type": "finish", "answer": "ok"}'

        async def executor(_t, _p):
            return "x"

        loop = self._loop(model)
        asyncio.run(loop.run("test goal", executor, plan_context="   "))
        self.assertNotIn("PLANNED APPROACH", captured[0])

    def test_plan_context_does_not_change_blocked_tool_behavior(self):
        calls = []

        async def model(_sys, _user):
            calls.append(1)
            if len(calls) == 1:
                return '{"type": "tool", "tool": "agent_task", "parameters": {"goal": "x"}}'
            return '{"type": "finish", "answer": "aborted"}'

        async def executor(_t, _p):
            raise AssertionError("executor must not run for blocked tools")

        loop = self._loop(model)
        result = asyncio.run(loop.run(
            "test goal", executor,
            plan_context="Step 1: agent_task",
        ))
        self.assertEqual(result.status, "finished")
        self.assertEqual(len(result.observations), 1)
        self.assertTrue(result.observations[0].blocked)

    def test_plan_context_does_not_change_iteration_cap(self):
        async def model(_sys, _user):
            return '{"type": "tool", "tool": "web_search", "parameters": {"query": "x"}}'

        async def executor(_t, _p):
            return "more"

        loop = self._loop(model, max_iterations=3)
        result = asyncio.run(loop.run(
            "test goal", executor,
            plan_context="Step 1: search",
        ))
        self.assertEqual(result.status, "max_iterations")
        self.assertEqual(result.iterations, 3)

    def test_plan_context_does_not_change_cancellation(self):
        cancel = threading.Event()
        cancel.set()

        async def model(_sys, _user):
            raise AssertionError("model must not be called when cancelled")

        async def executor(_t, _p):
            return "x"

        loop = self._loop(model)
        result = asyncio.run(loop.run(
            "test goal", executor,
            cancel_flag=cancel,
            plan_context="Step 1: do something",
        ))
        self.assertEqual(result.status, "cancelled")
        self.assertEqual(result.iterations, 0)


if __name__ == "__main__":
    unittest.main()
