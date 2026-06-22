import csv
import json
from collections import defaultdict
from datetime import datetime
from pathlib import Path

import pandas as pd

from actions.trading.market_data import _base_dir, get_prices, get_fear_greed

TRADES_PATH = _base_dir() / "memory" / "trades.json"


def _normalize_tags(raw) -> list[str]:
    if raw is None:
        return []
    if isinstance(raw, list):
        return sorted({t.strip().lower() for t in raw if t.strip()})
    if isinstance(raw, str):
        return sorted({t.strip().lower() for t in raw.split(",") if t.strip()})
    return []


def _capture_market_context() -> dict | None:
    try:
        fng = get_fear_greed()
        prices = get_prices(("bitcoin",))
        btc_change = prices.get("bitcoin", {}).get("usd_24h_change")
        return {
            "fear_greed": fng["value"],
            "fear_greed_label": fng["classification"],
            "btc_24h_change": round(btc_change, 2) if btc_change is not None else None,
        }
    except Exception:
        return None


def _risk_per_unit(trade: dict) -> float | None:
    if trade.get("stop_loss") is None:
        return None
    risk = abs(trade["entry_price"] - trade["stop_loss"])
    return risk if risk > 0 else None


def _recompute_realized(trade: dict):
    direction = 1 if trade["side"] == "long" else -1
    total_size = trade["size"]
    risk_per_unit = _risk_per_unit(trade)
    pnl_total = 0.0
    r_weighted_sum = 0.0
    r_weight_total = 0.0
    entry_fee = trade.get("entry_fee", 0.0)
    for ex in trade.get("exits", []):
        exit_size = ex["size"]
        pnl_per_unit = (ex["price"] - trade["entry_price"]) * direction
        prorated_entry_fee = entry_fee * (exit_size / total_size) if total_size else 0.0
        pnl_total += pnl_per_unit * exit_size - ex.get("fee", 0.0) - prorated_entry_fee
        if risk_per_unit:
            r_weighted_sum += (pnl_per_unit / risk_per_unit) * exit_size
            r_weight_total += exit_size
    trade["realized_pnl_usd"] = round(pnl_total, 2)
    trade["realized_r"] = (
        round(r_weighted_sum / r_weight_total, 2) if r_weight_total else None
    )


def _holding_hours(trade: dict) -> float | None:
    if not trade.get("opened_at"):
        return None
    start = datetime.fromisoformat(trade["opened_at"])
    end = (
        datetime.fromisoformat(trade["closed_at"])
        if trade.get("closed_at")
        else datetime.now()
    )
    return round((end - start).total_seconds() / 3600, 1)


def _classify_exit(trade: dict, exit_price: float) -> str:
    direction = 1 if trade["side"] == "long" else -1
    sl, tp = trade.get("stop_loss"), trade.get("take_profit")
    if sl is not None and (
        (direction == 1 and exit_price <= sl)
        or (direction == -1 and exit_price >= sl)
    ):
        return "stopped_out"
    if tp is not None and (
        (direction == 1 and exit_price >= tp)
        or (direction == -1 and exit_price <= tp)
    ):
        return "hit_target"
    return "manual"


def _migrate_legacy(it: dict) -> dict:
    if "remaining_size" in it:
        return it
    size = it.get("size", 0) or 0
    exits = []
    if it.get("status") == "closed" and it.get("exit_price") is not None:
        exits = [
            {
                "price": it["exit_price"],
                "size": size,
                "fee": 0.0,
                "timestamp": it.get("closed_at") or it.get("opened_at"),
                "exit_type": "manual",
            }
        ]
    migrated = {
        "id": it.get("id"),
        "symbol": it.get("symbol"),
        "side": it.get("side"),
        "setup": "unspecified",
        "entry_price": it.get("entry_price"),
        "stop_loss": None,
        "take_profit": None,
        "size": size,
        "remaining_size": 0.0 if it.get("status") == "closed" else size,
        "entry_fee": 0.0,
        "reasoning": it.get("reasoning", ""),
        "tags": [],
        "notes": "",
        "status": it.get("status", "open"),
        "opened_at": it.get("opened_at")
        or datetime.now().isoformat(timespec="seconds"),
        "closed_at": it.get("closed_at"),
        "exits": exits,
        "market_context": None,
        "realized_pnl_usd": 0.0,
        "realized_r": None,
    }
    if exits:
        _recompute_realized(migrated)
    return migrated


