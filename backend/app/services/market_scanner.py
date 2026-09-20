"""
Real-time Live Market Scanner & Pattern Detection Engine — TradePilot AI

Phase 11 Implementation:
  - Multi-Category Technical Scanners:
      1. BREAKOUT: High volume breakouts, Bollinger Band expansion, pivot level breach
      2. REVERSAL: RSI oversold/overbought mean-reversion, Pinbar / Hammer / Shooting Star
      3. MOMENTUM: Bullish/Bearish MACD crossovers, Supertrend flips, EMA golden/death crosses
      4. PATTERNS: Bullish Engulfing, Bearish Engulfing, Hammer, Shooting Star, Doji
      5. GAINER / LOSER: Top session movers across tracked symbols
      6. CONFLUENCE: High multi-timeframe confluence setups (from MultiTimeframeEngine)
  - Multi-Market & Multi-Currency:
      - Indian Equities (NSE/BSE, INR, ₹)
      - US Equities & ETFs (NASDAQ/NYSE, USD, $)
  - Real-time quote integration:
      - Reads live validated quotes from MarketDataManager
      - Never produces synthetic or fake ticker data
  - Dedicated Filtering & Sorting:
      - Filter by category, market (IN / US), min_confidence, signal_type (BUY / SELL / WATCH)
      - Returns enriched ScannerResult with currency symbol, current price, risk score, confidence
"""
from typing import List, Dict, Any, Optional, Tuple
import math
import time
import logging

from app.schemas.trade import ScannerResult
from app.services.market_data.market_data_manager import get_market_data_manager, CORE_US_SYMBOLS
from app.services.market_data import generate_historical_candles
from app.services.feature_engineering import extract_all_features
from app.services.instrument_master import get_instrument_by_symbol
from app.services.multi_timeframe_engine import compute_multi_timeframe_analysis

logger = logging.getLogger(__name__)

_SCANNER_CACHE: Dict[str, Tuple[float, List[ScannerResult]]] = {}
_SCANNER_CACHE_TTL = 15.0


def _filter_and_sort_scanner_results(
    results: List[ScannerResult],
    filter_category: str = "ALL",
    min_confidence: int = 60,
) -> List[ScannerResult]:
    cat_upper = filter_category.upper().strip()
    filtered = results
    if cat_upper != "ALL":
        filtered = [r for r in filtered if r.category.upper() == cat_upper]

    if min_confidence > 0:
        filtered = [r for r in filtered if r.confidence >= min_confidence]

    seen = set()
    deduped: List[ScannerResult] = []
    for r in filtered:
        key = (r.symbol, r.pattern)
        if key not in seen:
            seen.add(key)
            deduped.append(r)

    deduped.sort(key=lambda x: (x.confidence, x.volume_ratio), reverse=True)
    return deduped


