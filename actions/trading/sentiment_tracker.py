import json
from datetime import datetime
from pathlib import Path

from actions.trading.market_data import get_fear_greed, get_prices, _base_dir

HISTORY_PATH = _base_dir() / "memory" / "sentiment_history.json"


def _load_history() -> list[dict]:
    if not HISTORY_PATH.exists():
        return []
    try:
        return json.loads(HISTORY_PATH.read_text(encoding="utf-8") or "[]")
    except Exception:
        return []


def _save_history(history: list[dict]):
    HISTORY_PATH.parent.mkdir(parents=True, exist_ok=True)
    HISTORY_PATH.write_text(
        json.dumps(history[-90:], indent=2), encoding="utf-8"
    )


def sentiment_tracker(parameters: dict, player=None, **kwargs) -> str:
    try:
        fng = get_fear_greed()
        prices = get_prices(("bitcoin",))
    except Exception as e:
        return f"Couldn't fetch sentiment data, sir: {e}"

    history = _load_history()
    today = datetime.now().strftime("%Y-%m-%d")
    if not history or history[-1]["date"] != today:
        history.append({"date": today, "value": fng["value"]})
        _save_history(history)

    trend = ""
    if len(history) >= 2:
        prev = history[-2]["value"]
        diff = fng["value"] - prev
        if abs(diff) >= 3:
            trend = f", {'up' if diff > 0 else 'down'} {abs(diff)} points from yesterday"

    btc_change = prices.get("bitcoin", {}).get("usd_24h_change", 0)
    momentum = "bullish" if btc_change > 1 else "bearish" if btc_change < -1 else "flat"

    return (
        f"Fear and Greed Index is at {fng['value']} — {fng['classification']}{trend}. "
        f"Bitcoin's {momentum} over the last 24 hours, sir."
    )