def _profit_factor(closed: list[dict]) -> float | None:
    gross_profit = sum(it["realized_pnl_usd"] for it in closed if it["realized_pnl_usd"] > 0)
    gross_loss = abs(sum(it["realized_pnl_usd"] for it in closed if it["realized_pnl_usd"] < 0))
    if gross_loss == 0:
        return None
    return round(gross_profit / gross_loss, 2)


def _expectancy(closed: list[dict]) -> float | None:
    r_vals = [it["realized_r"] for it in closed if it["realized_r"] is not None]
    if len(r_vals) < 2:
        return None
    wins_r = [r for r in r_vals if r > 0]
    losses_r = [r for r in r_vals if r <= 0]
    if not wins_r or not losses_r:
        return None
    win_rate = len(wins_r) / len(r_vals)
    loss_rate = 1 - win_rate
    avg_win_r = sum(wins_r) / len(wins_r)
    avg_loss_r = abs(sum(losses_r) / len(losses_r))
    return round(win_rate * avg_win_r - loss_rate * avg_loss_r, 3)


def _consecutive_streaks(closed: list[dict]) -> dict:
    sorted_c = sorted(
        [it for it in closed if it.get("closed_at")],
        key=lambda x: x["closed_at"]
    )
    if not sorted_c:
        return {"current_streak": 0, "current_streak_type": None,
                "max_win_streak": 0, "max_loss_streak": 0}
    max_win = max_loss = cur_win = cur_loss = 0
    for it in sorted_c:
        if it["realized_pnl_usd"] > 0:
            cur_win += 1
            cur_loss = 0
        else:
            cur_loss += 1
            cur_win = 0
        max_win = max(max_win, cur_win)
        max_loss = max(max_loss, cur_loss)
    last_type = "win" if sorted_c[-1]["realized_pnl_usd"] > 0 else "loss"
    current = 0
    for it in reversed(sorted_c):
        is_win = it["realized_pnl_usd"] > 0
        if (is_win and last_type == "win") or (not is_win and last_type == "loss"):
            current += 1
        else:
            break
    return {"current_streak": current, "current_streak_type": last_type,
            "max_win_streak": max_win, "max_loss_streak": max_loss}


def _load() -> list[dict]:
    if not TRADES_PATH.exists():
        return []
    try:
        raw = TRADES_PATH.read_text(encoding="utf-8")
        data = json.loads(raw) if raw.strip() else []
        if not isinstance(data, list):
            return []
        migrated = [_migrate_legacy(it) for it in data]
        if migrated != data:
            _save(migrated)
        backfill = False
        for item in migrated:
            if item.setdefault("tags", []) is not item.get("tags") or item.setdefault("notes", "") is not item.get("notes"):
                backfill = True
            item.setdefault("tags", [])
            item.setdefault("notes", "")
        if backfill:
            _save(migrated)
        return migrated
    except Exception:
        return []


def _save(items: list[dict]):
    TRADES_PATH.parent.mkdir(parents=True, exist_ok=True)
    TRADES_PATH.write_text(
        json.dumps(items, indent=2, ensure_ascii=False), encoding="utf-8"
    )


