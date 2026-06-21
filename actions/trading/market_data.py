import sys
import time
import requests
from pathlib import Path

COINGECKO_BASE = "https://api.coingecko.com/api/v3"
FNG_URL = "https://api.alternative.me/fng/"

_price_cache = {"data": None, "ts": 0.0}
CACHE_TTL = 60


def _base_dir() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).parent
    p = Path(__file__).resolve().parent
    while p != p.parent:
        if (p / "main.py").exists() or (p / ".git").exists():
            return p
        p = p.parent
    return Path(__file__).resolve().parent.parent.parent


def get_prices(coins=("bitcoin", "ethereum"), force_refresh=False) -> dict:
    now = time.time()
    if not force_refresh and _price_cache["data"] and now - _price_cache["ts"] < CACHE_TTL:
        return _price_cache["data"]
    params = {
        "ids": ",".join(coins),
        "vs_currencies": "usd",
        "include_24hr_change": "true",
        "include_24hr_vol": "true",
        "include_market_cap": "true",
    }
    resp = requests.get(f"{COINGECKO_BASE}/simple/price", params=params, timeout=10)
    resp.raise_for_status()
    data = resp.json()
    _price_cache["data"] = data
    _price_cache["ts"] = now
    return data


def get_fear_greed() -> dict:
    resp = requests.get(FNG_URL, params={"limit": 1}, timeout=10)
    resp.raise_for_status()
    item = resp.json()["data"][0]
    return {
        "value": int(item["value"]),
        "classification": item["value_classification"],
        "timestamp": item["timestamp"],
    }
