import feedparser
import json
import re
from datetime import datetime
from pathlib import Path

from actions.trading.market_data import _base_dir

FEEDS = [
    "https://www.coindesk.com/arc/outboundfeeds/rss/",
    "https://cointelegraph.com/rss",
]
SEEN_PATH = _base_dir() / "memory" / "news_seen.json"


def _load_seen() -> set:
    if not SEEN_PATH.exists():
        return set()
    try:
        return set(json.loads(SEEN_PATH.read_text(encoding="utf-8") or "[]"))
    except Exception:
        return set()


def _save_seen(seen: set):
    SEEN_PATH.parent.mkdir(parents=True, exist_ok=True)
    SEEN_PATH.write_text(
        json.dumps(list(seen)[-200:]), encoding="utf-8"
    )


def _fetch_entries(limit_per_feed=10) -> list[dict]:
    entries = []
    for url in FEEDS:
        try:
            feed = feedparser.parse(url)
            for e in feed.entries[:limit_per_feed]:
                entries.append({
                    "title": e.get("title", ""),
                    "summary": e.get("summary", ""),
                    "link": e.get("link", ""),
                })
        except Exception:
            continue
    return entries


def _call_gemini(prompt: str, system: str = "", model_name: str = "gemini-2.5-flash") -> str:
    from config.settings import GEMINI_API_KEY
    from core import gemini_compat as genai
    genai.configure(api_key=GEMINI_API_KEY)
    if system:
        model = genai.GenerativeModel(model_name=model_name, system_instruction=system)
    else:
        model = genai.GenerativeModel(model_name)
    response = model.generate_content(prompt)
    return response.text.strip()


def news_filter(parameters: dict, player=None, **kwargs) -> str:
    seen = _load_seen()
    entries = _fetch_entries()
    new_entries = [e for e in entries if e["title"] not in seen]
    if not new_entries:
        return "No new crypto news since last check, sir."

    headlines_block = "\n".join(
        f"- {e['title']}: {e['summary'][:150]}" for e in new_entries[:15]
    )
    prompt = (
        "Here are recent crypto news headlines with short summaries:\n"
        f"{headlines_block}\n\n"
        "Pick the 3 most market-relevant items (regulatory news, major exchange "
        "events, BTC/ETH-specific catalysts) — skip generic price-recap fluff and "
        "listicles. For each, give one spoken-friendly sentence. Return plain text, "
        "no markdown, no numbering, one sentence per line."
    )
    summary = _call_gemini(
        prompt,
        system="You are a crypto market analyst. Filter news for trading relevance.",
    )

    for e in new_entries:
        seen.add(e["title"])
    _save_seen(seen)

    return summary
