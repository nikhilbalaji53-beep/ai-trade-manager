"""
Analytics API Routes — TradePilot

All metrics returned here must be computed from actual trade records
in the portfolio store. Hardcoded/fake performance figures are not allowed.
"""
from typing import List, Dict, Any
from fastapi import APIRouter, HTTPException

from app.schemas.trade import (
    MLPrediction,
    NewsArticle,
    SentimentSummary,
    BacktestRequest,
    BacktestResponse,
    AISignal,
)
from app.services.ml_engine import get_ml_prediction, get_sentiment_analytics
from app.services.market_data import get_news_feed
from app.services.market_data.instrument_manager import get_instrument_manager
from app.services.backtesting_engine import run_strategy_backtest
from app.services.decision_engine import generate_ai_signals
from app.config import get_settings
from app.database import get_store

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("/predictions/{symbol}", response_model=MLPrediction)
def symbol_prediction(symbol: str):
    symbol = symbol.upper()
    inst = get_instrument_manager().get_instrument(symbol)
    if not inst:
        raise HTTPException(status_code=404, detail=f"Symbol {symbol} not found in Indian Instrument Master")
    return get_ml_prediction(symbol)


@router.get("/predictions", response_model=List[MLPrediction])
def all_predictions():
    return [get_ml_prediction(sym) for sym in ["RELIANCE", "TCS", "INFY", "HDFCBANK", "ICICIBANK"]]


@router.get("/sentiment", response_model=SentimentSummary)
def sentiment_analysis():
    return get_sentiment_analytics()


@router.get("/news", response_model=List[NewsArticle])
def news_feed():
    return get_news_feed()


@router.post("/backtest", response_model=BacktestResponse)
def run_backtest(req: BacktestRequest):
    try:
        return run_strategy_backtest(
            strategy_name=req.strategy_name,
            symbol=req.symbol,
            timeframe=req.timeframe,
            days_lookback=req.days_lookback,
            starting_capital=req.starting_capital,
            risk_per_trade_pct=req.risk_per_trade_pct,
            slippage_pct=req.slippage_pct,
            commission_per_trade=req.commission_per_trade,
            stop_loss_pct=req.stop_loss_pct,
            take_profit_pct=req.take_profit_pct,
            trailing_stop=req.trailing_stop,
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e)) from e


@router.get("/signals", response_model=List[AISignal])
def trade_signals():
    return generate_ai_signals()


@router.get("/performance-deck")
def performance_deck():
    """
    Return performance analytics computed from REAL closed trades.

    When no trades have been placed, all metrics are zero.
    This endpoint MUST NEVER return hardcoded or fake performance figures.
    """
    settings = get_settings()
    store = get_store(settings.starting_capital)

    trades = store.trades  # Closed trade records

    if not trades:
        return {
            "net_pnl":              0.0,
            "win_rate":             0.0,
            "profit_factor":        0.0,
            "sharpe_ratio":         None,  # Insufficient data
            "sortino_ratio":        None,
            "max_drawdown_pct":     0.0,
            "cagr_pct":             None,
            "total_trades":         0,
            "avg_win_trade":        0.0,
            "avg_loss_trade":       0.0,
            "strategy_performance": [],
            "monthly_returns":      [],
            "data_note": (
                "No closed trades found. Place real trades to generate performance metrics. "
                "All figures will be computed from actual trade records."
            ),
        }

    # --- Compute real metrics from closed trade records ---
    realized_pnls = [t.realized_pnl for t in trades if hasattr(t, "realized_pnl") and t.realized_pnl is not None]

    wins   = [p for p in realized_pnls if p > 0]
    losses = [p for p in realized_pnls if p < 0]

    total_pnl    = round(sum(realized_pnls), 2)
    total_trades = len(realized_pnls)
    win_count    = len(wins)
    win_rate     = round((win_count / total_trades) * 100, 2) if total_trades > 0 else 0.0

    avg_win  = round(sum(wins) / len(wins), 2) if wins else 0.0
    avg_loss = round(sum(losses) / len(losses), 2) if losses else 0.0

    total_wins_val   = sum(wins) if wins else 0.0
    total_losses_val = abs(sum(losses)) if losses else 0.0
    profit_factor    = round(total_wins_val / total_losses_val, 2) if total_losses_val > 0 else None

    # Max drawdown: simple running max drawdown over ordered trade sequence
    max_drawdown_pct = 0.0
    running_pnl      = 0.0
    peak_pnl         = 0.0
    for pnl in realized_pnls:
        running_pnl += pnl
        if running_pnl > peak_pnl:
            peak_pnl = running_pnl
        if peak_pnl > 0:
            drawdown = (peak_pnl - running_pnl) / peak_pnl * 100.0
            if drawdown > max_drawdown_pct:
                max_drawdown_pct = drawdown

    # Strategy breakdown
    strategy_map: Dict[str, Dict[str, Any]] = {}
    for t in trades:
        if not hasattr(t, "realized_pnl") or t.realized_pnl is None:
            continue
        strat = getattr(t, "strategy", "Unknown")
        if strat not in strategy_map:
            strategy_map[strat] = {"trades": 0, "wins": 0, "pnl": 0.0}
        strategy_map[strat]["trades"] += 1
        strategy_map[strat]["pnl"]    += t.realized_pnl
        if t.realized_pnl > 0:
            strategy_map[strat]["wins"] += 1

    strategy_performance = [
        {
            "strategy": k,
            "trades":   v["trades"],
            "win_rate": round(v["wins"] / v["trades"] * 100, 1) if v["trades"] > 0 else 0.0,
            "pnl":      round(v["pnl"], 2),
        }
        for k, v in strategy_map.items()
    ]

    return {
        "net_pnl":              total_pnl,
        "win_rate":             win_rate,
        "profit_factor":        profit_factor,
        "sharpe_ratio":         None,   # Requires time-series returns data
        "sortino_ratio":        None,   # Requires time-series returns data
        "max_drawdown_pct":     round(max_drawdown_pct, 2),
        "cagr_pct":             None,   # Requires date range of trading
        "total_trades":         total_trades,
        "avg_win_trade":        avg_win,
        "avg_loss_trade":       avg_loss,
        "strategy_performance": strategy_performance,
        "monthly_returns":      [],     # Requires trade timestamps grouped by month
        "data_note":            "Computed from actual closed trade records in the portfolio store.",
    }
