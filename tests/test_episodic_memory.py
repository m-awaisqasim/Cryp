import json
import os
import shutil
import sys
import tempfile
import unittest
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import patch

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from memory.memory_manager import (
    EpisodicStore,
    load_recent_episodes,
    search_episodes,
    format_episodes_for_prompt,
    prune_episodes,
    EPISODES_PROMPT_MAX_CHARS,
)


class EpisodicStoreSaveTest(unittest.TestCase):

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="cryp_ep_"))
        self.store = EpisodicStore(base_dir=self.tmp)

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_save_then_load_round_trip(self):
        ep = {
            "timestamp":  "2026-06-01T14:32:00",
            "summary":    "Test summary about websockets",
            "tools_used": ["web_search", "file_controller"],
            "goal":       "fix bug",
        }
        self.store.save_episode(ep)
        loaded = self.store.get_recent_episodes(days=30)
        self.assertEqual(len(loaded), 1)
        self.assertEqual(loaded[0]["summary"], "Test summary about websockets")
        self.assertEqual(loaded[0]["tools_used"], ["web_search", "file_controller"])

    def test_appends_same_day_instead_of_overwriting(self):
        ts = "2026-06-01T10:00:00"
        self.store.save_episode({"timestamp": ts, "summary": "first"})
        self.store.save_episode({"timestamp": ts, "summary": "second"})
        files = list((self.tmp / "memory" / "episodic").glob("*.json"))
        self.assertEqual(len(files), 1)
        data = json.loads(files[0].read_text(encoding="utf-8"))
        self.assertIsInstance(data, list)
        self.assertEqual(len(data), 2)
        summaries = {e["summary"] for e in data}
        self.assertEqual(summaries, {"first", "second"})

    def test_get_recent_returns_newest_first(self):
        self.store.save_episode({"timestamp": "2026-05-30T09:00:00", "summary": "older"})
        self.store.save_episode({"timestamp": "2026-06-01T09:00:00", "summary": "newest"})
        self.store.save_episode({"timestamp": "2026-05-31T09:00:00", "summary": "middle"})
        eps = self.store.get_recent_episodes(days=30)
        self.assertEqual([e["summary"] for e in eps], ["newest", "middle", "older"])

    def test_missing_dir_returns_empty(self):
        empty_dir = Path(tempfile.mkdtemp(prefix="cryp_empty_"))
        try:
            store = EpisodicStore(base_dir=empty_dir)
            shutil.rmtree(store.directory, ignore_errors=True)
            self.assertEqual(store.get_recent_episodes(days=7), [])
        finally:
            shutil.rmtree(empty_dir, ignore_errors=True)

    def test_malformed_file_is_skipped(self):
        (self.tmp / "memory" / "episodic").mkdir(parents=True, exist_ok=True)
        bad = self.tmp / "memory" / "episodic" / "2026-06-01.json"
        bad.write_text("not json at all {", encoding="utf-8")
        good_ts = "2026-05-30T12:00:00"
        self.store.save_episode({"timestamp": good_ts, "summary": "good"})
        eps = self.store.get_recent_episodes(days=30)
        self.assertEqual([e["summary"] for e in eps], ["good"])


class EpisodicStoreFormatTest(unittest.TestCase):

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="cryp_ep_"))
        self.store = EpisodicStore(base_dir=self.tmp)

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_empty_store_returns_empty_string(self):
        self.assertEqual(self.store.format_for_prompt(), "")

    def test_format_contains_header_and_dates(self):
        today     = datetime.now()
        yesterday = today - timedelta(days=1)
        self.store.save_episode({
            "timestamp": today.isoformat(timespec="seconds"),
            "summary":   "Searched for AI papers, saved results to Documents/",
        })
        self.store.save_episode({
            "timestamp": yesterday.isoformat(timespec="seconds"),
            "summary":   "Opened Chrome, played YouTube video about Python",
        })
        out = self.store.format_for_prompt(days=3)
        self.assertIn("[RECENT ACTIVITY]", out)
        self.assertIn(today.strftime("%Y-%m-%d"), out)
        self.assertIn(yesterday.strftime("%Y-%m-%d"), out)
        self.assertIn("AI papers", out)
        self.assertIn("Chrome", out)


class SessionSummarizerTest(unittest.TestCase):

    def _run(self, coro):
        import asyncio
        return asyncio.new_event_loop().run_until_complete(coro)

    def test_returns_fallback_on_empty_transcript(self):
        from memory.memory_manager import summarize_session
        ep = self._run(summarize_session([], api_key="fake-key"))
        self.assertIn("timestamp", ep)
        self.assertIn("summary", ep)
        self.assertEqual(ep["tools_used"], [])
        self.assertTrue(ep["summary"].startswith("Session on "))

    def test_returns_fallback_on_missing_api_key(self):
        from memory.memory_manager import summarize_session
        ep = self._run(summarize_session(["You: hi", "Jarvis: hello"], api_key=""))
        self.assertTrue(ep["summary"].startswith("Session on "))

    def test_uses_gemini_summary_when_available(self):
        from memory import memory_manager
        with patch.object(
            memory_manager, "_call_gemini_sync", return_value="User asked about websockets."
        ):
            ep = self._run(memory_manager.summarize_session(
                ["You: explain websockets", "Jarvis: sure"], api_key="fake-key"
            ))
        self.assertEqual(ep["summary"], "User asked about websockets.")

    def test_returns_fallback_on_gemini_exception(self):
        from memory import memory_manager

        def boom(*args, **kwargs):
            raise RuntimeError("api down")

        with patch.object(memory_manager, "_call_gemini_sync", side_effect=boom):
            ep = self._run(memory_manager.summarize_session(
                ["You: hi", "Jarvis: hello"], api_key="fake-key"
            ))
        self.assertTrue(ep["summary"].startswith("Session on "))


