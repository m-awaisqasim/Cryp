import asyncio
import json
import os
from datetime import datetime, timedelta
from threading import Lock
from pathlib import Path
import sys


def get_base_dir() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).parent
    return Path(__file__).resolve().parent.parent


BASE_DIR         = get_base_dir()
MEMORY_PATH      = BASE_DIR / "memory" / "long_term.json"
_lock            = Lock()
MAX_VALUE_LENGTH = 380
MEMORY_MAX_CHARS = 2200

def _empty_memory() -> dict:
    return {
        "identity":      {},
        "preferences":   {},
        "projects":      {},
        "relationships": {},
        "wishes":        {},
        "notes":         {},
    }

def load_memory() -> dict:
    if not MEMORY_PATH.exists():
        return _empty_memory()
    with _lock:
        try:
            data = json.loads(MEMORY_PATH.read_text(encoding="utf-8"))
            if isinstance(data, dict):
                base = _empty_memory()
                for key in base:
                    if key not in data:
                        data[key] = {}
                return data
            return _empty_memory()
        except Exception as e:
            print(f"[Memory] ⚠️ Load error: {e}")
            return _empty_memory()

def _all_entries(memory: dict) -> list[tuple]:
    entries = []
    for cat, items in memory.items():
        if not isinstance(items, dict):
            continue
        for key, entry in items.items():
            if isinstance(entry, dict) and "value" in entry:
                entries.append((cat, key, entry))
    return entries


def _trim_to_limit(memory: dict) -> dict:
    if len(json.dumps(memory, ensure_ascii=False)) <= MEMORY_MAX_CHARS:
        return memory
    entries = _all_entries(memory)
    entries.sort(key=lambda t: t[2].get("updated", "0000-00-00"))
    for cat, key, _ in entries:
        if len(json.dumps(memory, ensure_ascii=False)) <= MEMORY_MAX_CHARS:
            break
        del memory[cat][key]
        print(f"[Memory] 🗑️  Trimmed {cat}/{key}")
    return memory

