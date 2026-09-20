"""
AI Trade Plan Generation Engine — TradePilot AI

Implements Phase 9:
  - Dynamic entry zones based on ATR & pivots (pullback vs breakout).
  - Multi-tier targets (Target 1: 1.5R, Target 2: 2.5R, Target 3: 3.5R runner).
  - Dynamic stop loss (1.5 - 2.0x ATR) and trailing stop percentage.
  - Position sizing calculator:
      max_capital_risk = account_balance * (risk_per_trade_pct / 100)
      suggested_quantity = max_capital_risk / abs(entry - stop_loss)
  - Pre-flight Trade Checklist:
      5 explicit Buy / Entry conditions
      5 explicit Do-Not-Buy / Invalidation conditions
  - Multi-Timeframe Integration:
      Aligns with MultiTimeframeEngine confluence score & tier.
  - Multi-Market & Multi-Currency:
      Indian (INR, ₹, NSE/BSE) vs US (USD, $, NASDAQ/NYSE).
  - Probabilistic Safety Guard:
      Zero guaranteed profit claims.
      Mandatory disclaimer: "AI predictions are probabilistic and do not guarantee future returns."
"""
from datetime import datetime, timezone
import math
import time
import logging
from typing import Dict, List, Any, Optional, Tuple

from app.schemas.ai import (
    AITradePlan,
    ConfidenceLevel,
    TradeAction,
    GenerateTradePlanRequest,
)
from app.services.market_data import (
    get_current_live_price,
    generate_historical_candles,
)
from app.services.ml_engine import get_ml_prediction
from app.services.feature_engineering import extract_all_features
from app.services.instrument_master import get_instrument_by_symbol
from app.services.multi_timeframe_engine import run_symbol_multi_timeframe_analysis

logger = logging.getLogger(__name__)


_TRADE_PLAN_CACHE: Dict[str, Tuple[float, AITradePlan]] = {}
_TRADE_PLAN_CACHE_TTL = 30.0  # 30 seconds