class MemoryManagerBackwardCompatTest(unittest.TestCase):

    def test_existing_functions_unchanged(self):
        import memory.memory_manager as mm
        for name in (
            "load_memory", "update_memory", "save_memory",
            "format_memory_for_prompt", "remember", "forget",
        ):
            self.assertTrue(hasattr(mm, name), f"missing existing function: {name}")
            self.assertTrue(callable(getattr(mm, name)))

    def test_format_full_memory_combines_sections(self):
        import memory.memory_manager as mm
        out = mm.format_full_memory_for_prompt({
            "identity": {"name": {"value": "Awais"}},
        })
        self.assertIn("Awais", out)

    def test_get_episodic_store_returns_singleton(self):
        import memory.memory_manager as mm
        a = mm.get_episodic_store()
        b = mm.get_episodic_store()
        self.assertIs(a, b)


class LoadRecentEpisodesTest(unittest.TestCase):

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="cryp_load_"))

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_count_based_newest_first(self):
        EpisodicStore(base_dir=self.tmp).save_episode({
            "timestamp": "2026-05-28T09:00:00", "summary": "oldest",
        })
        EpisodicStore(base_dir=self.tmp).save_episode({
            "timestamp": "2026-06-01T09:00:00", "summary": "newest",
        })
        EpisodicStore(base_dir=self.tmp).save_episode({
            "timestamp": "2026-05-31T09:00:00", "summary": "middle",
        })
        store = EpisodicStore(base_dir=self.tmp)
        with patch("memory.memory_manager._EPISODIC_STORE", store):
            eps = load_recent_episodes(n=2)
        self.assertEqual([e["summary"] for e in eps], ["newest", "middle"])

    def test_empty_when_no_files(self):
        store = EpisodicStore(base_dir=self.tmp)
        with patch("memory.memory_manager._EPISODIC_STORE", store):
            self.assertEqual(load_recent_episodes(n=5), [])


class SearchEpisodesTest(unittest.TestCase):

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="cryp_search_"))

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def _store(self) -> EpisodicStore:
        return EpisodicStore(base_dir=self.tmp)

    def test_case_insensitive_summary_match(self):
        s = self._store()
        s.save_episode({"timestamp": "2026-06-01T10:00:00", "summary": "WebSocket bug fix"})
        s.save_episode({"timestamp": "2026-06-01T11:00:00", "summary": "Pizza order"})
        with patch("memory.memory_manager._EPISODIC_STORE", s):
            hits = search_episodes("WEBSOCKET", limit=5)
        self.assertEqual(len(hits), 1)
        self.assertEqual(hits[0]["summary"], "WebSocket bug fix")

    def test_match_against_topics(self):
        s = self._store()
        s.save_episode({"timestamp": "2026-06-01T10:00:00",
                        "summary": "general",
                        "topics":  ["python", "asyncio"]})
        s.save_episode({"timestamp": "2026-06-01T11:00:00",
                        "summary": "other",
                        "topics":  ["cooking"]})
        with patch("memory.memory_manager._EPISODIC_STORE", s):
            hits = search_episodes("asyncio", limit=5)
        self.assertEqual(len(hits), 1)
        self.assertEqual(hits[0]["summary"], "general")

    def test_no_match_returns_empty(self):
        s = self._store()
        s.save_episode({"timestamp": "2026-06-01T10:00:00", "summary": "anything"})
        with patch("memory.memory_manager._EPISODIC_STORE", s):
            self.assertEqual(search_episodes("zzznotpresent", limit=3), [])

    def test_limit_caps_results(self):
        s = self._store()
        for i in range(5):
            s.save_episode({"timestamp": f"2026-06-0{i+1}T10:00:00", "summary": f"python talk {i}"})
        with patch("memory.memory_manager._EPISODIC_STORE", s):
            hits = search_episodes("python", limit=2)
        self.assertEqual(len(hits), 2)

    def test_never_raises_on_broken_store(self):
        broken = EpisodicStore(base_dir=self.tmp)
        with patch("memory.memory_manager._EPISODIC_STORE", broken), \
             patch.object(broken, "get_latest_episodes", side_effect=RuntimeError("boom")):
            self.assertEqual(search_episodes("python", limit=3), [])