def _parse_import_row(row: dict, row_num: int) -> tuple[dict | None, str | None]:
    try:
        symbol = str(row.get("symbol", "")).strip().upper()
        side = str(row.get("side", "")).strip().lower()
        entry_price = row.get("entry_price")
        size = row.get("size")
        if not symbol or side not in ("long", "short") or pd.isna(entry_price) or pd.isna(size):
            return None, f"Row {row_num}: missing symbol/side/entry_price/size"
        entry_price, size = float(entry_price), float(size)
        if entry_price <= 0 or size <= 0:
            return None, f"Row {row_num}: entry_price and size must be positive"

        stop_loss = row.get("stop_loss")
        stop_loss = float(stop_loss) if not pd.isna(stop_loss) else None
        if stop_loss is not None:
            if side == "long" and stop_loss >= entry_price:
                return None, f"Row {row_num}: stop_loss must be below entry_price for a long"
            if side == "short" and stop_loss <= entry_price:
                return None, f"Row {row_num}: stop_loss must be above entry_price for a short"

        take_profit = row.get("take_profit")
        take_profit = float(take_profit) if not pd.isna(take_profit) else None

        def _norm_date(val, label):
            if pd.isna(val):
                return datetime.now().isoformat(timespec="seconds"), None
            try:
                return datetime.fromisoformat(str(val)).isoformat(timespec="seconds"), None
            except ValueError:
                return None, f"Row {row_num}: {label} '{val}' isn't a valid date — use YYYY-MM-DD"

        opened_at, err = _norm_date(row.get("opened_at"), "opened_at")
        if err:
            return None, err

        trade = {
            "id": None,
            "symbol": symbol,
            "side": side,
            "setup": str(row.get("setup", "unspecified") or "unspecified").strip().lower(),
            "entry_price": entry_price,
            "stop_loss": stop_loss,
            "take_profit": take_profit,
            "size": size,
            "remaining_size": size,
            "entry_fee": float(row.get("fee", 0) or 0),
            "reasoning": str(row.get("reasoning", "") or ""),
            "status": "open",
            "opened_at": opened_at,
            "closed_at": None,
            "exits": [],
            "market_context": None,
            "realized_pnl_usd": 0.0,
            "realized_r": None,
        }

        exit_price = row.get("exit_price")
        if not pd.isna(exit_price):
            exit_price = float(exit_price)
            if exit_price <= 0:
                return None, f"Row {row_num}: exit_price must be positive"
            closed_at, err = _norm_date(row.get("closed_at"), "closed_at")
            if err:
                return None, err
            exit_type = _classify_exit(trade, exit_price)
            trade["exits"].append(
                {
                    "price": exit_price,
                    "size": size,
                    "fee": float(row.get("exit_fee", 0) or 0),
                    "timestamp": closed_at,
                    "exit_type": exit_type,
                }
            )
            trade["remaining_size"] = 0.0
            trade["status"] = "closed"
            trade["closed_at"] = closed_at
            _recompute_realized(trade)

        return trade, None
    except (ValueError, TypeError) as e:
        return None, f"Row {row_num}: couldn't parse — {e}"


def import_trades(file_path: str) -> dict:
    path = Path(file_path)
    if not path.exists():
        return {"imported": 0, "skipped": 0, "errors": [f"File not found: {file_path}"]}
    try:
        df = (
            pd.read_excel(path)
            if path.suffix.lower() in (".xlsx", ".xls")
            else pd.read_csv(path)
        )
    except Exception as e:
        return {"imported": 0, "skipped": 0, "errors": [f"Couldn't read file: {e}"]}

    df.columns = [str(c).strip().lower() for c in df.columns]
    required = {"symbol", "side", "entry_price", "size"}
    missing = required - set(df.columns)
    if missing:
        return {
            "imported": 0,
            "skipped": 0,
            "errors": [
                f"Missing required column(s): {', '.join(sorted(missing))}"
            ],
        }

    items = _load()
    imported, errors = [], []
    for i, row in df.iterrows():
        trade, error = _parse_import_row(row.to_dict(), i + 2)
        if error:
            errors.append(error)
            continue
        trade["id"] = (
            f"t{len(items) + len(imported) + 1}_"
            f"{int(datetime.now().timestamp())}_{i}"
        )
        imported.append(trade)

    items.extend(imported)
    _save(items)
    return {"imported": len(imported), "skipped": len(errors), "errors": errors[:10]}


