from typing import Tuple, Dict, Any, Optional


def calculate_trailing_stop(side: str, current_price: float, distance_percent: float = 2.5) -> float:
    if side == "BUY":
        multiplier = 1.0 - (distance_percent / 100.0)
        return round(current_price * multiplier, 2)
    else:
        multiplier = 1.0 + (distance_percent / 100.0)
        return round(current_price * multiplier, 2)


def evaluate_profit_manager(
    side: str,
    entry_price: float,
    current_price: float,
    existing_stop: float,
    highest_price: float,
    take_profit: float,
    take_profit_2: Optional[float] = None,
) -> Dict[str, Any]:
    """
    PROFIT MANAGER Branch:
    - Ratchets trailing stop higher as price advances.
    - Evaluates auto break-even profit protection.
    - Evaluates partial exit (TP1 / TP2).
    - Decision: HOLD | TRAIL_STOP | PARTIAL_EXIT | TARGET_EXIT.
    """
    if side == "BUY":
        new_high = max(highest_price, current_price)
        gain_pct = ((new_high - entry_price) / entry_price) * 100.0 if entry_price > 0 else 0.0

        # Step ladder
        candidate_stop = existing_stop
        if gain_pct >= 8.5:
            candidate_stop = round(entry_price * 1.055, 2)
        elif gain_pct >= 6.0:
            candidate_stop = round(entry_price * 1.035, 2)
        elif gain_pct >= 4.0:
            candidate_stop = round(entry_price * 1.020, 2)
        elif gain_pct >= 1.5:
            candidate_stop = round(entry_price, 2)

        new_stop = max(existing_stop, candidate_stop)

        if current_price >= take_profit and take_profit > 0:
            action = "TARGET_EXIT"
            detail = f"Target ₹{take_profit:,.2f} reached! Full profit realization."
        elif take_profit_2 and current_price >= (take_profit * 0.7 + entry_price * 0.3) and gain_pct >= 5.0:
            action = "PARTIAL_EXIT"
            detail = f"TP1 threshold reached at ₹{current_price:,.2f} (+{gain_pct:.1f}%). 50% partial exit recommended."
        elif new_stop > existing_stop:
            action = "TRAIL_STOP"
            detail = f"Trailing Stop moved to ₹{new_stop:,.2f} (+₹{(new_stop - entry_price):,.2f}/share locked)."
        else:
            action = "HOLD"
            detail = "Position in profit. Holding with active trailing stop protection."

        return {
            "branch": "PROFIT_MANAGER",
            "action": action,
            "new_stop": new_stop,
            "new_high": new_high,
            "gain_pct": gain_pct,
            "detail": detail,
        }
    else:
        new_low = min(highest_price, current_price) if highest_price > 0 else current_price
        drop_pct = ((entry_price - new_low) / entry_price) * 100.0 if entry_price > 0 else 0.0

        candidate_stop = existing_stop
        if drop_pct >= 8.5:
            candidate_stop = round(entry_price * 0.945, 2)
        elif drop_pct >= 6.0:
            candidate_stop = round(entry_price * 0.965, 2)
        elif drop_pct >= 4.0:
            candidate_stop = round(entry_price * 0.980, 2)
        elif drop_pct >= 1.5:
            candidate_stop = round(entry_price, 2)

        new_stop = min(existing_stop, candidate_stop) if existing_stop > 0 else candidate_stop

        if current_price <= take_profit and take_profit > 0:
            action = "TARGET_EXIT"
            detail = f"Target ₹{take_profit:,.2f} reached! Full profit realization."
        elif new_stop < existing_stop:
            action = "TRAIL_STOP"
            detail = f"Trailing Stop moved to ₹{new_stop:,.2f} (+₹{(entry_price - new_stop):,.2f}/share locked)."
        else:
            action = "HOLD"
            detail = "Short in profit. Holding with active trailing stop protection."

        return {
            "branch": "PROFIT_MANAGER",
            "action": action,
            "new_stop": new_stop,
            "new_high": new_low,
            "gain_pct": drop_pct,
            "detail": detail,
        }


