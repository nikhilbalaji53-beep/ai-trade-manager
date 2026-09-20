from typing import Dict, Any


def position_pnl(side: str, quantity: float, entry_price: float, current_price: float) -> float:
    direction = 1.0 if side == "BUY" else -1.0
    return round((current_price - entry_price) * quantity * direction, 2)


def position_summary(position: Any) -> Dict[str, Any]:
    if isinstance(position, dict):
        sym = position["symbol"]
        side = position["side"]
        qty = position["quantity"]
        entry = position["entry_price"]
        curr = position.get("current_price", entry)
        sl = position.get("stop_loss", 0.0)
        ts = position.get("trailing_stop", sl)
        tp = position.get("take_profit", 0.0)
        tp2 = position.get("take_profit_2", None)
        be = position.get("break_even_activated", False)
        opened_at = position.get("opened_at", "")
    else:
        sym = position.symbol
        side = position.side
        qty = position.quantity
        entry = position.entry_price
        curr = position.current_price
        sl = position.stop_loss
        ts = position.trailing_stop
        tp = position.take_profit
        tp2 = getattr(position, "take_profit_2", None)
        be = getattr(position, "break_even_activated", False)
        opened_at = getattr(position, "opened_at", "")

    pnl = position_pnl(side, qty, entry, curr)
    cost = entry * qty
    pnl_pct = round((pnl / cost) * 100.0, 2) if cost else 0.0

    stop_dist = abs(curr - sl) / curr if curr > 0 else 0.1
    risk_level = "High" if stop_dist < 0.02 else "Moderate" if stop_dist < 0.05 else "Low"
    branch = "PROFIT_MANAGER" if pnl >= 0 else "LOSS_MANAGER"
    manager_decision = "HOLD" if pnl >= 0 else ("RECOVER_WATCH" if abs(pnl_pct) < 1.5 else "HOLD")

    return {
        "symbol": sym,
        "side": side,
        "quantity": qty,
        "entry_price": entry,
        "current_price": curr,
        "market_value": round(curr * qty, 2),
        "unrealized_pnl": pnl,
        "pnl_percent": pnl_pct,
        "stop_loss": sl,
        "trailing_stop": ts,
        "take_profit": tp,
        "take_profit_2": tp2,
        "risk_level": risk_level,
        "break_even_activated": be,
        "branch": branch,
        "manager_decision": manager_decision,
        "opened_at": opened_at,
    }
