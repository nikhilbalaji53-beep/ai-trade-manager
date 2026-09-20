import uuid
from datetime import datetime, timezone
from typing import List, Dict, Any

from app.services.market_data import (
    get_quotes,
    get_current_live_price,
    generate_historical_candles,
)
from app.services.feature_engineering import extract_all_features
from app.services.ml_engine import get_ml_prediction


def generate_ai_signals() -> List[Dict[str, Any]]:
    quotes = get_quotes()
    signals = []

    for quote in quotes:
        symbol = quote["symbol"]
        curr_price = quote["price"]
        bars = generate_historical_candles(symbol, "1h", 60)
        tech = extract_all_features(symbol, bars)
        ml_pred = get_ml_prediction(symbol)

        conviction = ml_pred.get("confidence", ml_pred.get("ensemble_conviction", 50.0))
        direction = ml_pred.get("direction", ml_pred.get("rf_direction", "SIDEWAYS"))
        rationale = ml_pred.get("rationale", f"Signal generated from {symbol} quantitative indicators.")
        atr = tech.get("atr14", curr_price * 0.02)

        if direction in ["UP", "BULLISH"] and conviction >= 70:
            action = "BUY"
            sl = round(curr_price - (atr * 1.8), 2)
            tp1 = round(curr_price + (atr * 2.5), 2)
            tp2 = round(curr_price + (atr * 4.2), 2)
            risk = max(0.01, curr_price - sl)
            reward = tp1 - curr_price
            rr = round(reward / risk, 2)

            signals.append({
                "id": f"SIG-{symbol}-{int(curr_price)}",
                "symbol": symbol,
                "action": action,
                "strategy_name": "AI Momentum Scout" if conviction > 80 else "Trend Follower",
                "conviction": conviction,
                "entry_price": curr_price,
                "stop_loss": sl,
                "take_profit_1": tp1,
                "take_profit_2": tp2,
                "risk_reward_ratio": rr,
                "timeframe": "1h / 4h Swing",
                "expected_duration": "2 - 5 days",
                "rationale": ml_pred["rationale"],
                "status": "ACTIVE",
                "generated_at": datetime.now(timezone.utc).isoformat(),
            })

        elif direction in ["DOWN", "BEARISH"] and conviction >= 72:
            action = "SELL"
            sl = round(curr_price + (atr * 1.8), 2)
            tp1 = round(curr_price - (atr * 2.5), 2)
            tp2 = round(curr_price - (atr * 4.2), 2)
            risk = max(0.01, sl - curr_price)
            reward = curr_price - tp1
            rr = round(reward / risk, 2)

            signals.append({
                "id": f"SIG-{symbol}-{int(curr_price)}",
                "symbol": symbol,
                "action": action,
                "strategy_name": "Volatility Breakdown",
                "conviction": conviction,
                "entry_price": curr_price,
                "stop_loss": sl,
                "take_profit_1": tp1,
                "take_profit_2": tp2,
                "risk_reward_ratio": rr,
                "timeframe": "1h Swing",
                "expected_duration": "1 - 3 days",
                "rationale": ml_pred["rationale"],
                "status": "ACTIVE",
                "generated_at": datetime.now(timezone.utc).isoformat(),
            })

    return signals
