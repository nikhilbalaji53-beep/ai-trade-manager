"""
AI Analysis & Probabilistic P&L Prediction Routes — TradePilot AI

CRITICAL SAFETY DIRECTIVE:
  - All predictions are purely probabilistic.
  - Zero claims of "Guaranteed Profit", "100% Accuracy", or "Risk Free".
  - Always output Profit Probability, Loss Probability, Expected P&L Range, Risk Score, and Confidence.
  - Every prediction includes the mandatory disclaimer:
    "AI predictions are probabilistic and do not guarantee future returns."
"""
from datetime import datetime, timezone
import math
from fastapi import APIRouter, HTTPException

from app.schemas.ai import (
    PnLPredictionRequest,
    PnLPredictionResponse,
    PnLRange,
    AITradePlan,
    GenerateTradePlanRequest,
    AITradeAnalysisResponse,
    MultiTimeframeAnalysisResponse,
    MultiAgentConsensusResponse,
    ConfidenceLevel,
    TradeAction,
)
from app.services.market_data import (
    get_current_live_price,
    generate_historical_candles,
)
from app.services.ml_engine import get_ml_prediction
from app.services.feature_engineering import extract_all_features
from app.services.market_data.market_data_manager import get_market_data_manager
from app.services.multi_timeframe_engine import run_symbol_multi_timeframe_analysis

ai_router = APIRouter(prefix="/v1/ai", tags=["v1-ai"])


def _calculate_probabilistic_pnl(
    symbol: str,
    direction: str,
    entry_price: float,
    current_price: float,
    quantity: float,
    stop_loss: float,
    target: float,
    ml_pred: dict,
    tech: dict,
) -> PnLPredictionResponse:
    """Calculates purely probabilistic expected P&L scenarios based on real market data and ML model."""
    direction = direction.upper()
    is_buy = direction == "BUY"

    # Risk and reward points per unit
    if is_buy:
        risk_per_unit = max(0.01, entry_price - stop_loss)
        reward_per_unit = max(0.01, target - entry_price)
    else:
        risk_per_unit = max(0.01, stop_loss - entry_price)
        reward_per_unit = max(0.01, entry_price - target)

    rr_ratio = round(reward_per_unit / risk_per_unit, 2)

    # Base model probabilities from real historical quantitative training
    bull_prob = ml_pred.get("bullish_probability", 0.50)
    bear_prob = ml_pred.get("bearish_probability", 0.50)
    model_conf = ml_pred.get("confidence", 50.0)

    # Adjust win probability based on trade direction alignment with ML model
    if is_buy:
        p_profit = max(0.15, min(0.85, bull_prob))
    else:
        p_profit = max(0.15, min(0.85, bear_prob))
    p_loss = round(1.0 - p_profit, 2)
    p_profit = round(p_profit, 2)

    # Expected dollar/rupee amounts
    potential_profit = round(reward_per_unit * quantity, 2)
    potential_loss = round(risk_per_unit * quantity, 2)

    # Expected P&L = (P_profit * Profit) - (P_loss * Loss)
    expected_pnl = round((p_profit * potential_profit) - (p_loss * potential_loss), 2)

    # Expected range
    pnl_min = round(-potential_loss, 2)
    pnl_max = round(potential_profit, 2)

    # Risk Score (0 = lowest risk, 100 = extreme risk)
    # Higher volatility (ATR) and poor R:R increase risk score
    atr = tech.get("atr14", current_price * 0.02)
    atr_pct = (atr / current_price) * 100.0 if current_price > 0 else 2.0
    risk_score = int(min(100, max(10, (atr_pct * 15.0) + (max(0, 2.0 - rr_ratio) * 20.0) + (p_loss * 40.0))))

    # Confidence classification
    if model_conf >= 75 and len(tech) > 5:
        confidence_level = ConfidenceLevel.HIGH
    elif model_conf >= 55:
        confidence_level = ConfidenceLevel.MEDIUM
    else:
        confidence_level = ConfidenceLevel.LOW

    # Decision logic
    reasons = []
    if ml_pred.get("rationale"):
        reasons.append(ml_pred["rationale"])

    if p_profit >= 0.65 and rr_ratio >= 1.5 and risk_score < 70 and confidence_level != ConfidenceLevel.LOW:
        recommended_action = TradeAction.BUY if is_buy else TradeAction.SELL
        reasons.append(f"Favorable Risk/Reward (1:{rr_ratio}) with {int(p_profit*100)}% directional win probability.")
    elif rr_ratio < 1.2:
        recommended_action = TradeAction.WAIT
        reasons.append(f"Risk/Reward ratio (1:{rr_ratio}) is below prudent trading threshold (min 1:1.5).")
    elif risk_score >= 70:
        recommended_action = TradeAction.NO_TRADE
        reasons.append(f"Elevated risk score ({risk_score}/100) due to market volatility.")
    else:
        recommended_action = TradeAction.WAIT
        reasons.append("Consolidation or mixed technical signals. Patience advised before entry.")

    return PnLPredictionResponse(
        symbol=symbol.upper(),
        direction=direction,
        current_price=current_price,
        entry_price=entry_price,
        quantity=quantity,
        profit_probability=p_profit,
        loss_probability=p_loss,
        expected_profit=potential_profit,
        expected_loss=potential_loss,
        expected_pnl=expected_pnl,
        expected_pnl_range=PnLRange(min=pnl_min, max=pnl_max),
        risk_reward_ratio=rr_ratio,
        confidence=confidence_level,
        confidence_score=model_conf,
        risk_score=risk_score,
        recommended_action=recommended_action,
        reasons=reasons,
        disclaimer="AI predictions are probabilistic and do not guarantee future returns.",
        timestamp=datetime.now(timezone.utc).isoformat(),
        model_version="tradepilot-probabilistic-v2.5",
    )


