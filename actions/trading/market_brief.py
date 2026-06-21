from actions.trading.market_data import get_prices


def market_brief(parameters: dict, player=None, **kwargs) -> str:
    try:
        data = get_prices(("bitcoin", "ethereum"))
    except Exception as e:
        return f"Couldn't fetch market data, sir: {e}"
    parts = []
    for coin, label in [("bitcoin", "Bitcoin"), ("ethereum", "Ethereum")]:
        d = data.get(coin)
        if not d:
            continue
        price = d.get("usd", 0)
        change = d.get("usd_24h_change", 0)
        direction = "up" if change >= 0 else "down"
        parts.append(
            f"{label} is at ${price:,.0f}, {direction} {abs(change):.1f}% in 24 hours"
        )
    if not parts:
        return "Couldn't get market data right now, sir."
    return ". ".join(parts) + ", sir."