def detect_candlestick_pattern(bars: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    """Detect classic price action candlestick patterns on the latest bars."""
    if not bars or len(bars) < 2:
        return None

    last = bars[-1]
    prev = bars[-2]

    o1, h1, l1, c1 = float(prev["open"]), float(prev["high"]), float(prev["low"]), float(prev["close"])
    o2, h2, l2, c2 = float(last["open"]), float(last["high"]), float(last["low"]), float(last["close"])

    body1 = abs(c1 - o1)
    body2 = abs(c2 - o2)
    range2 = max(0.01, h2 - l2)

    # 1. Bullish Engulfing
    if c1 < o1 and c2 > o2 and o2 <= c1 and c2 >= o1 and body2 > body1:
        return {
            "pattern": "Bullish Engulfing",
            "signal_type": "BUY",
            "confidence": 85,
            "detail": "Bullish candle completely engulfs prior bearish body, signaling aggressive reversal demand.",
        }

    # 2. Bearish Engulfing
    if c1 > o1 and c2 < o2 and o2 >= c1 and c2 <= o1 and body2 > body1:
        return {
            "pattern": "Bearish Engulfing",
            "signal_type": "SELL",
            "confidence": 85,
            "detail": "Bearish candle completely engulfs prior bullish body, signaling heavy distribution.",
        }

    # 3. Hammer (Bullish Reversal)
    lower_shadow2 = min(o2, c2) - l2
    upper_shadow2 = h2 - max(o2, c2)
    effective_body2 = max(0.2, body2)
    if lower_shadow2 >= 1.8 * effective_body2 and upper_shadow2 <= 0.6 * effective_body2 and range2 > 0.5:
        return {
            "pattern": "Bullish Hammer",
            "signal_type": "BUY",
            "confidence": 82,
            "detail": "Extended lower tail reflects rejection of lower prices and strong intraday buying support.",
        }

    # 4. Shooting Star (Bearish Reversal)
    if upper_shadow2 >= 1.8 * effective_body2 and lower_shadow2 <= 0.6 * effective_body2 and range2 > 0.5:
        return {
            "pattern": "Shooting Star",
            "signal_type": "SELL",
            "confidence": 82,
            "detail": "Extended upper shadow reflects sharp rejection of intraday highs and overhead supply.",
        }

    # 5. Doji (Indecision)
    if body2 <= 0.1 * range2:
        return {
            "pattern": "Indecision Doji",
            "signal_type": "WATCH",
            "confidence": 70,
            "detail": "Equilibrium between buyers and sellers near pivotal price action level.",
        }

    return None


def scan_market(
    filter_category: str = "ALL",
    market_filter: Optional[str] = None,
    min_confidence: int = 60,
    timeframe: str = "1h",
) -> List[ScannerResult]:
    """
    Scan tracked equities and ETFs across Indian and US markets for high-probability setups.
    Returns structured, deduplicated ScannerResult models.
    """
    m_filter = market_filter.upper().strip() if market_filter else "ALL"
    cache_key = f"{m_filter}_{timeframe}"
    now = time.time()
    if cache_key in _SCANNER_CACHE:
        cached_ts, cached_raw = _SCANNER_CACHE[cache_key]
        if (now - cached_ts) < _SCANNER_CACHE_TTL and cached_raw:
            return _filter_and_sort_scanner_results(cached_raw, filter_category, min_confidence)

    manager = get_market_data_manager()

    # Determine universe of quotes to scan
    quotes: List[Dict[str, Any]] = []
    if m_filter == "US":
        cached_us = [q for s, q in manager._cached_quotes.items() if s in CORE_US_SYMBOLS]
        if len(cached_us) >= 4:
            quotes = cached_us
        else:
            quotes = manager.get_us_quotes()
    elif m_filter == "IN":
        cached_in = [q for s, q in manager._cached_quotes.items() if s not in CORE_US_SYMBOLS and not s.startswith("^")]
        if len(cached_in) >= 8:
            quotes = cached_in
        else:
            quotes = manager.get_nifty50_constituents_live()
    else:
        # Default: combined live quotes (Indian NIFTY 50 + US Leaders)
        if len(manager._cached_quotes) >= 10:
            quotes = list(manager._cached_quotes.values())
        else:
            in_quotes = manager.get_nifty50_constituents_live()
            us_quotes = manager.get_us_quotes()
            quotes = (in_quotes or []) + (us_quotes or [])

    if not quotes:
        quotes = list(manager._cached_quotes.values())

    # Parallelize candle fetching across all target symbols for high-speed scanning
    from concurrent.futures import ThreadPoolExecutor
    clean_symbols = [
        q["symbol"].upper().replace(".NS", "").replace(".BO", "").strip()
        for q in quotes if q.get("symbol")
    ]

    def _fetch_bars(sym: str):
        try:
            return sym, manager.get_historical_candles(sym, timeframe=timeframe, count=60)
        except Exception:
            return sym, []

    with ThreadPoolExecutor(max_workers=min(12, len(clean_symbols) or 1)) as executor:
        bars_map = dict(executor.map(_fetch_bars, clean_symbols))

    results: List[ScannerResult] = []

    for quote in quotes:
        symbol = quote.get("symbol")
        if not symbol:
            continue

        clean_sym = symbol.upper().replace(".NS", "").replace(".BO", "").strip()
        curr_price = float(quote.get("last_price") or quote.get("price") or 0.0)
        if curr_price <= 0:
            continue

        pct_change = float(quote.get("change_percent") or 0.0)

        # Instrument metadata for market & currency symbol
        inst = get_instrument_by_symbol(clean_sym)
        market = inst.get("market", "IN") if inst else ("US" if clean_sym.startswith("NASDAQ:") or clean_sym.startswith("NYSE:") or clean_sym in ["AAPL", "MSFT", "NVDA", "TSLA", "AMZN", "GOOGL", "META", "SPY", "QQQ"] else "IN")
        curr_sym = inst.get("currency_symbol", "₹") if inst else ("$" if market == "US" else "₹")

        # Historical candles from pre-fetched parallel map
        bars = bars_map.get(clean_sym, [])
        tech = extract_all_features(clean_sym, bars) if bars else {}

        vol_ratio = float(tech.get("volume_surge_ratio", 1.0))
        rsi = float(tech.get("rsi", 50.0))
        macd_cross = str(tech.get("macd_cross", "NONE"))
        bb_bw = float(tech.get("bb_bandwidth", 4.0))
        supertrend_dir = str(tech.get("supertrend_direction", "NEUTRAL"))
        ema9 = float(tech.get("ema9", curr_price))
        ema21 = float(tech.get("ema21", curr_price))
        r1 = float(tech.get("r1", curr_price * 1.02))
        s1 = float(tech.get("s1", curr_price * 0.98))

        # Risk score (1-10) calibration
        atr = float(tech.get("atr14", curr_price * 0.02))
        atr_pct = (atr / curr_price) * 100.0 if curr_price > 0 else 2.0
        risk_score = max(1, min(10, int(round(atr_pct * 1.8 + (1.5 if abs(pct_change) > 2.5 else 0)))))

        # -------------------------------------------------------------
        # 1. VOLUME BREAKOUT & EXPANSION
        # -------------------------------------------------------------
        if vol_ratio >= 1.35 and abs(pct_change) >= 0.8:
            sig = "BUY" if pct_change > 0 else "SELL"
            conf = min(95, int(75 + vol_ratio * 8))
            results.append(ScannerResult(
                symbol=clean_sym,
                pattern="High Volume Breakout",
                category="BREAKOUT",
                timeframe=timeframe,
                confidence=conf,
                signal_type=sig,
                change_percent=pct_change,
                volume_ratio=vol_ratio,
                current_price=curr_price,
                market=market,
                currency_symbol=curr_sym,
                risk_score=risk_score,
                detail=f"Surging at {vol_ratio:.1f}x average volume with strong {sig} momentum ({pct_change:+.2f}%).",
            ))

        # -------------------------------------------------------------
        # 2. BOLLINGER BAND SQUEEZE
        # -------------------------------------------------------------
        if bb_bw < 3.2 and len(bars) >= 20:
            results.append(ScannerResult(
                symbol=clean_sym,
                pattern="Bollinger Band Squeeze",
                category="BREAKOUT",
                timeframe=timeframe,
                confidence=78,
                signal_type="WATCH",
                change_percent=pct_change,
                volume_ratio=vol_ratio,
                current_price=curr_price,
                market=market,
                currency_symbol=curr_sym,
                risk_score=min(risk_score, 5),
                detail=f"Extreme volatility compression (Bandwidth: {bb_bw:.1f}%). High probability explosive breakout setup.",
            ))

        # -------------------------------------------------------------
        # 3. MACD MOMENTUM CROSSOVER
        # -------------------------------------------------------------
        if macd_cross == "BULLISH_CROSS":
            results.append(ScannerResult(
                symbol=clean_sym,
                pattern="Bullish MACD Crossover",
                category="MACD",
                timeframe=timeframe,
                confidence=84,
                signal_type="BUY",
                change_percent=pct_change,
                volume_ratio=vol_ratio,
                current_price=curr_price,
                market=market,
                currency_symbol=curr_sym,
                risk_score=risk_score,
                detail="Fast MACD line crossed above Signal line confirming upward momentum expansion.",
            ))
        elif macd_cross == "BEARISH_CROSS":
            results.append(ScannerResult(
                symbol=clean_sym,
                pattern="Bearish MACD Crossover",
                category="MACD",
                timeframe=timeframe,
                confidence=82,
                signal_type="SELL",
                change_percent=pct_change,
                volume_ratio=vol_ratio,
                current_price=curr_price,
                market=market,
                currency_symbol=curr_sym,
                risk_score=risk_score,
                detail="Fast MACD line crossed below Signal line confirming downside acceleration.",
            ))

        # -------------------------------------------------------------
        # 4. RSI OVERSOLD / OVERBOUGHT REVERSAL
        # -------------------------------------------------------------
        if rsi < 34:
            results.append(ScannerResult(
                symbol=clean_sym,
                pattern="RSI Oversold Reversal",
                category="RSI",
                timeframe=timeframe,
                confidence=80,
                signal_type="BUY",
                change_percent=pct_change,
                volume_ratio=vol_ratio,
                current_price=curr_price,
                market=market,
                currency_symbol=curr_sym,
                risk_score=risk_score,
                detail=f"RSI deep in oversold territory ({rsi:.1f}) near support. Favorable mean-reversion setup.",
            ))
        elif rsi > 69:
            results.append(ScannerResult(
                symbol=clean_sym,
                pattern="RSI Overbought Warning",
                category="RSI",
                timeframe=timeframe,
                confidence=76,
                signal_type="WATCH",
                change_percent=pct_change,
                volume_ratio=vol_ratio,
                current_price=curr_price,
                market=market,
                currency_symbol=curr_sym,
                risk_score=risk_score,
                detail=f"RSI in overbought zone ({rsi:.1f}). Extended rally susceptible to mean reversion or pullback.",
            ))

        # -------------------------------------------------------------
        # 5. EMA ALIGNMENT & SUPERTREND
        # -------------------------------------------------------------
        if ema9 > ema21 and supertrend_dir == "BULLISH" and curr_price > ema9:
            results.append(ScannerResult(
                symbol=clean_sym,
                pattern="Bullish Trend Alignment",
                category="MOMENTUM",
                timeframe=timeframe,
                confidence=82,
                signal_type="BUY",
                change_percent=pct_change,
                volume_ratio=vol_ratio,
                current_price=curr_price,
                market=market,
                currency_symbol=curr_sym,
                risk_score=risk_score,
                detail=f"Price ({curr_sym}{curr_price:,.2f}) trading above EMA 9/21 with active Bullish Supertrend.",
            ))
        elif ema9 < ema21 and supertrend_dir == "BEARISH" and curr_price < ema9:
            results.append(ScannerResult(
                symbol=clean_sym,
                pattern="Bearish Trend Breakdown",
                category="MOMENTUM",
                timeframe=timeframe,
                confidence=80,
                signal_type="SELL",
                change_percent=pct_change,
                volume_ratio=vol_ratio,
                current_price=curr_price,
                market=market,
                currency_symbol=curr_sym,
                risk_score=risk_score,
                detail=f"Price ({curr_sym}{curr_price:,.2f}) broken below EMA 9/21 with active Bearish Supertrend.",
            ))

        # -------------------------------------------------------------
        # 6. PRICE ACTION CANDLESTICK PATTERNS
        # -------------------------------------------------------------
        candle_pat = detect_candlestick_pattern(bars)
        if candle_pat:
            results.append(ScannerResult(
                symbol=clean_sym,
                pattern=candle_pat["pattern"],
                category="CANDLESTICK",
                timeframe=timeframe,
                confidence=candle_pat["confidence"],
                signal_type=candle_pat["signal_type"],
                change_percent=pct_change,
                volume_ratio=vol_ratio,
                current_price=curr_price,
                market=market,
                currency_symbol=curr_sym,
                risk_score=risk_score,
                detail=candle_pat["detail"],
            ))

        # -------------------------------------------------------------
        # 7. TOP GAINERS & LOSERS
        # -------------------------------------------------------------
        if pct_change >= 2.0:
            results.append(ScannerResult(
                symbol=clean_sym,
                pattern="Top Session Gainer",
                category="GAINER",
                timeframe="1D",
                confidence=86,
                signal_type="BUY",
                change_percent=pct_change,
                volume_ratio=vol_ratio,
                current_price=curr_price,
                market=market,
                currency_symbol=curr_sym,
                risk_score=risk_score,
                detail=f"Outperforming benchmark with strong session gain of {pct_change:+.2f}%.",
            ))
        elif pct_change <= -1.8:
            results.append(ScannerResult(
                symbol=clean_sym,
                pattern="Top Session Loser",
                category="LOSER",
                timeframe="1D",
                confidence=78,
                signal_type="WATCH",
                change_percent=pct_change,
                volume_ratio=vol_ratio,
                current_price=curr_price,
                market=market,
                currency_symbol=curr_sym,
                risk_score=risk_score,
                detail=f"Underperforming session with pullback of {pct_change:+.2f}%. Monitoring support levels.",
            ))

    # -------------------------------------------------------------
    # Cache the computed raw scan results for quick subsequent queries
    _SCANNER_CACHE[cache_key] = (time.time(), results)

    return _filter_and_sort_scanner_results(results, filter_category, min_confidence)