@ai_router.post("/predict-pnl", response_model=PnLPredictionResponse)
def predict_trade_pnl(req: PnLPredictionRequest):
    """
    Produce a probabilistic P&L prediction and scenario analysis for a hypothetical trade.
    Uses REAL live market price and technical indicator models.
    """
    clean_sym = req.symbol.upper().replace(".NS", "").replace(".BO", "").strip()
    curr_price = get_current_live_price(clean_sym)

    if curr_price is None or curr_price <= 0:
        raise HTTPException(
            status_code=503,
            detail={
                "error": "MARKET_FEED_UNAVAILABLE",
                "symbol": clean_sym,
                "message": f"Real live market price unavailable for '{clean_sym}'. Connect market data provider.",
            }
        )

    entry = req.entry_price or curr_price
    bars = generate_historical_candles(clean_sym, "1h", 60)
    tech = extract_all_features(clean_sym, bars) if bars else {}
    ml_pred = get_ml_prediction(clean_sym)

    atr = tech.get("atr14", curr_price * 0.02)
    is_buy = req.direction.upper() == "BUY"

    # Default stop loss & target if not user-provided
    sl = req.stop_loss or (round(entry - (atr * 1.8), 2) if is_buy else round(entry + (atr * 1.8), 2))
    tp = req.target or (round(entry + (atr * 2.8), 2) if is_buy else round(entry - (atr * 2.8), 2))

    return _calculate_probabilistic_pnl(
        symbol=clean_sym,
        direction=req.direction,
        entry_price=entry,
        current_price=curr_price,
        quantity=req.quantity,
        stop_loss=sl,
        target=tp,
        ml_pred=ml_pred,
        tech=tech,
    )


@ai_router.get("/trade-plan/{symbol}", response_model=AITradePlan)
def get_trade_plan(symbol: str):
    """
    Generate a structured AI trade plan for a given symbol:
    Entry Zone, Stop Loss, Target 1, Target 2, Target 3, Trailing Stop, Buy Conditions, Do Not Buy Conditions.
    """
    from app.services.trade_plan_generator import generate_trade_plan as create_plan

    clean_sym = symbol.upper().replace(".NS", "").replace(".BO", "").strip()
    curr_price = get_current_live_price(clean_sym)

    if curr_price is None or curr_price <= 0:
        raise HTTPException(
            status_code=503,
            detail={
                "error": "MARKET_FEED_UNAVAILABLE",
                "symbol": clean_sym,
                "message": f"Real live price unavailable for '{clean_sym}'. Connect market data provider.",
            }
        )

    try:
        return create_plan(symbol=clean_sym)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@ai_router.post("/generate-trade-plan", response_model=AITradePlan)
