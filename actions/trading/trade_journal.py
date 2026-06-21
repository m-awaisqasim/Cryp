import json
from datetime import datetime
from pathlib import Path

from actions.trading.market_data import _base_dir

TRADES_PATH = _base_dir() / "memory" / "trades.json"


def _load() -> list[dict]:
    if not TRADES_PATH.exists():
        return []
    try:
        raw = TRADES_PATH.read_text(encoding="utf-8")
        data = json.loads(raw) if raw.strip() else []
        return data if isinstance(data, list) else []
    except Exception:
        return []


def _save(items: list[dict]):
    TRADES_PATH.parent.mkdir(parents=True, exist_ok=True)
    TRADES_PATH.write_text(
        json.dumps(items, indent=2, ensure_ascii=False), encoding="utf-8"
    )


def trade_journal(parameters: dict, player=None, **kwargs) -> str:
    action = parameters.get("action", "list")
    items = _load()

    if action == "log":
        symbol = parameters.get("symbol", "").strip().upper()
        side = parameters.get("side", "").strip().lower()
        entry_price = parameters.get("entry_price")
        size = parameters.get("size")
        reasoning = parameters.get("reasoning", "")
        if not symbol or not side or entry_price is None:
            return "I need at least a symbol, side (long/short), and entry price, sir."
        entry = {
            "id": f"t{len(items) + 1}_{int(datetime.now().timestamp())}",
            "symbol": symbol,
            "side": side,
            "entry_price": float(entry_price),
            "exit_price": None,
            "size": float(size) if size is not None else None,
            "reasoning": reasoning,
            "status": "open",
            "opened_at": datetime.now().isoformat(timespec="seconds"),
            "closed_at": None,
            "pnl_pct": None,
        }
        items.append(entry)
        _save(items)
        return f"Logged: {side} {symbol} at {entry_price}, sir."

    if action == "close":
        symbol_q = parameters.get("symbol", "").strip().upper()
        exit_price = parameters.get("exit_price")
        if not symbol_q or exit_price is None:
            return "I need the symbol and exit price to close a trade, sir."
        open_matches = [
            it
            for it in items
            if it["symbol"] == symbol_q and it["status"] == "open"
        ]
        if not open_matches:
            return f"No open {symbol_q} trade found, sir."
        trade = open_matches[-1]
        exit_price = float(exit_price)
        direction = 1 if trade["side"] == "long" else -1
        trade["exit_price"] = exit_price
        trade["status"] = "closed"
        trade["closed_at"] = datetime.now().isoformat(timespec="seconds")
        trade["pnl_pct"] = round(
            direction
            * (exit_price - trade["entry_price"])
            / trade["entry_price"]
            * 100,
            2,
        )
        _save(items)
        result = "profit" if trade["pnl_pct"] >= 0 else "loss"
        return f"Closed {symbol_q} at {exit_price}: {trade['pnl_pct']}% {result}, sir."

    if action == "list":
        status_filter = parameters.get("status")
        filtered = [
            it for it in items if not status_filter or it["status"] == status_filter
        ]
        if not filtered:
            return "No trades logged yet, sir."
        lines = [
            f"{it['side']} {it['symbol']} @ {it['entry_price']}"
            + (
                f" -> {it['pnl_pct']}%"
                if it["pnl_pct"] is not None
                else " (open)"
            )
            for it in filtered[-5:]
        ]
        return "Recent trades: " + "; ".join(lines)

    if action == "stats":
        closed = [it for it in items if it["status"] == "closed"]
        if not closed:
            return "No closed trades yet to compute stats, sir."
        wins = [it for it in closed if it["pnl_pct"] > 0]
        win_rate = round(len(wins) / len(closed) * 100, 1)
        avg_pnl = round(
            sum(it["pnl_pct"] for it in closed) / len(closed), 2
        )
        return (
            f"{len(closed)} closed trades, {win_rate}% win rate, "
            f"average {avg_pnl}% per trade, sir."
        )

    return "Unknown trade_journal action."