def save_memory(memory: dict) -> None:
    if not isinstance(memory, dict):
        return
    memory = _trim_to_limit(memory)
    MEMORY_PATH.parent.mkdir(parents=True, exist_ok=True)
    with _lock:
        MEMORY_PATH.write_text(
            json.dumps(memory, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )


def _truncate_value(val: str) -> str:
    if isinstance(val, str) and len(val) > MAX_VALUE_LENGTH:
        return val[:MAX_VALUE_LENGTH].rstrip() + "…"
    return val


def _recursive_update(target: dict, updates: dict) -> bool:
    changed = False
    for key, value in updates.items():
        if value is None:
            continue
        if isinstance(value, str) and not value.strip():
            continue
        if isinstance(value, dict) and "value" not in value:
            if key not in target or not isinstance(target[key], dict):
                target[key] = {}
                changed = True
            if _recursive_update(target[key], value):
                changed = True
        else:
            new_val  = _truncate_value(str(value["value"] if isinstance(value, dict) else value))
            entry    = {"value": new_val, "updated": datetime.now().strftime("%Y-%m-%d")}
            existing = target.get(key, {})
            if not isinstance(existing, dict) or existing.get("value") != new_val:
                target[key] = entry
                changed = True
    return changed


def update_memory(memory_update: dict) -> dict:
    if not isinstance(memory_update, dict) or not memory_update:
        return load_memory()
    memory = load_memory()
    if _recursive_update(memory, memory_update):
        save_memory(memory)
        print(f"[Memory] 💾 Saved: {list(memory_update.keys())}")
    return memory

def format_memory_for_prompt(memory: dict | None) -> str:
    if not memory:
        return ""

    lines = []

    identity  = memory.get("identity", {})
    id_fields = ["name", "age", "birthday", "city", "job", "language", "school", "nationality"]
    for field in id_fields:
        entry = identity.get(field)
        if entry:
            val = entry.get("value") if isinstance(entry, dict) else entry
            if val:
                lines.append(f"{field.title()}: {val}")
    for key, entry in identity.items():
        if key in id_fields:
            continue
        val = entry.get("value") if isinstance(entry, dict) else entry
        if val:
            lines.append(f"{key.replace('_', ' ').title()}: {val}")

    prefs = memory.get("preferences", {})
    if prefs:
        lines.append("")
        lines.append("Preferences:")
        for key, entry in list(prefs.items())[:15]:
            val = entry.get("value") if isinstance(entry, dict) else entry
            if val:
                lines.append(f"  - {key.replace('_', ' ').title()}: {val}")

    projects = memory.get("projects", {})
    if projects:
        lines.append("")
        lines.append("Active Projects / Goals:")
        for key, entry in list(projects.items())[:8]:
            val = entry.get("value") if isinstance(entry, dict) else entry
            if val:
                lines.append(f"  - {key.replace('_', ' ').title()}: {val}")

    rels = memory.get("relationships", {})
    if rels:
        lines.append("")
        lines.append("People in their life:")
        for key, entry in list(rels.items())[:10]:
            val = entry.get("value") if isinstance(entry, dict) else entry
            if val:
                lines.append(f"  - {key.replace('_', ' ').title()}: {val}")

    wishes = memory.get("wishes", {})
    if wishes:
        lines.append("")
        lines.append("Wishes / Plans / Wants:")
        for key, entry in list(wishes.items())[:8]:
            val = entry.get("value") if isinstance(entry, dict) else entry
            if val:
                lines.append(f"  - {key.replace('_', ' ').title()}: {val}")

    notes = memory.get("notes", {})
    if notes:
        lines.append("")
        lines.append("Other notes:")
        for key, entry in list(notes.items())[:8]:
            val = entry.get("value") if isinstance(entry, dict) else entry
            if val:
                lines.append(f"  - {key}: {val}")

    if not lines:
        return ""

    header = "[WHAT YOU KNOW ABOUT THIS PERSON — use naturally, never recite like a list]\n"
    result = header + "\n".join(lines)
    if len(result) > 2000:
        result = result[:1997] + "…"

    return result + "\n"

def remember(key: str, value: str, category: str = "notes") -> str:
    valid = {"identity", "preferences", "projects", "relationships", "wishes", "notes"}
    if category not in valid:
        category = "notes"
    update_memory({category: {key: {"value": value}}})
    return f"Remembered: {category}/{key} = {value}"


def forget(key: str, category: str = "notes") -> str:
    memory = load_memory()
    cat    = memory.get(category, {})
    if key in cat:
        del cat[key]
        memory[category] = cat
        save_memory(memory)
        return f"Forgotten: {category}/{key}"
    return f"Not found: {category}/{key}"


forget_memory = forget



EPISODIC_DIR_NAME            = "episodic"
EPISODIC_PROMPT_DAYS         = 3
EPISODIC_RECENT_DAYS         = 7
EPISODE_MAX_CHARS            = 2000
EPISODES_PROMPT_MAX_CHARS    = 1500
DEFAULT_RECENT_EPISODES      = 5
MAX_EPISODE_FILES            = 500
_episodic_lock               = Lock()


class EpisodicStore:

    def __init__(self, base_dir: Path | None = None) -> None:
        root = Path(base_dir) if base_dir else BASE_DIR
        self._dir = root / "memory" / EPISODIC_DIR_NAME
        try:
            self._dir.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            print(f"[episodic] mkdir failed: {e}")

    @property
    def directory(self) -> Path:
        return self._dir

    def _normalize(self, episode: dict) -> dict:
        ep = dict(episode or {})
        ts = ep.get("timestamp") or datetime.now().isoformat(timespec="seconds")
        ep["timestamp"]   = str(ts)
        ep["summary"]     = str(ep.get("summary") or "").strip()
        tools             = ep.get("tools_used") or []
        if not isinstance(tools, list):
            tools = [str(tools)]
        ep["tools_used"]  = [str(t) for t in tools if t]
        ep["goal"]        = str(ep.get("goal") or "").strip()
        return ep

    def _file_for(self, timestamp: str) -> Path:
        day = (timestamp or "")[:10] or datetime.now().strftime("%Y-%m-%d")
        return self._dir / f"{day}.json"

    def save_episode(self, episode: dict) -> None:
        try:
            ep   = self._normalize(episode)
            path = self._file_for(ep["timestamp"])
            with _episodic_lock:
                self._dir.mkdir(parents=True, exist_ok=True)
                existing: list = []
                if path.exists():
                    try:
                        loaded = json.loads(path.read_text(encoding="utf-8"))
                        if isinstance(loaded, list):
                            existing = loaded
                        elif isinstance(loaded, dict):
                            existing = [loaded]
                    except Exception as e:
                        print(f"[episodic] could not parse {path.name}, starting fresh: {e}")
                        existing = []
                existing.append(ep)
                path.write_text(
                    json.dumps(existing, indent=2, ensure_ascii=False),
                    encoding="utf-8",
                )
        except Exception as e:
            print(f"[episodic] save_episode failed: {e}")

    def _list_files_desc(self) -> list[Path]:
        try:
            files = sorted(self._dir.glob("*.json"), key=lambda p: p.name, reverse=True)
            return [p for p in files if p.is_file()]
        except Exception:
            return []

    def get_recent_episodes(self, days: int = EPISODIC_RECENT_DAYS) -> list[dict]:
        if days <= 0:
            return []
        cutoff = (datetime.now().date() - timedelta(days=days - 1)).isoformat()
        out: list[dict] = []
        for path in self._list_files_desc():
            day = path.stem
            if day < cutoff:
                continue
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
            except Exception:
                continue
            items = data if isinstance(data, list) else [data] if isinstance(data, dict) else []
            for item in reversed(items):
                if isinstance(item, dict):
                    out.append(item)
        out.sort(key=lambda e: str(e.get("timestamp", "")), reverse=True)
        return out

    def get_latest_episodes(self, n: int = DEFAULT_RECENT_EPISODES) -> list[dict]:
        if n <= 0:
            return []
        out: list[dict] = []
        for path in self._list_files_desc():
            if len(out) >= n:
                break
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
            except Exception:
                continue
            items = data if isinstance(data, list) else [data] if isinstance(data, dict) else []
            for item in reversed(items):
                if isinstance(item, dict):
                    out.append(item)
                    if len(out) >= n:
                        break
        out.sort(key=lambda e: str(e.get("timestamp", "")), reverse=True)
        return out[:n]

    def prune(self, keep_last: int = MAX_EPISODE_FILES) -> int:
        try:
            files = sorted(self._dir.glob("*.json"), key=lambda p: p.name, reverse=True)
            extra = len(files) - keep_last
            if extra <= 0:
                return 0
            to_delete = list(reversed(files))[:extra]
            deleted = 0
            with _episodic_lock:
                for p in to_delete:
                    try:
                        p.unlink()
                        deleted += 1
                    except Exception as e:
                        print(f"[episodic] prune failed for {p.name}: {e}")
            return deleted
        except Exception as e:
            print(f"[episodic] prune error: {e}")
            return 0

    def format_for_prompt(self, days: int = EPISODIC_PROMPT_DAYS) -> str:
        episodes = self.get_recent_episodes(days=days)
        if not episodes:
            return ""
        by_day: dict[str, list[str]] = {}
        order: list[str] = []
        for ep in episodes:
            ts  = str(ep.get("timestamp", ""))
            day = ts[:10] or datetime.now().strftime("%Y-%m-%d")
            summary = str(ep.get("summary") or "").strip()
            if not summary:
                continue
            if day not in by_day:
                by_day[day] = []
                order.append(day)
            by_day[day].append(summary)
        if not order:
            return ""
        lines = ["[RECENT ACTIVITY]"]
        for day in order:
            joined = " | ".join(by_day[day])
            if len(joined) > 280:
                joined = joined[:277] + "..."
            lines.append(f"{day}: {joined}")
        return "\n".join(lines)


_EPISODIC_STORE: EpisodicStore | None = None


def get_episodic_store() -> EpisodicStore:
    global _EPISODIC_STORE
    if _EPISODIC_STORE is None:
        _EPISODIC_STORE = EpisodicStore()
    return _EPISODIC_STORE


def format_full_memory_for_prompt(semantic_memory: dict | None) -> str:
    semantic = format_memory_for_prompt(semantic_memory) or ""
    try:
        episodic = format_episodes_for_prompt(load_recent_episodes(_env_recent_count())) or ""
    except Exception as e:
        print(f"[episodic] format_full_memory_for_prompt failed: {e}")
        episodic = ""
    parts = [s for s in (semantic.strip(), episodic.strip()) if s]
    return "\n\n".join(parts)


def _env_recent_count() -> int:
    try:
        return int(os.getenv("EPISODIC_RECENT_COUNT", str(DEFAULT_RECENT_EPISODES)))
    except Exception:
        return DEFAULT_RECENT_EPISODES


def load_recent_episodes(n: int = DEFAULT_RECENT_EPISODES) -> list[dict]:
    try:
        return get_episodic_store().get_latest_episodes(n=n)
    except Exception as e:
        print(f"[episodic] load_recent_episodes failed: {e}")
        return []


def search_episodes(query: str, limit: int = 5) -> list[dict]:
    try:
        q       = (query or "").lower().strip()
        if not q:
            return []
        episodes = get_episodic_store().get_latest_episodes(n=max(limit * 4, 50))
        matches: list[dict] = []
        for ep in episodes:
            fields: list[str] = []
            summary = ep.get("summary")
            if summary:
                fields.append(str(summary))
            for field in ("topics", "goal"):
                v = ep.get(field)
                if isinstance(v, list):
                    fields.extend(str(x) for x in v if x)
                elif v:
                    fields.append(str(v))
            tools = ep.get("tools_used")
            if isinstance(tools, list):
                fields.extend(str(t) for t in tools if t)
            haystack = " ".join(fields).lower()
            if q in haystack:
                matches.append(ep)
            if len(matches) >= limit:
                break
        return matches
    except Exception as e:
        print(f"[episodic] search_episodes failed: {e}")
        return []


def format_episodes_for_prompt(
    episodes: list[dict] | None,
    max_chars: int = EPISODES_PROMPT_MAX_CHARS,
) -> str:
    if not episodes:
        return ""

    def _date_of(ep: dict) -> str:
        ts = str(ep.get("timestamp") or ep.get("started_at") or "")
        return ts[:10] or datetime.now().strftime("%Y-%m-%d")

    def _topics_of(ep: dict) -> str:
        t = ep.get("topics")
        if isinstance(t, list) and t:
            return ", ".join(str(x) for x in t if x)
        g = ep.get("goal")
        if g:
            return str(g)
        tools = ep.get("tools_used")
        if isinstance(tools, list) and tools:
            return "tools: " + ", ".join(str(x) for x in tools if x)
        return ""

    def _first_sentence(text: str) -> str:
        s = str(text or "").strip()
        if not s:
            return ""
        for sep in (". ", "! ", "? ", "\n"):
            if sep in s:
                s = s.split(sep, 1)[0]
                break
        return s.strip()[:240]

    # Newest first; trim oldest if total exceeds max_chars
    eps = list(episodes)
    eps.sort(key=_date_of, reverse=True)

    lines = ["[RECENT CONVERSATIONS — reference naturally, do not recite]"]
    rendered: list[str] = []
    for ep in eps:
        date  = _date_of(ep)
        first = _first_sentence(ep.get("summary", ""))
        topics = _topics_of(ep)
        line = f"- {date}: {first}"
        if topics:
            line += f" [topics: {topics}]"
        rendered.append(line)

    total = sum(len(l) + 1 for l in lines) + sum(len(l) + 1 for l in rendered)
    while rendered and total > max_chars:
        rendered.pop()
        total = sum(len(l) + 1 for l in lines) + sum(len(l) + 1 for l in rendered)

    if not rendered:
        return ""
    lines.extend(rendered)
    return "\n".join(lines)


def prune_episodes(keep_last: int = MAX_EPISODE_FILES) -> int:
    try:
        return get_episodic_store().prune(keep_last=keep_last)
    except Exception as e:
        print(f"[episodic] prune_episodes failed: {e}")
        return 0



_SUMMARY_PROMPT = (
    "Summarize this conversation in 1-2 sentences focusing on what "
    "the user asked for and what was accomplished. Be specific about "
    "tools used and goals achieved. Output only the summary text, "
    "nothing else.\n\nTranscript:\n{transcript}"
)


def _fallback_episode() -> dict:
    return {
        "timestamp":  datetime.now().isoformat(timespec="seconds"),
        "summary":    f"Session on {datetime.now().strftime('%Y-%m-%d')}",
        "tools_used": [],
        "goal":       "",
    }


def _call_gemini_sync(prompt_text: str, api_key: str, model: str) -> str:
    import google.generativeai as genai
    genai.configure(api_key=api_key)
    gm   = genai.GenerativeModel(model)
    resp = gm.generate_content(prompt_text)
    text = getattr(resp, "text", None)
    if not text and getattr(resp, "candidates", None):
        try:
            text = resp.candidates[0].content.parts[0].text
        except Exception:
            text = None
    return (text or "").strip()


async def summarize_session(
    transcript: list[str],
    api_key: str,
    model: str = "gemini-2.0-flash",
) -> dict:
    episode = _fallback_episode()
    try:
        lines = [str(t) for t in (transcript or []) if str(t).strip()]
        if not lines:
            return episode
        transcript_text = "\n".join(lines)[-6000:]
        prompt_text     = _SUMMARY_PROMPT.format(transcript=transcript_text)
        if not api_key:
            return episode
        loop    = asyncio.get_event_loop()
        summary = await loop.run_in_executor(
            None, _call_gemini_sync, prompt_text, api_key, model
        )
        if summary:
            episode["summary"] = summary.strip()[:600]
        return episode
    except Exception as e:
        print(f"[episodic] summarize_session failed: {e}")
        return episode