class FormatEpisodesForPromptTest(unittest.TestCase):

    def test_empty_returns_empty_string(self):
        self.assertEqual(format_episodes_for_prompt([]), "")

    def test_includes_header_and_date_prefix(self):
        eps = [{"timestamp": "2026-06-01T10:00:00", "summary": "Did a thing.", "topics": ["x"]}]
        out = format_episodes_for_prompt(eps, max_chars=2000)
        self.assertIn("[RECENT CONVERSATIONS", out)
        self.assertIn("2026-06-01", out)
        self.assertIn("Did a thing", out)
        self.assertIn("topics: x", out)

    def test_respects_max_chars(self):
        eps = [
            {"timestamp": f"2026-06-{i:02d}T10:00:00",
             "summary":   "X" * 200}
            for i in range(1, 11)
        ]
        out = format_episodes_for_prompt(eps, max_chars=500)
        self.assertLessEqual(len(out), 500)
        # header should be present; at least one newest line should be kept
        self.assertIn("[RECENT CONVERSATIONS", out)
        self.assertGreater(out.count("- 2026-"), 0)


class PruneEpisodesTest(unittest.TestCase):

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="cryp_prune_"))

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_under_limit_is_noop(self):
        store = EpisodicStore(base_dir=self.tmp)
        for d in range(1, 6):
            store.save_episode({"timestamp": f"2026-05-{d:02d}T10:00:00", "summary": f"d{d}"})
        with patch("memory.memory_manager._EPISODIC_STORE", store):
            deleted = prune_episodes(keep_last=500)
        self.assertEqual(deleted, 0)
        self.assertEqual(len(list(store.directory.glob("*.json"))), 5)

    def test_over_limit_deletes_oldest(self):
        store = EpisodicStore(base_dir=self.tmp)
        for d in range(1, 8):
            store.save_episode({"timestamp": f"2026-05-{d:02d}T10:00:00", "summary": f"d{d}"})
        with patch("memory.memory_manager._EPISODIC_STORE", store):
            deleted = prune_episodes(keep_last=3)
        self.assertEqual(deleted, 4)
        remaining = sorted(p.name for p in store.directory.glob("*.json"))
        self.assertEqual(remaining, ["2026-05-05.json", "2026-05-06.json", "2026-05-07.json"])

    def test_never_raises(self):
        broken = EpisodicStore(base_dir=self.tmp)
        with patch("memory.memory_manager._EPISODIC_STORE", broken), \
             patch.object(broken, "prune", side_effect=RuntimeError("boom")):
            self.assertEqual(prune_episodes(), 0)


class EndToEndShutdownFlowTest(unittest.TestCase):
    """
    Simulates the 7.4 manual verification:
    Have a short conversation, trigger shutdown, confirm a new
    episode file appears in memory/episodic/ with the expected fields.
    """

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="cryp_e2e_"))

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_shutdown_writes_episode_file(self):
        import asyncio
        from memory.memory_manager import summarize_session, get_episodic_store

        store = EpisodicStore(base_dir=self.tmp)
        with patch("memory.memory_manager._EPISODIC_STORE", store):
            episode = asyncio.new_event_loop().run_until_complete(
                summarize_session(
                    [
                        "You:     Open Spotify and play some lofi",
                        "Jarvis:  Opening Spotify now.",
                    ],
                    api_key="",
                )
            )
            store.save_episode(episode)

            files = list(store.directory.glob("*.json"))
            self.assertEqual(len(files), 1, "expected one dated episode file")
            data = json.loads(files[0].read_text(encoding="utf-8"))
            self.assertIsInstance(data, list)
            self.assertEqual(len(data), 1)
            ep = data[0]
            self.assertIn("timestamp", ep)
            self.assertIn("summary",   ep)
            self.assertIn("tools_used", ep)
            self.assertIsInstance(ep["tools_used"], list)
            self.assertEqual(ep["summary"].startswith("Session on "), True)


class BuildConfigEpisodicInjectionTest(unittest.TestCase):
    """
    Simulates the 7.5 manual verification:
    After a prior session has been recorded, the next connection's
    system instruction must contain the 'Recent conversations' block.
    """

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="cryp_cfg_"))

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_recent_conversations_block_appears(self):
        store = EpisodicStore(base_dir=self.tmp)
        store.save_episode({
            "timestamp": "2026-06-01T14:32:00",
            "summary":   "User asked Jarvis to summarize the README.",
            "topics":    ["docs", "summarization"],
        })

        with patch("memory.memory_manager._EPISODIC_STORE", store):
            n   = int(os.getenv("EPISODIC_RECENT_COUNT", "5"))
            eps = load_recent_episodes(n)
            block = format_episodes_for_prompt(eps)

        self.assertIn("[RECENT CONVERSATIONS", block)
        self.assertIn("2026-06-01",            block)
        self.assertIn("summarize the README",   block)
        self.assertIn("docs",                   block)

    def test_no_block_when_no_episodes(self):
        empty = EpisodicStore(base_dir=self.tmp)
        with patch("memory.memory_manager._EPISODIC_STORE", empty):
            block = format_episodes_for_prompt(load_recent_episodes(5))
        self.assertEqual(block, "")


if __name__ == "__main__":
    unittest.main()