def trade_journal(parameters: dict, player=None, **kwargs) -> str:
    action = parameters.get("action", "list")
    items = _load()

    try:
        if action == "log":
            symbol = parameters.get("symbol", "").strip().upper()
            side = parameters.get("side", "").strip().lower()
            entry_price = parameters.get("entry_price")
            size = parameters.get("size")
            if (
                not symbol
                or side not in ("long", "short")
                or entry_price is None
                or size is None
            ):
                return "I need symbol, side (long/short), entry price, and size, sir."
            entry_price, size = float(entry_price), float(size)
            if entry_price <= 0 or size <= 0:
                return "Entry price and size must be positive numbers, sir."
            stop_loss = parameters.get("stop_loss")
            stop_loss = float(stop_loss) if stop_loss is not None else None
            if stop_loss is not None:
                if side == "long" and stop_loss >= entry_price:
                    return "For a long, the stop loss needs to be below your entry price, sir."
                if side == "short" and stop_loss <= entry_price:
                    return "For a short, the stop loss needs to be above your entry price, sir."
            take_profit = parameters.get("take_profit")
            entry = {
                "id": f"t{len(items) + 1}_{int(datetime.now().timestamp())}",
                "symbol": symbol,
                "side": side,
                "setup": (parameters.get("setup") or "unspecified").strip().lower(),
                "entry_price": entry_price,
                "stop_loss": stop_loss,
                "take_profit": float(take_profit) if take_profit is not None else None,
                "size": size,
                "remaining_size": size,
                "entry_fee": float(parameters.get("fee", 0) or 0),
                "reasoning": parameters.get("reasoning", ""),
                "tags": _normalize_tags(parameters.get("tags")),
                "notes": str(parameters.get("notes", "") or ""),
                "status": "open",
                "opened_at": datetime.now().isoformat(timespec="seconds"),
                "closed_at": None,
                "exits": [],
                "market_context": _capture_market_context(),
                "realized_pnl_usd": 0.0,
                "realized_r": None,
            }
            items.append(entry)
            _save(items)
            risk_note = (
                f" Risking ${abs(entry_price - stop_loss) * size:,.2f} to the stop."
                if stop_loss
                else ""
            )
            return f"Logged: {side} {symbol} at {entry_price}, size {size}.{risk_note} Sir."

        if action == "close":
            symbol_q = parameters.get("symbol", "").strip().upper()
            if not symbol_q:
                return "Which symbol are you closing, sir?"
            open_matches = [
                it
                for it in items
                if it["symbol"] == symbol_q and it["status"] == "open"
            ]
            if not open_matches:
                return f"No open {symbol_q} trade found, sir."
            trade = open_matches[-1]
            exit_price = parameters.get("exit_price")
            if exit_price is None:
                coin_id = {"BTC": "bitcoin", "ETH": "ethereum"}.get(symbol_q)
                if not coin_id:
                    return f"No live price source for {symbol_q} — please give me an exit price, sir."
                try:
                    exit_price = get_prices((coin_id,))[coin_id]["usd"]
                except Exception:
                    return "Couldn't fetch a live price, sir — please give me an exit price."
            exit_price = float(exit_price)
            if exit_price <= 0:
                return "Exit price must be a positive number, sir."
            close_size = parameters.get("size")
            close_size = (
                float(close_size)
                if close_size is not None
                else trade["remaining_size"]
            )
            if close_size <= 0:
                return "Close size must be a positive number, sir."
            close_size = min(close_size, trade["remaining_size"])
            exit_type = _classify_exit(trade, exit_price)
            trade["exits"].append(
                {
                    "price": exit_price,
                    "size": close_size,
                    "fee": float(parameters.get("fee", 0) or 0),
                    "timestamp": datetime.now().isoformat(timespec="seconds"),
                    "exit_type": exit_type,
                }
            )
            trade["remaining_size"] = round(trade["remaining_size"] - close_size, 8)
            _recompute_realized(trade)
            is_full = trade["remaining_size"] <= 1e-8
            if is_full:
                trade["status"] = "closed"
                trade["closed_at"] = datetime.now().isoformat(timespec="seconds")
                if parameters.get("notes"):
                    trade["notes"] = str(parameters["notes"])
            _save(items)
            r_note = (
                f", {trade['realized_r']}R"
                if trade["realized_r"] is not None
                else ""
            )
            scope = (
                "Fully closed"
                if is_full
                else f"Partially closed ({close_size} units of)"
            )
            type_note = {
                "stopped_out": " — stopped out",
                "hit_target": " — hit target",
            }.get(exit_type, "")
            return (
                f"{scope} {symbol_q} at {exit_price}{type_note}{r_note}. "
                f"Realized P&L: ${trade['realized_pnl_usd']:,.2f}, sir."
            )

        if action == "list":
            status_filter = parameters.get("status")
            setup_filter = (
                (parameters.get("setup") or "").strip().lower() or None
            )
            filtered = [
                it
                for it in items
                if (not status_filter or it["status"] == status_filter)
                and (not setup_filter or it.get("setup") == setup_filter)
            ]
            if not filtered:
                return "No matching trades, sir."
            lines = []
            for it in filtered[-5:]:
                if it["status"] == "open":
                    lines.append(
                        f"{it['side']} {it['symbol']} @ {it['entry_price']} "
                        f"(open, {it['remaining_size']} remaining)"
                    )
                else:
                    r = (
                        f" ({it['realized_r']}R)"
                        if it["realized_r"] is not None
                        else ""
                    )
                    lines.append(
                        f"{it['side']} {it['symbol']} @ {it['entry_price']} "
                        f"-> ${it['realized_pnl_usd']:,.2f}{r}"
                    )
            return "Recent trades: " + "; ".join(lines)

        if action == "stats":
            closed = [
                it
                for it in items
                if it["status"] == "closed" and it.get("closed_at")
            ]
            if not closed:
                return "No closed trades yet, sir."
            wins = [it for it in closed if it["realized_pnl_usd"] > 0]
            win_rate = round(len(wins) / len(closed) * 100, 1)
            total_pnl = round(sum(it["realized_pnl_usd"] for it in closed), 2)
            r_values = [
                it["realized_r"]
                for it in closed
                if it["realized_r"] is not None
            ]
            avg_r = round(sum(r_values) / len(r_values), 2) if r_values else None
            sorted_closed = sorted(
                closed, key=lambda x: (x.get("closed_at") or "")
            )
            equity = peak = max_dd = 0.0
            for it in sorted_closed:
                equity += it["realized_pnl_usd"]
                peak = max(peak, equity)
                max_dd = max(max_dd, peak - equity)
            avg_r_note = (
                f", average {avg_r}R per trade" if avg_r is not None else ""
            )
            pf = _profit_factor(closed)
            exp_val = _expectancy(closed)
            streaks = _consecutive_streaks(closed)
            pf_note = f" Profit factor: {'∞' if pf is None else pf}." if closed else ""
            exp_note = f" Expectancy: {exp_val}R." if exp_val is not None else ""
            streak_type = streaks.get("current_streak_type")
            streak_note = (
                f" Currently on a {streaks['current_streak']}-trade {streak_type} streak."
                if streak_type else ""
            )
            summary = (
                f"{len(closed)} closed trades, {win_rate}% win rate{avg_r_note}."
                f"{pf_note}{exp_note} "
                f"Total realized P&L: ${total_pnl:,.2f}. "
                f"Max drawdown: ${max_dd:,.2f}.{streak_note}"
            )
            setup_groups = defaultdict(list)
            for it in closed:
                setup_groups[it.get("setup") or "unspecified"].append(it)
            breakdown_lines = []
            for setup, trades in sorted(setup_groups.items(), key=lambda x: -len(x[1])):
                if setup == "unspecified":
                    continue
                wins_s = [t for t in trades if t["realized_pnl_usd"] > 0]
                r_vals = [t["realized_r"] for t in trades if t["realized_r"] is not None]
                wr = round(len(wins_s) / len(trades) * 100, 1)
                avg_r_s = round(sum(r_vals) / len(r_vals), 2) if r_vals else None
                r_note = f", {avg_r_s}R avg" if avg_r_s is not None else ""
                breakdown_lines.append(f"{setup}: {len(trades)} trades, {wr}% win rate{r_note}")
            if breakdown_lines:
                return summary + " Breakdown by strategy: " + "; ".join(breakdown_lines) + "."
            return summary

        if action == "position_size":
            acc, risk_pct, ep, sl = (
                parameters.get(k)
                for k in ("account_size", "risk_pct", "entry_price", "stop_loss")
            )
            if acc is None or ep is None or sl is None:
                return "I need account size, entry price, and stop loss, sir."
            acc, ep, sl = float(acc), float(ep), float(sl)
            risk_pct = float(risk_pct) if risk_pct is not None else 1.0
            if risk_pct <= 0 or risk_pct > 100:
                return "Risk percent should be between 0 and 100, sir."
            risk_amount = acc * (risk_pct / 100)
            per_unit_risk = abs(ep - sl)
            if per_unit_risk == 0:
                return "Entry and stop loss can't be the same price, sir."
            size = risk_amount / per_unit_risk
            return (
                f"Risking ${risk_amount:,.2f} ({risk_pct}% of account), "
                f"size out to {size:.4f} units (${size * ep:,.2f} notional), sir."
            )

        if action == "exposure":
            open_trades = [it for it in items if it["status"] == "open"]
            if not open_trades:
                return "No open positions right now, sir."
            total_risk = sum(
                (_risk_per_unit(it) or 0) * it["remaining_size"]
                for it in open_trades
            )
            total_notional = sum(
                it["entry_price"] * it["remaining_size"] for it in open_trades
            )
            unsized = sum(1 for it in open_trades if _risk_per_unit(it) is None)
            note = (
                f" ({unsized} position(s) have no stop loss, risk understated)"
                if unsized
                else ""
            )
            return (
                f"{len(open_trades)} open position(s), "
                f"${total_notional:,.2f} notional, "
                f"${total_risk:,.2f} at risk to stops{note}, sir."
            )

        if action == "edit":
            trade_id = parameters.get("id", "").strip()
            symbol_q = parameters.get("symbol", "").strip().upper()
            if not trade_id and not symbol_q:
                return "Tell me the trade ID or symbol to edit, sir."
            match = None
            if trade_id:
                match = next((it for it in items if it["id"] == trade_id), None)
            else:
                open_matches = [it for it in items if it["symbol"] == symbol_q
                                and it["status"] == "open"]
                match = open_matches[-1] if open_matches else None
            if not match:
                return "Couldn't find that trade, sir."

            blocked = [k for k in ("entry_price", "size", "side")
                       if parameters.get(k) is not None]
            if blocked and match["exits"]:
                return (f"Can't edit {', '.join(blocked)} on a trade that already "
                        f"has exits — it would corrupt the P&L history, sir.")

            changed = []
            if parameters.get("stop_loss") is not None:
                if match["status"] == "closed":
                    return "Can't edit stop loss on a closed trade — it would change historical R, sir."
                sl = float(parameters["stop_loss"])
                if match["side"] == "long" and sl >= match["entry_price"]:
                    return "Stop loss must be below entry price for a long, sir."
                if match["side"] == "short" and sl <= match["entry_price"]:
                    return "Stop loss must be above entry price for a short, sir."
                match["stop_loss"] = sl
                changed.append("stop loss")
            if parameters.get("take_profit") is not None:
                match["take_profit"] = float(parameters["take_profit"])
                changed.append("take profit")
            if parameters.get("setup") is not None:
                match["setup"] = str(parameters["setup"]).strip().lower()
                changed.append("setup")
            if parameters.get("reasoning") is not None:
                match["reasoning"] = str(parameters["reasoning"])
                changed.append("reasoning")
            if parameters.get("tags") is not None:
                match["tags"] = _normalize_tags(parameters["tags"])
                changed.append("tags")
            if parameters.get("notes") is not None:
                match["notes"] = str(parameters["notes"])
                changed.append("notes")
            if not changed:
                return "Nothing to update — tell me what to change, sir."
            _save(items)
            return f"Updated {', '.join(changed)} on {match['symbol']} trade, sir."

        if action == "export":
            export_path = _base_dir() / "memory" / "trades_export.csv"
            fields = [
                "id", "symbol", "side", "setup", "entry_price", "stop_loss",
                "take_profit", "size", "remaining_size", "status", "opened_at",
                "closed_at", "holding_hours", "realized_pnl_usd", "realized_r",
                "fear_greed_at_entry", "btc_24h_change_at_entry",
            ]
            with open(export_path, "w", newline="", encoding="utf-8") as f:
                w = csv.DictWriter(f, fieldnames=fields)
                w.writeheader()
                for it in items:
                    ctx = it.get("market_context") or {}
                    w.writerow(
                        {
                            "id": it["id"],
                            "symbol": it["symbol"],
                            "side": it["side"],
                            "setup": it.get("setup"),
                            "entry_price": it["entry_price"],
                            "stop_loss": it.get("stop_loss"),
                            "take_profit": it.get("take_profit"),
                            "size": it["size"],
                            "remaining_size": it["remaining_size"],
                            "status": it["status"],
                            "opened_at": it["opened_at"],
                            "closed_at": it.get("closed_at"),
                            "holding_hours": _holding_hours(it),
                            "realized_pnl_usd": it.get("realized_pnl_usd"),
                            "realized_r": it.get("realized_r"),
                            "fear_greed_at_entry": ctx.get("fear_greed"),
                            "btc_24h_change_at_entry": ctx.get("btc_24h_change"),
                        }
                    )
            return f"Exported {len(items)} trades to {export_path}, sir."

        if action == "import":
            file_path = parameters.get("file_path")
            if not file_path:
                return "I need a file path to import from, sir."
            result = import_trades(file_path)
            msg = f"Imported {result['imported']} trade(s)"
            if result["skipped"]:
                msg += f", skipped {result['skipped']}: {'; '.join(result['errors'][:3])}"
                if result["skipped"] > 3:
                    msg += f" (+{result['skipped'] - 3} more)"
            return msg + ", sir."

        return "Unknown trade_journal action."

    except (ValueError, TypeError) as e:
        return (
            f"I couldn't process that, sir — check the numbers you gave me. ({e})"
        )