def generate_trade_plan_custom(req: GenerateTradePlanRequest):
    """
    Generate an AI Trade Plan with customized parameters:
    account_balance, risk_per_trade_pct, direction, timeframe.
    """
    from app.services.trade_plan_generator import generate_trade_plan as create_plan

    clean_sym = req.symbol.upper().replace(".NS", "").replace(".BO", "").strip()
    curr_price = get_current_live_price(clean_sym)

    if curr_price is None or curr_price <= 0:
        raise HTTPException(
            status_code=503,
            detail={
                "error": "MARKET_FEED_UNAVAILABLE",
                "symbol": clean_sym,
                "message": f"Real live price unavailable for '{clean_sym}'. Connect market data provider.",
            }
        )

    try:
        return create_plan(
            symbol=clean_sym,
            requested_direction=req.direction,
            account_balance=req.account_balance or 100000.0,
            risk_per_trade_pct=req.risk_per_trade_pct or 1.0,
            timeframe=req.timeframe or "1h",
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@ai_router.get("/analyze/{symbol}", response_model=AITradeAnalysisResponse)
def analyze_symbol(symbol: str):
    """
    Comprehensive stock analysis endpoint:
    Returns real live price, structured AI Trade Plan, and Probabilistic P&L Scenarios.
    """
    clean_sym = symbol.upper().replace(".NS", "").replace(".BO", "").strip()
    curr_price = get_current_live_price(clean_sym)

    if curr_price is None or curr_price <= 0:
        raise HTTPException(
            status_code=503,
            detail={
                "error": "MARKET_FEED_UNAVAILABLE",
                "symbol": clean_sym,
                "message": f"Real market quote for '{clean_sym}' not available from active provider.",
                "disclaimer": "AI analysis requires real live market data feed.",
            }
        )

    plan = get_trade_plan(clean_sym)
    pred_req = PnLPredictionRequest(
        symbol=clean_sym,
        direction=plan.direction,
        entry_price=curr_price,
        quantity=10.0,
        stop_loss=plan.stop_loss,
        target=plan.target_1,
        trailing_stop_pct=plan.trailing_stop_pct,
    )
    prediction = predict_trade_pnl(pred_req)

    manager = get_market_data_manager()
    feed_health = manager.get_feed_health()
    data_status = feed_health.get("connection_status", "LIVE_DELAYED")

    mtf_analysis = None
    try:
        mtf_analysis = run_symbol_multi_timeframe_analysis(clean_sym)
    except Exception:
        pass

    return AITradeAnalysisResponse(
        symbol=clean_sym,
        current_price=curr_price,
        currency_symbol="₹",
        data_status=data_status,
        trade_plan=plan,
        prediction=prediction,
        multi_timeframe=mtf_analysis,
        disclaimer="AI predictions are probabilistic and do not guarantee future returns.",
        timestamp=datetime.now(timezone.utc).isoformat(),
    )


@ai_router.get("/multi-timeframe/{symbol}", response_model=MultiTimeframeAnalysisResponse)
def get_ai_multi_timeframe_analysis(symbol: str):
    """
    Return comprehensive 3-tier Multi-Timeframe Technical Analysis (HTF 1d, ITF 1h, LTF 15m)
    with Confluence Score, Trend Alignment, and Probabilistic Safety metrics.
    """
    clean_sym = symbol.upper().replace(".NS", "").replace(".BO", "").strip()
    return run_symbol_multi_timeframe_analysis(clean_sym)


@ai_router.get("/agents/consensus/{symbol}", response_model=MultiAgentConsensusResponse)
def get_multi_agent_consensus(symbol: str):
    """
    Execute full Multi-Agent consensus deliberation (Scout, Risk, Trade, Macro)
    with Risk Veto Authority and probabilistic non-guarantee safety guard.
    """
    from app.services.multi_agent_engine import get_multi_agent_consensus_engine

    clean_sym = symbol.upper().replace(".NS", "").replace(".BO", "").strip()
    curr_price = get_current_live_price(clean_sym)
    if curr_price is None or curr_price <= 0:
        raise HTTPException(
            status_code=503,
            detail={
                "error": "MARKET_FEED_UNAVAILABLE",
                "symbol": clean_sym,
                "message": f"Real live price unavailable for '{clean_sym}'. Connect market data provider.",
            }
        )

    engine = get_multi_agent_consensus_engine()
    try:
        return engine.run_consensus(symbol=clean_sym)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@ai_router.post("/agents/consensus", response_model=MultiAgentConsensusResponse)
def post_multi_agent_consensus(req: GenerateTradePlanRequest):
    """
    Customized Multi-Agent consensus deliberation with user-specified account balance,
    risk parameters, and timeframe.
    """
    from app.services.multi_agent_engine import get_multi_agent_consensus_engine

    clean_sym = req.symbol.upper().replace(".NS", "").replace(".BO", "").strip()
    curr_price = get_current_live_price(clean_sym)
    if curr_price is None or curr_price <= 0:
        raise HTTPException(
            status_code=503,
            detail={
                "error": "MARKET_FEED_UNAVAILABLE",
                "symbol": clean_sym,
                "message": f"Real live price unavailable for '{clean_sym}'. Connect market data provider.",
            }
        )

    engine = get_multi_agent_consensus_engine()
    try:
        return engine.run_consensus(
            symbol=clean_sym,
            account_balance=req.account_balance or 100000.0,
            risk_per_trade_pct=req.risk_per_trade_pct or 1.0,
            timeframe=req.timeframe or "1h",
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

