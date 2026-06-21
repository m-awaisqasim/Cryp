from actions.trading.market_data import get_prices

_baseline = {"bitcoin": None, "ethereum": None, "ts": 0}
CHECK_INTERVAL = 300
MOVE_THRESHOLD_PCT = 3.0
CRITICAL_THRESHOLD_PCT = 6.0


def check_price_anomaly() -> str | None:
    try:
        data = get_prices(("bitcoin", "ethereum"), force_refresh=True)
    except Exception:
        return None
    alerts = []
    for coin, label in [("bitcoin", "Bitcoin"), ("ethereum", "Ethereum")]:
        current = data.get(coin, {}).get("usd")
        if current is None:
            continue
        prev = _baseline.get(coin)
        _baseline[coin] = current
        if prev is None:
            continue
        pct_move = (current - prev) / prev * 100
        if abs(pct_move) >= MOVE_THRESHOLD_PCT:
            direction = "spiked" if pct_move > 0 else "dropped"
            critical = abs(pct_move) >= CRITICAL_THRESHOLD_PCT
            alerts.append(
                (f"{label} just {direction} {abs(pct_move):.1f}% — now ${current:,.0f}, sir.", critical)
            )
    if not alerts:
        return None
    msg, is_critical = max(alerts, key=lambda x: x[1])
    return msg if not is_critical else f"[CRITICAL] {msg}"


def is_critical_alert(msg: str | None) -> bool:
    if msg is None:
        return False
    return msg.startswith("[CRITICAL] ")