def get_weekly_recap() -> str | None:
    try:
        items = _load()
        cutoff = datetime.now().timestamp() - 7 * 86400
        closed_this_week = [
            it
            for it in items
            if it["status"] == "closed"
            and it.get("closed_at")
            and datetime.fromisoformat(it["closed_at"]).timestamp() >= cutoff
        ]
        if not closed_this_week:
            return None
        wins = [it for it in closed_this_week if it["realized_pnl_usd"] > 0]
        total_pnl = round(
            sum(it["realized_pnl_usd"] for it in closed_this_week), 2
        )
        win_rate = round(len(wins) / len(closed_this_week) * 100, 1)
        return f"This week: {len(closed_this_week)} trades closed, {win_rate}% win rate, ${total_pnl:,.2f} P&L."
    except Exception:
        return None


def _build_setup_breakdown(closed_trades: list[dict]) -> list[dict]:
    groups = defaultdict(list)
    for it in closed_trades:
        groups[it.get("setup") or "unspecified"].append(it)
    result = []
    for setup, trades in sorted(groups.items(), key=lambda x: -len(x[1])):
        wins = [t for t in trades if t["realized_pnl_usd"] > 0]
        r_vals = [t["realized_r"] for t in trades if t["realized_r"] is not None]
        result.append({
            "setup": setup,
            "trades": len(trades),
            "win_rate": round(len(wins) / len(trades) * 100, 1),
            "avg_r": round(sum(r_vals) / len(r_vals), 2) if r_vals else None,
            "total_pnl": round(sum(t["realized_pnl_usd"] for t in trades), 2),
        })
    return result


