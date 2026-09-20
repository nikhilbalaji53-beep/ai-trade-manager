import math
from typing import List, Dict, Any, Tuple
import numpy as np


def compute_sma(prices: List[float], period: int) -> List[float]:
    if not prices:
        return []
    if len(prices) < period:
        return [prices[-1]] * len(prices)

    res = []
    for i in range(len(prices)):
        if i < period - 1:
            res.append(sum(prices[: i + 1]) / (i + 1))
        else:
            res.append(sum(prices[i - period + 1 : i + 1]) / period)
    return res


def compute_ema(prices: List[float], period: int) -> List[float]:
    if not prices:
        return []
    res = [prices[0]]
    multiplier = 2.0 / (period + 1)
    for price in prices[1:]:
        ema_val = (price - res[-1]) * multiplier + res[-1]
        res.append(ema_val)
    return res


def compute_rsi(prices: List[float], period: int = 14) -> float:
    if len(prices) < period + 1:
        return 50.0
    changes = [prices[i] - prices[i - 1] for i in range(1, len(prices))]
    gains = [max(0, c) for c in changes]
    losses = [max(0, -c) for c in changes]

    avg_gain = sum(gains[-period:]) / period
    avg_loss = sum(losses[-period:]) / period

    if avg_loss == 0:
        return 100.0
    rs = avg_gain / avg_loss
    rsi = 100.0 - (100.0 / (1.0 + rs))
    return round(rsi, 2)


def compute_macd(prices: List[float], fast: int = 12, slow: int = 26, signal_period: int = 9) -> Tuple[float, float, float, str]:
    if len(prices) < slow:
        return 0.0, 0.0, 0.0, "NONE"
    ema_fast = compute_ema(prices, fast)
    ema_slow = compute_ema(prices, slow)
    macd_line = [f - s for f, s in zip(ema_fast, ema_slow)]
    signal_line = compute_ema(macd_line, signal_period)
    hist = [m - s for m, s in zip(macd_line, signal_line)]

    curr_macd = round(macd_line[-1], 2)
    curr_sig = round(signal_line[-1], 2)
    curr_hist = round(hist[-1], 2)

    cross = "NONE"
    if len(macd_line) >= 2:
        if macd_line[-2] <= signal_line[-2] and curr_macd > curr_sig:
            cross = "BULLISH_CROSS"
        elif macd_line[-2] >= signal_line[-2] and curr_macd < curr_sig:
            cross = "BEARISH_CROSS"

    return curr_macd, curr_sig, curr_hist, cross


def compute_bollinger_bands(prices: List[float], period: int = 20, num_std: float = 2.0) -> Tuple[float, float, float, float, float]:
    if len(prices) < period:
        p = prices[-1]
        return p * 1.02, p, p * 0.98, 0.5, 4.0
    recent = prices[-period:]
    mean = sum(recent) / period
    std = math.sqrt(sum((x - mean) ** 2 for x in recent) / period)
    upper = mean + num_std * std
    lower = mean - num_std * std
    bandwidth = ((upper - lower) / mean) * 100 if mean != 0 else 0
    pct_b = (prices[-1] - lower) / (upper - lower) if (upper - lower) != 0 else 0.5
    return round(upper, 2), round(mean, 2), round(lower, 2), round(pct_b, 3), round(bandwidth, 2)


def compute_atr(highs: List[float], lows: List[float], closes: List[float], period: int = 14) -> float:
    if len(closes) < 2:
        return 2.5
    tr_list = []
    for i in range(1, len(closes)):
        h = highs[i]
        l = lows[i]
        prev_c = closes[i - 1]
        tr = max(h - l, abs(h - prev_c), abs(l - prev_c))
        tr_list.append(tr)
    if not tr_list:
        return 2.5
    if len(tr_list) < period:
        return round(sum(tr_list) / len(tr_list), 2)
    return round(sum(tr_list[-period:]) / period, 2)


def compute_supertrend(highs: List[float], lows: List[float], closes: List[float], period: int = 10, multiplier: float = 3.0) -> Tuple[float, str]:
    if len(closes) < period + 1:
        return round(closes[-1] * 0.97, 2), "BULLISH"
    atr = compute_atr(highs, lows, closes, period)
    hl2 = [(h + l) / 2.0 for h, l in zip(highs, lows)]
    upper_band = hl2[-1] + multiplier * atr
    lower_band = hl2[-1] - multiplier * atr

    curr_close = closes[-1]
    if curr_close > lower_band:
        return round(lower_band, 2), "BULLISH"
    else:
        return round(upper_band, 2), "BEARISH"


def compute_stochastic(highs: List[float], lows: List[float], closes: List[float], k_period: int = 14, d_period: int = 3) -> Tuple[float, float]:
    if len(closes) < k_period:
        return 50.0, 50.0
    highest_h = max(highs[-k_period:])
    lowest_l = min(lows[-k_period:])
    curr_c = closes[-1]
    if highest_h == lowest_l:
        k_val = 50.0
    else:
        k_val = ((curr_c - lowest_l) / (highest_h - lowest_l)) * 100.0
    d_val = k_val * 0.95 + 2.5  # Smoothed approximation
    return round(k_val, 2), round(d_val, 2)


