from datetime import datetime, timezone
from typing import Dict, Any, Optional

INSTRUMENT_TOKENS: Dict[str, int] = {
    "NIFTY 50": 256265,
    "NIFTY BANK": 260105,
    "SENSEX": 265,
    "INDIA VIX": 264969,
    "RELIANCE": 738561,
    "TCS": 2953217,
    "INFY": 408065,
    "HDFCBANK": 341249,
    "ICICIBANK": 1270529,
    "TATAMOTORS": 884737,
    "SBIN": 779521,
    "BHARTIARTL": 2714625,
    "LT": 2939649,
}


def get_instrument_token(symbol: str) -> int:
    clean_sym = symbol.upper().replace(".NS", "").replace(".BO", "")
    return INSTRUMENT_TOKENS.get(clean_sym, 999999)


def calculate_pivot_levels(high: float, low: float, close: float) -> Dict[str, float]:
    """
    Standard Floor Trader Pivot Point & Support/Resistance Levels
    """
    pivot = round((high + low + close) / 3.0, 2)
    r1 = round((2.0 * pivot) - low, 2)
    s1 = round((2.0 * pivot) - high, 2)
    r2 = round(pivot + (high - low), 2)
    s2 = round(pivot - (high - low), 2)
    r3 = round(high + 2.0 * (pivot - low), 2)
    s3 = round(low - 2.0 * (high - pivot), 2)

    return {
        "pivot": pivot,
        "r1": r1,
        "s1": s1,
        "r2": r2,
        "s2": s2,
        "r3": r3,
        "s3": s3,
    }


def normalize_market_feed(raw_data: Dict[str, Any]) -> Dict[str, Any]:
    symbol = raw_data.get("symbol", "").upper().replace(".NS", "").replace(".BO", "")
    token = get_instrument_token(symbol)
    
    price = float(raw_data.get("price", raw_data.get("ltp", 0.0)))
    open_p = float(raw_data.get("open", price))
    high_p = float(raw_data.get("high", price))
    low_p = float(raw_data.get("low", price))
    prev_close = float(raw_data.get("previous_close", price))
    volume = int(raw_data.get("volume", 0))

    change = round(price - prev_close, 2)
    change_pct = round((change / prev_close) * 100.0, 2) if prev_close > 0 else 0.0
    turnover_cr = round((price * volume) / 10_000_000.0, 2)

    pivots = calculate_pivot_levels(high_p, low_p, price)

    return {
        "symbol": symbol,
        "instrument_token": token,
        "exchange": "NSE",
        "market_status": "OPEN",
        "ltp": price,
        "open": open_p,
        "high": high_p,
        "low": low_p,
        "previous_close": prev_close,
        "change": change,
        "change_percent": change_pct,
        "volume": volume,
        "turnover_crores": turnover_cr,
        "support_resistance": pivots,
        "timestamp": raw_data.get("timestamp", datetime.now(timezone.utc).isoformat()),
    }
