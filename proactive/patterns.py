import json
import sys
from collections import Counter
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from memory.memory_manager import query_patterns, save_patterns
from core.logger import get_logger

log = get_logger(__name__)


def detect_time_patterns(sessions: list[dict]) -> list[dict]:
    patterns = []
    time_buckets: dict[str, Counter] = {}
    for ep in sessions:
        ts = ep.get("started_at", "")
        if not ts:
            continue
        try:
            dt = datetime.fromisoformat(ts)
        except Exception:
            continue
        hour_key = f"{dt.hour:02d}:00"
        day_name = dt.strftime("%A")
        for tool in ep.get("tools_used", []):
            bucket_key = f"{tool}@{hour_key}"
            if bucket_key not in time_buckets:
                time_buckets[bucket_key] = Counter()
            time_buckets[bucket_key][day_name] += 1
    for bucket_key, days in time_buckets.items():
        total = sum(days.values())
        if total >= 3:
            tool, hour = bucket_key.split("@")
            patterns.append({
                "tool": tool,
                "time": hour,
                "days": dict(days),
                "frequency": total,
            })
    return patterns


def detect_frequency_patterns(sessions: list[dict]) -> dict:
    time_blocks = {"morning": Counter(), "afternoon": Counter(), "evening": Counter()}
    for ep in sessions:
        ts = ep.get("started_at", "")
        if not ts:
            continue
        try:
            dt = datetime.fromisoformat(ts)
        except Exception:
            continue
        hour = dt.hour
        block = "morning" if 6 <= hour < 12 else "afternoon" if 12 <= hour < 18 else "evening"
        for tool in ep.get("tools_used", []):
            time_blocks[block][tool] += 1
    result = {}
    for block, counter in time_blocks.items():
        top = [item[0] for item in counter.most_common(3)]
        if top:
            result[block] = top
    return result


def compute_baseline(sessions: list[dict]) -> dict:
    hourly: dict[int, list[float]] = {h: [] for h in range(24)}
    app_hourly: dict[int, Counter] = {h: Counter() for h in range(24)}
    for ep in sessions:
        ts = ep.get("started_at", "")
        if not ts:
            continue
        try:
            dt = datetime.fromisoformat(ts)
        except Exception:
            continue
        h = dt.hour
        for tool in ep.get("tools_used", []):
            app_hourly[h][tool] += 1
    baseline = {}
    for h in range(24):
        app_counts = app_hourly.get(h, Counter())
        most_common = app_counts.most_common(1)
        baseline[f"{h:02d}:00"] = {
            "typical_app": most_common[0][0] if most_common else None,
            "app_count": sum(app_counts.values()),
        }
    return baseline


def run_pattern_scan():
    try:
        sessions = query_patterns(days_back=7)
        if not sessions:
            return
        time_patterns = detect_time_patterns(sessions)
        freq_patterns = detect_frequency_patterns(sessions)
        baseline = compute_baseline(sessions)
        save_patterns({
            "time_patterns": time_patterns,
            "frequency_patterns": freq_patterns,
            "baseline": baseline,
        })
        log.info("pattern_scan_complete", time_patterns=len(time_patterns), freq_patterns=len(freq_patterns))
    except Exception as e:
        log.error("pattern_scan_failed", exc_info=True)