def compute_vwap(highs: List[float], lows: List[float], closes: List[float], volumes: List[float]) -> float:
    if not closes or not volumes:
        return 100.0
    tp = [(h + l + c) / 3.0 for h, l, c in zip(highs, lows, closes)]
    cum_tp_vol = sum(t * v for t, v in zip(tp, volumes))
    cum_vol = sum(volumes)
    if cum_vol == 0:
        return closes[-1]
    return round(cum_tp_vol / cum_vol, 2)


def compute_obv(closes: List[float], volumes: List[float]) -> float:
    if len(closes) < 2:
        return 0.0
    obv = 0.0
    for i in range(1, len(closes)):
        if closes[i] > closes[i - 1]:
            obv += volumes[i]
        elif closes[i] < closes[i - 1]:
            obv -= volumes[i]
    return round(obv, 0)


def extract_all_features(symbol: str, bars: List[Dict[str, Any]]) -> Dict[str, Any]:
    if not bars:
        return {}
    closes = [b["close"] for b in bars]
    highs = [b["high"] for b in bars]
    lows = [b["low"] for b in bars]
    volumes = [b["volume"] for b in bars]
    current_price = closes[-1]

    sma20_vals = compute_sma(closes, 20)
    sma50_vals = compute_sma(closes, 50)
    sma200_vals = compute_sma(closes, 200)

    ema9_vals = compute_ema(closes, 9)
    ema21_vals = compute_ema(closes, 21)
    ema55_vals = compute_ema(closes, 55)

    rsi = compute_rsi(closes, 14)
    rsi_signal = "OVERBOUGHT" if rsi > 70 else "OVERSOLD" if rsi < 30 else "NEUTRAL"

    macd_line, macd_sig, macd_h, macd_cross = compute_macd(closes)
    bb_up, bb_mid, bb_low, bb_pct_b, bb_bw = compute_bollinger_bands(closes, 20, 2.0)
    atr = compute_atr(highs, lows, closes, 14)
    st_val, st_dir = compute_supertrend(highs, lows, closes)
    stoch_k, stoch_d = compute_stochastic(highs, lows, closes)
    vwap_val = compute_vwap(highs, lows, closes, volumes)
    obv_val = compute_obv(closes, volumes)

    # Volume surge
    recent_vol = volumes[-1]
    avg_vol = sum(volumes[-20:]) / min(len(volumes), 20) if volumes else 1.0
    vol_ratio = round(recent_vol / avg_vol, 2) if avg_vol > 0 else 1.0

    # Determine regime
    if current_price > sma50_vals[-1] and ema21_vals[-1] > sma50_vals[-1] and rsi > 55:
        regime = "TRENDING_BULL"
    elif current_price < sma50_vals[-1] and ema21_vals[-1] < sma50_vals[-1] and rsi < 45:
        regime = "TRENDING_BEAR"
    elif vol_ratio > 2.0 and abs(bb_pct_b - 0.5) > 0.4:
        regime = "BREAKOUT"
    else:
        regime = "CONSOLIDATION"

    # Pivot Point Support & Resistance
    p_high = max(highs[-20:]) if highs else current_price
    p_low = min(lows[-20:]) if lows else current_price
    pivot = round((p_high + p_low + current_price) / 3.0, 2)
    r1 = round((2.0 * pivot) - p_low, 2)
    s1 = round((2.0 * pivot) - p_high, 2)
    r2 = round(pivot + (p_high - p_low), 2)
    s2 = round(pivot - (p_high - p_low), 2)

    # Momentum score (-100 to +100)
    mom_pct = round(((current_price - closes[0]) / closes[0]) * 100.0, 2) if closes else 0.0

    return {
        "symbol": symbol,
        "current_price": current_price,
        "sma20": round(sma20_vals[-1], 2),
        "sma50": round(sma50_vals[-1], 2),
        "sma200": round(sma200_vals[-1], 2),
        "ema9": round(ema9_vals[-1], 2),
        "ema21": round(ema21_vals[-1], 2),
        "ema55": round(ema55_vals[-1], 2),
        "vwap": vwap_val,
        "rsi": rsi,
        "rsi_signal": rsi_signal,
        "macd_line": macd_line,
        "macd_signal": macd_sig,
        "macd_hist": macd_h,
        "macd_cross": macd_cross,
        "bb_upper": bb_up,
        "bb_middle": bb_mid,
        "bb_lower": bb_low,
        "bb_pct_b": bb_pct_b,
        "bb_bandwidth": bb_bw,
        "atr14": atr,
        "supertrend": st_val,
        "supertrend_direction": st_dir,
        "stoch_k": stoch_k,
        "stoch_d": stoch_d,
        "obv": obv_val,
        "volume_surge_ratio": vol_ratio,
        "regime": regime,
        "pivot": pivot,
        "r1": r1,
        "r2": r2,
        "s1": s1,
        "s2": s2,
        "momentum_pct": mom_pct,
    }