def generate_trade_plan(
    symbol: str,
    requested_direction: Optional[str] = None,
    account_balance: float = 100000.0,
    risk_per_trade_pct: float = 1.0,
    timeframe: str = "1h",
) -> AITradePlan:
    """
    Generate a full probabilistic AI Trade Plan for an instrument.
    """
    clean_sym = (
        symbol.upper()
        .replace(".NS", "")
        .replace(".BO", "")
        .replace("NSE:", "")
        .replace("BSE:", "")
        .replace("NASDAQ:", "")
        .replace("NYSE:", "")
        .strip()
    )

    cache_key = f"{clean_sym}_{requested_direction}_{account_balance}_{risk_per_trade_pct}_{timeframe}"
    now = time.time()
    if cache_key in _TRADE_PLAN_CACHE:
        cached_ts, cached_plan = _TRADE_PLAN_CACHE[cache_key]
        if (now - cached_ts) < _TRADE_PLAN_CACHE_TTL and cached_plan:
            return cached_plan

    # 1. Fetch instrument metadata
    inst = get_instrument_by_symbol(clean_sym)
    market = inst.get("market", "IN") if inst else ("US" if clean_sym.startswith("NASDAQ:") or clean_sym.startswith("NYSE:") else "IN")
    currency = inst.get("currency", "INR") if inst else ("USD" if market == "US" else "INR")
    curr_symbol = inst.get("currency_symbol", "₹") if inst else ("$" if market == "US" else "₹")

    # 2. Fetch live price
    curr_price = get_current_live_price(clean_sym)
    if curr_price is None or curr_price <= 0:
        raise ValueError(f"Real market quote for '{clean_sym}' not available from active provider.")

    # 3. Retrieve historical candles & technical indicators
    bars = generate_historical_candles(clean_sym, timeframe, 60)
    tech = extract_all_features(clean_sym, bars) if bars else {}
    ml_pred = get_ml_prediction(clean_sym)

    # 4. Multi-timeframe confluence lookup (safe fallback if feed error)
    mtf_trend = "NEUTRAL"
    mtf_score = 50.0
    mtf_reasons = []
    try:
        mtf = run_symbol_multi_timeframe_analysis(clean_sym)
        if mtf:
            mtf_trend = mtf.overall_trend
            mtf_score = mtf.confluence_score
            mtf_reasons = mtf.reasons[:2]
    except Exception as e:
        logger.warning(f"Could not calculate MTF confluence for {clean_sym}: {e}")

    # 5. Volatility (ATR) & Direction Determination
    atr = float(tech.get("atr14", curr_price * 0.02))
    if atr <= 0:
        atr = curr_price * 0.02

    bull_prob = float(ml_pred.get("bullish_probability", 0.50))
    bear_prob = float(ml_pred.get("bearish_probability", 0.50))
    ml_direction = str(ml_pred.get("direction", "SIDEWAYS")).upper()

    if requested_direction in ["BUY", "SELL"]:
        direction = requested_direction.upper()
    else:
        if mtf_trend == "BULLISH" or bull_prob > 0.55 or ml_direction in ["UP", "BULLISH"]:
            direction = "BUY"
        elif mtf_trend == "BEARISH" or bear_prob > 0.55 or ml_direction in ["DOWN", "BEARISH"]:
            direction = "SELL"
        else:
            direction = "BUY" if bull_prob >= bear_prob else "SELL"

    is_buy = direction == "BUY"

    # 6. Dynamic Entry Zone, Stop Loss & Multi-tier Targets
    if is_buy:
        entry_low = round(curr_price - (atr * 0.4), 2)
        entry_high = round(curr_price + (atr * 0.2), 2)
        entry_mid = round((entry_low + entry_high) / 2.0, 2)
        
        sl = round(curr_price - (atr * 1.8), 2)
        risk_per_unit = max(0.01, entry_mid - sl)
        
        tp1 = round(entry_mid + (risk_per_unit * 1.5), 2)
        tp2 = round(entry_mid + (risk_per_unit * 2.5), 2)
        tp3 = round(entry_mid + (risk_per_unit * 3.5), 2)
        reward_per_unit = tp1 - entry_mid
        
        p_profit = max(0.15, min(0.85, bull_prob))
        trigger = f"Breakout above {curr_symbol}{entry_high:,.2f} or limit fill inside pullback zone ({curr_symbol}{entry_low:,.2f} - {curr_symbol}{entry_high:,.2f})"
    else:
        entry_low = round(curr_price - (atr * 0.2), 2)
        entry_high = round(curr_price + (atr * 0.4), 2)
        entry_mid = round((entry_low + entry_high) / 2.0, 2)
        
        sl = round(curr_price + (atr * 1.8), 2)
        risk_per_unit = max(0.01, sl - entry_mid)
        
        tp1 = round(entry_mid - (risk_per_unit * 1.5), 2)
        tp2 = round(entry_mid - (risk_per_unit * 2.5), 2)
        tp3 = round(entry_mid - (risk_per_unit * 3.5), 2)
        reward_per_unit = entry_mid - tp1
        
        p_profit = max(0.15, min(0.85, bear_prob))
        trigger = f"Breakdown below {curr_symbol}{entry_low:,.2f} or limit fill inside retest zone ({curr_symbol}{entry_low:,.2f} - {curr_symbol}{entry_high:,.2f})"

    p_loss = round(1.0 - p_profit, 2)
    p_profit = round(p_profit, 2)
    rr_ratio = round(reward_per_unit / risk_per_unit, 2)

    # 7. Position Sizing
    risk_pct = max(0.1, min(10.0, risk_per_trade_pct))
    max_capital_risk = round(account_balance * (risk_pct / 100.0), 2)
    
    lot_size = inst.get("lot_size", 1) if inst else 1
    raw_qty = max_capital_risk / risk_per_unit
    if market == "US":
        suggested_quantity = round(raw_qty, 2) if raw_qty < 1.0 else float(math.floor(raw_qty))
    else:
        suggested_quantity = float(max(lot_size, math.floor(raw_qty / lot_size) * lot_size))

    # 8. Score, Confidence & Risk Score
    model_conf = float(ml_pred.get("confidence", 50.0))
    trade_score = int(min(100, max(10, (p_profit * 50.0) + (mtf_score * 0.3) + (min(rr_ratio, 3.0) / 3.0 * 20.0))))

    atr_ratio = (atr / curr_price) if curr_price > 0 else 0.02
    raw_risk = (atr_ratio * 100.0) * 1.5 + (p_loss * 5.0) + (max(0, 2.0 - rr_ratio) * 2.0)
    risk_score = max(1, min(10, int(round(raw_risk))))

    if model_conf >= 75 and mtf_score >= 70:
        confidence = ConfidenceLevel.HIGH
    elif model_conf >= 55 or mtf_score >= 55:
        confidence = ConfidenceLevel.MEDIUM
    else:
        confidence = ConfidenceLevel.LOW

    if trade_score >= 75 and rr_ratio >= 1.4 and risk_score <= 7:
        decision = TradeAction.BUY if is_buy else TradeAction.SELL
    elif trade_score >= 50:
        decision = TradeAction.WAIT
    else:
        decision = TradeAction.NO_TRADE

    # 9. Pre-flight Checklists
    buy_conditions = [
        f"Price trades within planned entry zone ({curr_symbol}{entry_low:,.2f} – {curr_symbol}{entry_high:,.2f})",
        f"Hard stop loss is strictly honored at {curr_symbol}{sl:,.2f} (Max Risk: {curr_symbol}{max_capital_risk:,.2f})",
        f"Volume confirms directional move (volume ratio >= 1.2x 10-period moving average)",
        f"Multi-timeframe momentum is aligned or neutral without opposing major HTF structure",
        f"Real-time live market feed is actively verified with zero data staleness",
    ]

    do_not_buy_conditions = [
        f"Live market data feed is STALE (> 5 minutes without tick) or DISCONNECTED",
        f"Price closes beyond invalidation level ({curr_symbol}{sl:,.2f})",
        f"High-impact macroeconomic event or earnings report occurs within active trade horizon",
        f"Abnormally high spread or market volatility spikes above 2.5x ATR ({curr_symbol}{atr*2.5:,.2f})",
        f"Position risk exceeds maximum allowable threshold ({risk_pct}% of account balance)",
    ]

    reasons = [
        ml_pred.get("rationale", f"Directional indicators calibrated for {clean_sym}."),
        f"Risk/Reward ratio calculated at 1:{rr_ratio} across target tiers.",
        f"Calculated win probability: {int(p_profit*100)}% (probabilistic, non-guaranteed).",
        f"Position size: {suggested_quantity} units risked at {curr_symbol}{max_capital_risk:,.2f} ({risk_pct}% account risk).",
    ]
    if mtf_reasons:
        reasons.extend(mtf_reasons)

    plan = AITradePlan(
        symbol=clean_sym,
        direction=direction,
        entry_zone=f"{curr_symbol}{entry_low:,.2f} – {curr_symbol}{entry_high:,.2f}",
        stop_loss=sl,
        target_1=tp1,
        target_2=tp2,
        target_3=tp3,
        trailing_stop_pct=2.0,
        risk_reward_ratio=rr_ratio,
        profit_probability=p_profit,
        loss_probability=p_loss,
        confidence=confidence,
        trade_score=trade_score,
        risk_score=risk_score,
        decision=decision,
        market=market,
        currency=currency,
        currency_symbol=curr_symbol,
        current_price=curr_price,
        order_type="LIMIT",
        trigger_condition=trigger,
        suggested_quantity=suggested_quantity,
        max_capital_risk=max_capital_risk,
        reasons=reasons,
        buy_conditions=buy_conditions,
        do_not_buy_conditions=do_not_buy_conditions,
        disclaimer="AI predictions are probabilistic and do not guarantee future returns.",
        timestamp=datetime.now(timezone.utc).isoformat(),
    )
    _TRADE_PLAN_CACHE[cache_key] = (now, plan)
    return plan