def get_dashboard_summary() -> dict:
    try:
        items = _load()
        open_trades = [it for it in items if it["status"] == "open"]
        closed_trades = sorted(
            [
                it
                for it in items
                if it["status"] == "closed" and it.get("closed_at")
            ],
            key=lambda x: (x.get("closed_at") or ""),
        )
        try:
            live_prices = get_prices(("bitcoin", "ethereum"))
        except Exception:
            live_prices = {}
        symbol_to_coin = {"BTC": "bitcoin", "ETH": "ethereum"}
        open_positions = []
        for it in open_trades:
            coin_id = symbol_to_coin.get(it["symbol"])
            current = live_prices.get(coin_id, {}).get("usd") if coin_id else None
            direction = 1 if it["side"] == "long" else -1
            unrealized = (
                round(
                    (current - it["entry_price"]) * direction * it["remaining_size"],
                    2,
                )
                if current
                else None
            )
            open_positions.append(
                {
                    **it,
                    "current_price": current,
                    "unrealized_pnl_usd": unrealized,
                    "holding_hours": _holding_hours(it),
                }
            )
        equity, peak = 0.0, 0.0
        max_dd, running_dd = 0.0, 0.0
        equity_curve, drawdown_curve, rolling_winrate = [], [], []
        window = 20
        for i, it in enumerate(closed_trades):
            equity += it["realized_pnl_usd"]
            peak = max(peak, equity)
            dd = peak - equity
            max_dd = max(max_dd, dd)
            date = it["closed_at"]
            equity_curve.append({"date": date, "cumulative_pnl": round(equity, 2)})
            drawdown_curve.append({"date": date, "drawdown": round(dd, 2)})
            window_trades = closed_trades[max(0, i - window + 1): i + 1]
            w_wins = sum(1 for t in window_trades if t["realized_pnl_usd"] > 0)
            rolling_winrate.append({
                "date": date,
                "win_rate": round(w_wins / len(window_trades) * 100, 1),
                "window": len(window_trades),
            })
        wins = [it for it in closed_trades if it["realized_pnl_usd"] > 0]
        r_values = [
            it["realized_r"]
            for it in closed_trades
            if it["realized_r"] is not None
        ]
        monthly_buckets = defaultdict(float)
        for it in closed_trades:
            if not it.get("closed_at"):
                continue
            month = it["closed_at"][:7]
            monthly_buckets[month] += it["realized_pnl_usd"]
        monthly_pnl = [{"month": m, "pnl": round(v, 2)}
                        for m, v in sorted(monthly_buckets.items())]
        recent_closed = [
            {**it, "holding_hours": _holding_hours(it)}
            for it in closed_trades[-20:][::-1]
        ]
        return {
            "open_positions": open_positions,
            "recent_closed": recent_closed,
            "equity_curve": equity_curve,
            "drawdown_curve": drawdown_curve,
            "rolling_winrate": rolling_winrate,
            "monthly_pnl": monthly_pnl,
            "stats": {
                "total_trades": len(closed_trades),
                "win_rate": (
                    round(len(wins) / len(closed_trades) * 100, 1)
                    if closed_trades
                    else None
                ),
                "avg_r": (
                    round(sum(r_values) / len(r_values), 2) if r_values else None
                ),
                "total_pnl": round(
                    sum(it["realized_pnl_usd"] for it in closed_trades), 2
                ),
                "max_drawdown": round(max_dd, 2),
                "profit_factor": _profit_factor(closed_trades),
                "expectancy": _expectancy(closed_trades),
                "streaks": _consecutive_streaks(closed_trades),
            },
            "setup_breakdown": _build_setup_breakdown(closed_trades),
            "exposure": {
                "open_count": len(open_trades),
                "total_notional": round(
                    sum(
                        it["entry_price"] * it["remaining_size"]
                        for it in open_trades
                    ),
                    2,
                ),
                "total_risk": round(
                    sum(
                        (_risk_per_unit(it) or 0) * it["remaining_size"]
                        for it in open_trades
                    ),
                    2,
                ),
            },
        }
    except Exception as e:
        return {
            "error": str(e),
            "open_positions": [],
            "recent_closed": [],
            "equity_curve": [],
            "drawdown_curve": [],
            "rolling_winrate": [],
            "monthly_pnl": [],
            "stats": {},
            "setup_breakdown": [],
            "exposure": {},
        }