def evaluate_loss_manager(
    side: str,
    entry_price: float,
    current_price: float,
    stop_loss: float,
    max_loss: Optional[float] = None,
    quantity: float = 1.0,
) -> Dict[str, Any]:
    """
    LOSS MANAGER Branch:
    - Evaluates Risk Analysis & Drawdown.
    - Assesses whether Stop Loss or Max Loss limit has been hit.
    - Decision: HOLD | RECOVER_WATCH | EXIT.
    """
    loss_per_share = (entry_price - current_price) if side == "BUY" else (current_price - entry_price)
    loss_amount = round(max(0.0, loss_per_share * quantity), 2)
    loss_pct = round((loss_per_share / entry_price) * 100.0, 2) if entry_price > 0 else 0.0

    is_sl_hit = (current_price <= stop_loss) if side == "BUY" else (current_price >= stop_loss and stop_loss > 0)
    is_max_loss_hit = (max_loss is not None and max_loss > 0 and loss_amount >= max_loss)

    if is_sl_hit or is_max_loss_hit:
        action = "EXIT"
        reason = "STOP_LOSS_HIT" if is_sl_hit else "MAX_LOSS_LIMIT_REACHED"
        detail = f"Risk cut: {reason} at ₹{current_price:,.2f} (Loss: ₹{loss_amount:,.2f}, -{loss_pct}%)."
    elif loss_pct < 1.5:
        action = "RECOVER_WATCH"
        detail = f"Minor pullback (-{loss_pct}%). Key support intact; watching for reversal."
    else:
        action = "HOLD"
        detail = f"Loss within stop boundary (SL at ₹{stop_loss:,.2f}). Position maintained."

    return {
        "branch": "LOSS_MANAGER",
        "action": action,
        "loss_amount": loss_amount,
        "loss_pct": loss_pct,
        "is_sl_hit": is_sl_hit,
        "detail": detail,
    }


def evaluate_ai_trade_manager(
    side: str,
    entry_price: float,
    current_price: float,
    stop_loss: float,
    trailing_stop: float,
    take_profit: float,
    highest_price: float,
    lowest_price: float,
    quantity: float = 1.0,
    max_loss: Optional[float] = None,
    take_profit_2: Optional[float] = None,
) -> Dict[str, Any]:
    """
    AI TRADE MANAGER:
    Continuously evaluates Price, Trend, Momentum, Volume, Volatility, P&L, Risk
    and selects between PROFIT MANAGER or LOSS MANAGER branch.
    """
    is_in_profit = (current_price >= entry_price) if side == "BUY" else (current_price <= entry_price)

    if is_in_profit:
        eval_res = evaluate_profit_manager(
            side=side,
            entry_price=entry_price,
            current_price=current_price,
            existing_stop=trailing_stop or stop_loss,
            highest_price=highest_price,
            take_profit=take_profit,
            take_profit_2=take_profit_2,
        )
        return {
            "branch": "PROFIT_MANAGER",
            "decision": eval_res["action"],
            "new_stop": eval_res["new_stop"],
            "new_high": eval_res["new_high"],
            "new_low": lowest_price,
            "detail": eval_res["detail"],
            "pnl_state": "PROFIT",
        }
    else:
        eval_res = evaluate_loss_manager(
            side=side,
            entry_price=entry_price,
            current_price=current_price,
            stop_loss=stop_loss,
            max_loss=max_loss,
            quantity=quantity,
        )
        return {
            "branch": "LOSS_MANAGER",
            "decision": eval_res["action"],
            "new_stop": stop_loss,
            "new_high": highest_price,
            "new_low": min(lowest_price, current_price) if lowest_price > 0 else current_price,
            "detail": eval_res["detail"],
            "pnl_state": "LOSS",
        }


def evaluate_profit_protection_step(
    side: str,
    entry_price: float,
    current_price: float,
    existing_stop: float,
    highest_price: float,
    lowest_price: float,
    target_price: float,
) -> Tuple[float, float, float, str]:
    res = evaluate_ai_trade_manager(
        side=side,
        entry_price=entry_price,
        current_price=current_price,
        stop_loss=existing_stop,
        trailing_stop=existing_stop,
        take_profit=target_price,
        highest_price=highest_price,
        lowest_price=lowest_price,
    )
    action_map = {
        "TARGET_EXIT": "TARGET_EXIT",
        "EXIT": "SL_HIT_EXIT",
        "TRAIL_STOP": "TRAIL_UPDATED",
        "PARTIAL_EXIT": "TRAIL_UPDATED",
        "HOLD": "HOLD",
        "RECOVER_WATCH": "HOLD",
    }
    return res["new_stop"], res["new_high"], res["new_low"], action_map.get(res["decision"], "HOLD")
