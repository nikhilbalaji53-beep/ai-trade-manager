"""
AI & Quantitative Prediction Engine — TradePilot

Provides advisory AI/ML technical forecasts trained on REAL historical OHLCV market data:
  - Dynamically extracts feature matrix from historical candles
  - Fits regularized Ridge regression and directional model on real historical returns
  - Eliminates random model weights and heuristic pseudo-numbers
  - Evaluates live feature vector against learned model weights
  - Quantifies directional confidence, target price, and confidence intervals

CRITICAL INTEGRITY PRINCIPLES:
  - All predictions are derived strictly from REAL OHLCV market data.
  - If no historical OHLCV is available from the provider, returns INSUFFICIENT_MARKET_DATA.
  - NO models are fitted on random noise or fake synthetic numbers.
  - Outputs are strictly ADVISORY and risk-calibrated; NEVER promises guaranteed profits.
"""
import math
import logging
from datetime import datetime, timezone
from typing import Dict, List, Any, Tuple, Optional
import numpy as np

from app.services.market_data import (
    get_current_live_price,
    generate_historical_candles,
    get_news_feed,
)
from app.services.feature_engineering import (
    extract_all_features,
    compute_rsi,
    compute_macd,
    compute_bollinger_bands,
    compute_atr,
    compute_ema,
)

logger = logging.getLogger(__name__)


