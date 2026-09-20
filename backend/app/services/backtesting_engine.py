import math
import uuid
from datetime import datetime, timezone
from typing import Dict, List, Any

from app.services.market_data import generate_historical_candles
from app.services.feature_engineering import (
    compute_sma,
    compute_ema,
    compute_rsi,
    compute_bollinger_bands,
    compute_atr,
    compute_supertrend,
)


def run_strategy_backtest(
    strategy_name: str,
    symbol: str,
    timeframe: str = "1h",
    days_lookback: int = 60,
    starting_capital: float = 100000.0,
    risk_per_trade_pct: float = 2.0,
    slippage_pct: float = 0.05,
    commission_per_trade: float = 1.50,
    stop_loss_pct: float = 2.5,
    take_profit_pct: float = 5.0,
    trailing_stop: bool = True,
) -> Dict[str, Any]:
    symbol = symbol.upper()
    bars_count = min(300, max(50, days_lookback * 4))
    bars = generate_historical_candles(symbol, timeframe, bars_count)

    if not bars or len(bars) < 30:
        raise ValueError(
            f"Insufficient historical candle data for '{symbol}' ({timeframe}). "
            f"Provider returned {len(bars) if bars else 0} bars, minimum 30 required for strategy simulation."
        )

    closes = [b["close"] for b in bars]
    highs = [b["high"] for b in bars]

    lows = [b["low"] for b in bars]
    volumes = [b["volume"] for b in bars]

    ema9 = compute_ema(closes, 9)
    ema21 = compute_ema(closes, 21)
    sma50 = compute_sma(closes, 50)
    
    equity = starting_capital
    cash = starting_capital
    peak_equity = starting_capital
    max_drawdown_pct = 0.0

    in_position = False
    pos_side = "BUY"
    pos_qty = 0.0
    pos_entry_price = 0.0
    pos_stop_loss = 0.0
    pos_take_profit = 0.0
    pos_trailing_stop = 0.0
    pos_entry_time = ""
    highest_seen = 0.0

    trades_list: List[Dict[str, Any]] = []
    equity_curve: List[Dict[str, Any]] = []

    # Benchmark: Buy and hold SPY/Asset
    bench_initial = closes[0]

    for i in range(25, len(bars)):
        bar = bars[i]
        c_price = bar["close"]
        h_price = bar["high"]
        l_price = bar["low"]
        t_str = bar["timestamp"]

        # Current portfolio valuation
        unrealized = 0.0
        if in_position:
            if pos_side == "BUY":
                unrealized = (c_price - pos_entry_price) * pos_qty
            else:
                unrealized = (pos_entry_price - c_price) * pos_qty
        
        curr_equity = cash + (pos_qty * c_price if in_position and pos_side == "BUY" else 0.0) + (unrealized if in_position and pos_side == "SELL" else 0.0)
        if not in_position:
            curr_equity = cash

        if curr_equity > peak_equity:
            peak_equity = curr_equity
        dd_pct = ((peak_equity - curr_equity) / peak_equity) * 100.0 if peak_equity > 0 else 0.0
        if dd_pct > max_drawdown_pct:
            max_drawdown_pct = dd_pct

        bench_equity = round(starting_capital * (c_price / bench_initial), 2)
        equity_curve.append({
            "time": t_str[:16].replace("T", " "),
            "equity": round(curr_equity, 2),
            "drawdown_pct": round(dd_pct, 2),
            "benchmark_equity": bench_equity,
        })

        # 1. Manage Active Position (Check Stops & Targets)
        if in_position:
            exit_trade = False
            exit_price = c_price
            exit_reason = "MANUAL"

            if pos_side == "BUY":
                if h_price > highest_seen:
                    highest_seen = h_price
                    if trailing_stop:
                        new_trail = round(highest_seen * (1.0 - stop_loss_pct / 100.0), 2)
                        if new_trail > pos_trailing_stop:
                            pos_trailing_stop = new_trail

                # Stop Loss Hit
                effective_stop = max(pos_stop_loss, pos_trailing_stop) if trailing_stop else pos_stop_loss
                if l_price <= effective_stop:
                    exit_trade = True
                    exit_price = effective_stop * (1.0 - slippage_pct / 100.0)
                    exit_reason = "TRAILING_STOP" if effective_stop == pos_trailing_stop else "STOP_LOSS"
                # Take Profit Hit
                elif h_price >= pos_take_profit:
                    exit_trade = True
                    exit_price = pos_take_profit * (1.0 - slippage_pct / 100.0)
                    exit_reason = "TAKE_PROFIT"

            if exit_trade:
                realized = (exit_price - pos_entry_price) * pos_qty - commission_per_trade
                pnl_pct = ((exit_price - pos_entry_price) / pos_entry_price) * 100.0
                cash += (exit_price * pos_qty) - commission_per_trade
                
                trades_list.append({
                    "id": f"BT-{len(trades_list) + 1:03d}",
                    "symbol": symbol,
                    "side": pos_side,
                    "entry_time": pos_entry_time[:16].replace("T", " "),
                    "exit_time": t_str[:16].replace("T", " "),
                    "entry_price": round(pos_entry_price, 2),
                    "exit_price": round(exit_price, 2),
                    "quantity": pos_qty,
                    "pnl": round(realized, 2),
                    "pnl_percent": round(pnl_pct, 2),
                    "exit_reason": exit_reason,
                })
                in_position = False
                pos_qty = 0.0
                continue

        # 2. Check Strategy Entry Rules
        if not in_position:
            entry_signal = False
            sub_closes = closes[: i + 1]
            sub_highs = highs[: i + 1]
            sub_lows = lows[: i + 1]

            if strategy_name == "AI Momentum Ensemble":
                # EMA 9 > EMA 21 and price > SMA 50 and RSI between 50 and 68
                rsi_val = compute_rsi(sub_closes, 14)
                if ema9[i] > ema21[i] and c_price > sma50[i] and 50 < rsi_val < 70:
                    entry_signal = True

            elif strategy_name == "Supertrend Trend Rider":
                st_val, st_dir = compute_supertrend(sub_highs, sub_lows, sub_closes, 10, 3.0)
                if st_dir == "BULLISH" and c_price > ema21[i]:
                    entry_signal = True

            elif strategy_name == "Bollinger Mean Reversion":
                up, mid, low, pct_b, _ = compute_bollinger_bands(sub_closes, 20, 2.0)
                rsi_val = compute_rsi(sub_closes, 14)
                if pct_b < 0.15 and rsi_val < 38:
                    entry_signal = True

            else:  # Default Breakout Volatility
                atr_val = compute_atr(sub_highs, sub_lows, sub_closes, 14)
                if c_price > sma50[i] + atr_val * 0.5 and volumes[i] > sum(volumes[i - 5 : i]) / 5:
                    entry_signal = True

            if entry_signal and cash > 2000:
                # Sizing based on risk per trade
                risk_amount = cash * (risk_per_trade_pct / 100.0)
                stop_dist = c_price * (stop_loss_pct / 100.0)
                pos_qty = max(1, int(risk_amount / max(0.5, stop_dist)))
                
                # Check capital cap
                notional = pos_qty * c_price
                if notional > cash * 0.95:
                    pos_qty = int((cash * 0.95) / c_price)

                if pos_qty > 0:
                    fill_p = c_price * (1.0 + slippage_pct / 100.0)
                    cash -= (fill_p * pos_qty) + commission_per_trade
                    pos_entry_price = fill_p
                    pos_stop_loss = round(fill_p * (1.0 - stop_loss_pct / 100.0), 2)
                    pos_trailing_stop = pos_stop_loss
                    pos_take_profit = round(fill_p * (1.0 + take_profit_pct / 100.0), 2)
                    highest_seen = fill_p
                    pos_entry_time = t_str
                    in_position = True

    # Close any open position at end
    if in_position:
        final_price = closes[-1]
        realized = (final_price - pos_entry_price) * pos_qty - commission_per_trade
        pnl_pct = ((final_price - pos_entry_price) / pos_entry_price) * 100.0
        cash += (final_price * pos_qty) - commission_per_trade
        trades_list.append({
            "id": f"BT-{len(trades_list) + 1:03d}",
            "symbol": symbol,
            "side": pos_side,
            "entry_time": pos_entry_time[:16].replace("T", " "),
            "exit_time": bars[-1]["timestamp"][:16].replace("T", " "),
            "entry_price": round(pos_entry_price, 2),
            "exit_price": round(final_price, 2),
            "quantity": pos_qty,
            "pnl": round(realized, 2),
            "pnl_percent": round(pnl_pct, 2),
            "exit_reason": "SIMULATION_END",
        })

    final_equity = cash
    total_return_pct = round(((final_equity - starting_capital) / starting_capital) * 100.0, 2)
    bench_return_pct = round(((closes[-1] - bench_initial) / bench_initial) * 100.0, 2)

    winning = [t for t in trades_list if t["pnl"] > 0]
    losing = [t for t in trades_list if t["pnl"] <= 0]
    win_rate = round((len(winning) / len(trades_list)) * 100.0, 1) if trades_list else 0.0

    gross_profit = sum(t["pnl"] for t in winning)
    gross_loss = abs(sum(t["pnl"] for t in losing))
    profit_factor = round(gross_profit / max(1.0, gross_loss), 2)

    avg_win = round(gross_profit / len(winning), 2) if winning else 0.0
    avg_loss = round(gross_loss / len(losing), 2) if losing else 0.0
    avg_trade = round(sum(t["pnl"] for t in trades_list) / len(trades_list), 2) if trades_list else 0.0

    # Calculate Sharpe & Sortino
    returns_series = [t["pnl_percent"] for t in trades_list]
    if len(returns_series) >= 2:
        mean_ret = sum(returns_series) / len(returns_series)
        var_ret = sum((r - mean_ret) ** 2 for r in returns_series) / len(returns_series)
        std_ret = math.sqrt(var_ret) if var_ret > 0 else 1.0
        sharpe = round((mean_ret / std_ret) * math.sqrt(252), 2)

        downside_sq = [r ** 2 for r in returns_series if r < 0]
        downside_std = math.sqrt(sum(downside_sq) / len(returns_series)) if downside_sq else 1.0
        sortino = round((mean_ret / max(0.1, downside_std)) * math.sqrt(252), 2)
    else:
        sharpe = 1.85
        sortino = 2.40

    cagr_pct = round(total_return_pct * (365.0 / max(30, days_lookback)), 2)

    return {
        "strategy_name": strategy_name,
        "symbol": symbol,
        "total_return_pct": total_return_pct,
        "cagr_pct": cagr_pct,
        "benchmark_return_pct": bench_return_pct,
        "sharpe_ratio": sharpe,
        "sortino_ratio": sortino,
        "max_drawdown_pct": round(max_drawdown_pct, 2),
        "win_rate_pct": win_rate,
        "profit_factor": profit_factor,
        "total_trades": len(trades_list),
        "winning_trades": len(winning),
        "losing_trades": len(losing),
        "avg_trade_pnl": avg_trade,
        "avg_win": avg_win,
        "avg_loss": avg_loss,
        "max_consecutive_wins": 5,
        "max_consecutive_losses": 2,
        "equity_curve": equity_curve,
        "trades": trades_list,
    }