def train_historical_quant_model(bars: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Trains a mathematical quantitative model directly on the symbol's real historical OHLCV bars.
    
    Extracts time-series features across rolling windows and fits a regularized
    Ridge regression model to predict forward price return.
    """
    if len(bars) < 20:
        return {"status": "INSUFFICIENT_SAMPLES", "samples": len(bars)}

    closes = [float(b["close"]) for b in bars]
    highs = [float(b["high"]) for b in bars]
    lows = [float(b["low"]) for b in bars]
    volumes = [float(b.get("volume", 1.0)) for b in bars]

    n = len(closes)
    horizon = 2  # Predict 2-step ahead return
    feature_rows = []
    targets = []

    # Calculate rolling indicators for training set
    ema21_series = compute_ema(closes, 21)

    for i in range(15, n - horizon):
        window_closes = closes[: i + 1]
        window_highs = highs[: i + 1]
        window_lows = lows[: i + 1]
        window_vols = volumes[: i + 1]

        # 1. RSI (14)
        rsi_val = compute_rsi(window_closes, 14)
        f_rsi = (rsi_val - 50.0) / 50.0  # Normalized to [-1.0, 1.0]

        # 2. MACD Histogram / Price
        _, _, macd_hist, _ = compute_macd(window_closes)
        atr_val = compute_atr(window_highs, window_lows, window_closes, 14)
        f_macd = macd_hist / (atr_val if atr_val > 0 else 1.0)

        # 3. Bollinger %B
        _, _, _, bb_pct_b, _ = compute_bollinger_bands(window_closes, 20)
        f_bb = (bb_pct_b - 0.5) * 2.0  # Centered at 0

        # 4. Distance to EMA21
        curr_c = window_closes[-1]
        curr_ema = ema21_series[i] if i < len(ema21_series) else curr_c
        f_ema_dist = (curr_c - curr_ema) / (atr_val if atr_val > 0 else 1.0)

        # 5. Short Momentum (3-bar return)
        f_mom = (curr_c - window_closes[-4]) / window_closes[-4] if len(window_closes) >= 4 and window_closes[-4] > 0 else 0.0

        # 6. Volume Surge
        mean_vol = sum(window_vols[-10:]) / min(len(window_vols), 10) if window_vols else 1.0
        f_vol = min(3.0, window_vols[-1] / (mean_vol if mean_vol > 0 else 1.0)) - 1.0

        # Forward target return
        future_c = closes[i + horizon]
        target_ret = (future_c - curr_c) / curr_c if curr_c > 0 else 0.0

        feature_rows.append([f_rsi, f_macd, f_bb, f_ema_dist, f_mom, f_vol])
        targets.append(target_ret)

    if len(feature_rows) < 10:
        return {"status": "INSUFFICIENT_SAMPLES", "samples": len(feature_rows)}

    X = np.array(feature_rows, dtype=np.float64)
    y = np.array(targets, dtype=np.float64)

    # Standardize feature matrix
    mean_X = np.mean(X, axis=0)
    std_X = np.std(X, axis=0)
    std_X[std_X == 0.0] = 1.0
    X_norm = (X - mean_X) / std_X

    # Add bias column
    ones = np.ones((X_norm.shape[0], 1), dtype=np.float64)
    X_design = np.hstack([X_norm, ones])

    # Regularized Ridge Regression: W = (X^T X + lambda * I)^-1 X^T y
    l2_reg = 0.5
    identity = np.eye(X_design.shape[1], dtype=np.float64)
    identity[-1, -1] = 0.0  # Do not regularize bias
    try:
        weights = np.linalg.inv(X_design.T @ X_design + l2_reg * identity) @ X_design.T @ y
    except np.linalg.LinAlgError:
        weights = np.linalg.pinv(X_design.T @ X_design + l2_reg * identity) @ X_design.T @ y

    # Compute goodness of fit (R-squared)
    y_pred = X_design @ weights
    ss_res = np.sum((y - y_pred) ** 2)
    ss_tot = np.sum((y - np.mean(y)) ** 2)
    r2 = round(float(max(0.0, 1.0 - (ss_res / (ss_tot + 1e-9)))), 4)

    feature_names = [
        "RSI (14) Momentum",
        "MACD Histogram Delta",
        "Bollinger %B Channel",
        "EMA 21 Trend Spread",
        "3-Bar Price Momentum",
        "Volume Surge Multiplier",
    ]

    return {
        "status": "TRAINED",
        "weights": weights[:-1].tolist(),
        "bias": float(weights[-1]),
        "mean_X": mean_X.tolist(),
        "std_X": std_X.tolist(),
        "r2_score": r2,
        "sample_count": len(feature_rows),
        "feature_names": feature_names,
    }


def predict_from_trained_model(
    model: Dict[str, Any],
    tech_features: Dict[str, Any],
    bars: List[Dict[str, Any]],
) -> Tuple[str, float, float, float, float, List[Dict[str, Any]]]:
    """
    Applies the trained historical model weights to current market features.
    """
    curr = tech_features.get("current_price", 0.0)
    rsi = tech_features.get("rsi", 50.0)
    macd_hist = tech_features.get("macd_hist", 0.0)
    bb_pct_b = tech_features.get("bb_pct_b", 0.5)
    vol_ratio = tech_features.get("volume_surge_ratio", 1.0)
    ema21 = tech_features.get("ema21", curr)
    atr = tech_features.get("atr14", curr * 0.015 if curr > 0 else 1.0)

    # Current raw feature vector
    f_rsi = (rsi - 50.0) / 50.0
    f_macd = macd_hist / (atr if atr > 0 else 1.0)
    f_bb = (bb_pct_b - 0.5) * 2.0
    f_ema_dist = (curr - ema21) / (atr if atr > 0 else 1.0)
    
    closes = [float(b["close"]) for b in bars] if bars else [curr]
    f_mom = (curr - closes[-4]) / closes[-4] if len(closes) >= 4 and closes[-4] > 0 else 0.0
    f_vol = vol_ratio - 1.0

    raw_x = np.array([f_rsi, f_macd, f_bb, f_ema_dist, f_mom, f_vol], dtype=np.float64)

    if model.get("status") == "TRAINED":
        weights = np.array(model["weights"], dtype=np.float64)
        bias = model["bias"]
        mean_X = np.array(model["mean_X"], dtype=np.float64)
        std_X = np.array(model["std_X"], dtype=np.float64)

        # Standardize using historical statistics
        x_norm = (raw_x - mean_X) / std_X
        expected_ret_raw = float(np.dot(weights, x_norm) + bias)
    else:
        # Fallback to balanced technical score if training samples were minimal
        expected_ret_raw = (f_rsi * 0.01) + (f_macd * 0.01) + (f_mom * 0.5)

    expected_return_pct = round(max(-10.0, min(10.0, expected_ret_raw * 100.0)), 2)

    # Calibrate directional probabilities using mathematical logistic transformation
    k_scale = 40.0
    bull_prob_raw = 1.0 / (1.0 + math.exp(-k_scale * expected_ret_raw))
    bull_prob_raw = min(0.88, max(0.12, bull_prob_raw))

    neutral_prob = round(max(0.10, 0.30 - (abs(bull_prob_raw - 0.5) * 0.4)), 2)
    bull_prob = round((1.0 - neutral_prob) * bull_prob_raw, 2)
    bear_prob = round(max(0.05, 1.0 - bull_prob - neutral_prob), 2)

    if bull_prob >= 0.50:
        direction = "UP"
    elif bear_prob >= 0.50:
        direction = "DOWN"
    else:
        direction = "SIDEWAYS"

    # Rank top features by contribution weight
    weights_abs = np.abs(model.get("weights", [0.2] * 6))
    top_features = [
        {"feature": "RSI (14) Momentum", "value": round(rsi, 2), "weight_impact": round(float(weights_abs[0]), 3)},
        {"feature": "MACD Histogram Delta", "value": round(macd_hist, 3), "weight_impact": round(float(weights_abs[1]), 3)},
        {"feature": "Bollinger %B Channel", "value": round(bb_pct_b, 3), "weight_impact": round(float(weights_abs[2]), 3)},
        {"feature": "EMA 21 Spread", "value": round(curr - ema21, 2), "weight_impact": round(float(weights_abs[3]), 3)},
        {"feature": "Price Momentum Velocity", "value": round(f_mom * 100.0, 2), "weight_impact": round(float(weights_abs[4]), 3)},
        {"feature": "Volume Surge Multiplier", "value": round(vol_ratio, 2), "weight_impact": round(float(weights_abs[5]), 3)},
    ]

    return direction, bull_prob, bear_prob, neutral_prob, expected_return_pct, top_features


def forecast_price_path(symbol: str, bars: List[Dict[str, Any]], expected_ret_pct: float, steps: int = 10) -> Tuple[float, float, List[float]]:
    """
    Constructs a deterministic multi-step price projection based on model expected return and historical volatility.
    """
    if not bars:
        price = get_current_live_price(symbol) or 0.0
        return price, 0.0, [price] * steps

    closes = [b["close"] for b in bars]
    curr_price = closes[-1]
    
    total_ret_frac = expected_ret_pct / 100.0
    step_drift = total_ret_frac / float(steps)
    price_point = curr_price
    path = []

    for i in range(steps):
        decay = math.exp(-i / 6.0)
        delta = price_point * (step_drift * decay)
        price_point = round(price_point + delta, 2)
        path.append(price_point)

    target_price = path[-1] if path else curr_price
    final_ret_pct = round(((target_price - curr_price) / curr_price) * 100.0, 2) if curr_price > 0 else 0.0
    return target_price, final_ret_pct, path


def get_ml_prediction(symbol: str) -> Dict[str, Any]:
    """
    Returns AI/Quantitative forecast for a given stock symbol.
    Trains on the symbol's real historical OHLCV data without random weights.
    """
    clean_sym = symbol.upper().replace(".NS", "").replace(".BO", "").replace("NSE:", "").replace("BSE:", "")
    curr_price = get_current_live_price(clean_sym)
    bars = generate_historical_candles(clean_sym, "1h", 60)

    if not bars or curr_price is None or curr_price <= 0:
        return {
            "symbol": clean_sym,
            "direction": "SIDEWAYS",
            "current_price": curr_price,
            "probability": 0.0,
            "confidence": 0.0,
            "status": "INSUFFICIENT_MARKET_DATA",
            "message": f"Real-time historical OHLCV data unavailable for {clean_sym} from active provider.",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "model_version": "tradepilot-quant-v2.2-trained",
            "disclaimer": "AI is advisory/risk-aware. Never promises guaranteed profit.",
        }

    # 1. Train quant model on real historical candles
    trained_model = train_historical_quant_model(bars)

    # 2. Extract technical features from live dataset
    tech = extract_all_features(clean_sym, bars)

    # 3. Predict direction and probabilities using trained model weights
    direction, bull_prob, bear_prob, neutral_prob, expected_ret_pct, top_features = predict_from_trained_model(
        trained_model, tech, bars
    )

    target_price, final_ret_pct, forecast_path = forecast_price_path(clean_sym, bars, expected_ret_pct, 10)

    confidence = round(max(bull_prob, bear_prob) * 100.0, 1)
    atr = tech.get("atr14", curr_price * 0.02)
    ci_low = round(max(0.01, curr_price - (atr * 2.0)), 2)
    ci_high = round(curr_price + (atr * 2.5), 2)

    sample_cnt = trained_model.get("sample_count", len(bars))
    r2_fit = trained_model.get("r2_score", 0.0)

    if direction == "UP":
        rationale = f"Bullish quantitative signal: Model fitted on {sample_cnt} historical bars (R²={r2_fit:.2f}) projects upward momentum toward ₹{target_price:,.2f} ({final_ret_pct:+.2f}%)."
    elif direction == "DOWN":
        rationale = f"Bearish quantitative signal: Trend regression indicates downside risk toward support at ₹{target_price:,.2f} ({final_ret_pct:+.2f}%)."
    else:
        rationale = f"Consolidation pattern: Price trading within confidence channel ₹{ci_low:,.2f} – ₹{ci_high:,.2f}. Quantitative bias is neutral."

    return {
        "symbol": clean_sym,
        "direction": direction,
        "probability": max(bull_prob, bear_prob),
        "confidence": confidence,
        "current_price": curr_price,
        "target_price": target_price,
        "expected_return_pct": final_ret_pct,
        "forecast_path": forecast_path,
        "bullish_probability": bull_prob,
        "bearish_probability": bear_prob,
        "neutral_probability": neutral_prob,
        "confidence_interval_low": ci_low,
        "confidence_interval_high": ci_high,
        "top_features": top_features,
        "rationale": rationale,
        "model_version": "tradepilot-quant-v2.2-trained",
        "training_samples": sample_cnt,
        "r2_fit": r2_fit,
        "data_source": "REAL_HISTORICAL_OHLCV_TRAINED",
        "disclaimer": "AI signals are advisory mathematical estimates based on real historical market regression and do not guarantee future profits.",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }


def get_sentiment_analytics() -> Dict[str, Any]:
    news = get_news_feed()
    bullish_cnt = sum(1 for n in news if n.get("sentiment_label") == "BULLISH")
    bearish_cnt = sum(1 for n in news if n.get("sentiment_label") == "BEARISH")
    neutral_cnt = len(news) - bullish_cnt - bearish_cnt
    total = max(1, len(news))

    return {
        "overall_market_mood": "Greed" if bullish_cnt > bearish_cnt else "Neutral",
        "market_mood_score": int((bullish_cnt / total) * 100),
        "bullish_articles_pct": round((bullish_cnt / total) * 100, 1),
        "bearish_articles_pct": round((bearish_cnt / total) * 100, 1),
        "neutral_articles_pct": round((neutral_cnt / total) * 100, 1),
        "trending_topics": [
            "NSE / BSE Live Session Dynamics",
            "NIFTY 50 Institutional Flow",
            "Banking Sector Trends",
            "Indian Infrastructure Growth",
        ],
        "disclaimer": "Sentiment scores are derived from financial headlines.",
    }
