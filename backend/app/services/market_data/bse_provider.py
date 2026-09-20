"""
BSE Live Market Data Provider — TradePilot

Fetches real live quotes for SENSEX and BSE-listed equities via Yahoo Finance.

DATA INTEGRITY:
- data_status = "LIVE_DELAYED" — real Yahoo Finance data, ~15-20 min delayed
- Returns None when no data available (caller must show FEED DISCONNECTED)
- bid/ask quantities are NOT available from Yahoo Finance (no L2 order book)
"""
import logging
import time
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional
import yfinance as yf

from app.services.market_data.base_provider import MarketDataProvider
from app.services.instrument_master import get_instrument_by_symbol, get_all_instruments

logger = logging.getLogger(__name__)

DATA_DELAY_MINUTES = 15


class BSEMarketDataProvider(MarketDataProvider):
    """
    BSE Market Data Provider:
    Fetches real live quotes for SENSEX and BSE-listed equities.

    DATA INTEGRITY CONTRACT:
    - Returns Yahoo Finance data (~15-20 min delayed) with data_status="LIVE_DELAYED"
    - bid_price / ask_price / bid_quantity / ask_quantity are None (L2 not available)
    - Returns None when Yahoo Finance provides no data
    - NEVER returns hardcoded or invented prices
    """

    def __init__(self):
        super().__init__("BSE_YFINANCE")
        self._quote_cache: Dict[str, Dict[str, Any]] = {}
        self._last_fetch_ts: Dict[str, float] = {}
        self._cache_ttl_seconds: float = 30.0

    def connect(self) -> bool:
        self.is_connected = True
        return True

    def disconnect(self):
        self.is_connected = False

    def subscribe(self, symbols: List[str]):
        for s in symbols:
            if s not in self.subscribed_symbols:
                self.subscribed_symbols.append(s)

    def unsubscribe(self, symbols: List[str]):
        for s in symbols:
            if s in self.subscribed_symbols:
                self.subscribed_symbols.remove(s)

    def get_quote(self, symbol: str) -> Optional[Dict[str, Any]]:
        """
        Fetch a real BSE quote from Yahoo Finance.

        Returns quote dict with data_status="LIVE_DELAYED" on success.
        Returns quote dict with data_status="STALE" from cache on failure.
        Returns None when no data available at all.
        """
        clean_sym = symbol.upper().replace(".BO", "").replace("BSE:", "")
        ticker_symbol = "^BSESN" if clean_sym in ["SENSEX", "BSESENSEX"] else f"{clean_sym}.BO"

        now = time.time()
        last_fetch = self._last_fetch_ts.get(clean_sym, 0.0)
        if (now - last_fetch) < self._cache_ttl_seconds and clean_sym in self._quote_cache:
            return self._quote_cache[clean_sym]

        try:
            ticker = yf.Ticker(ticker_symbol)

            # --- Step 1: Try fast_info (raises KeyError outside market hours) ---
            last_price = open_p = high_p = low_p = prev_close = None
            volume = 0
            fast_ok = False
            try:
                fast = ticker.fast_info
                last_price = getattr(fast, "last_price", None) or getattr(fast, "regular_market_price", None)
                if last_price and float(last_price) > 0:
                    open_p     = getattr(fast, "open", last_price) or last_price
                    high_p     = getattr(fast, "day_high", last_price) or last_price
                    low_p      = getattr(fast, "day_low", last_price) or last_price
                    prev_close = getattr(fast, "previous_close", last_price) or last_price
                    volume     = getattr(fast, "last_volume", 0) or 0
                    fast_ok    = True
            except (KeyError, Exception) as fast_err:
                logger.debug(f"BSEMarketDataProvider: fast_info unavailable for '{clean_sym}' ({fast_err}), falling back to history")

            # --- Step 2: Fallback to OHLCV history if fast_info failed ---
            if not fast_ok:
                hist = None
                for period_attempt in ("5d", "1mo", "3mo"):
                    try:
                        hist = ticker.history(period=period_attempt)
                        if not hist.empty:
                            break
                        hist = None
                    except Exception:
                        hist = None

                if hist is not None and not hist.empty:
                    last_price = float(hist["Close"].iloc[-1])
                    open_p     = float(hist["Open"].iloc[-1])
                    high_p     = float(hist["High"].iloc[-1])
                    low_p      = float(hist["Low"].iloc[-1])
                    prev_close = float(hist["Close"].iloc[-2]) if len(hist) > 1 else float(hist["Close"].iloc[-1])
                    volume     = int(hist["Volume"].iloc[-1])
                else:
                    return self._return_stale_cache_or_none(clean_sym)

            last_price = round(float(last_price), 2)
            open_p = round(float(open_p), 2)
            high_p = round(float(high_p), 2)
            low_p = round(float(low_p), 2)
            prev_close = round(float(prev_close), 2)
            change = round(last_price - prev_close, 2)
            change_pct = round((change / prev_close) * 100.0, 2) if prev_close > 0 else 0.0

            inst = get_instrument_by_symbol(clean_sym)
            token = str(inst["instrument_token"]) if inst else "UNKNOWN"

            quote = {
                "symbol":             clean_sym,
                "exchange":           "BSE",
                "instrument_token":   token,
                "timestamp":          datetime.now(timezone.utc).isoformat(),
                "last_price":         last_price,
                "open":               open_p,
                "high":               high_p,
                "low":                low_p,
                "previous_close":     prev_close,
                "change":             change,
                "change_percent":     change_pct,
                "volume":             int(volume),
                # Level 2 order book is NOT available from Yahoo Finance.
                # bid_price / ask_price are None to signal unavailable.
                # bid_quantity / ask_quantity are omitted to prevent misinterpretation.
                "bid_price":          None,
                "ask_price":          None,
                "market_status":      "OPEN",
                "data_source":        "BSE_YFINANCE",
                "data_status":        "LIVE_DELAYED",
                "data_delay_minutes": DATA_DELAY_MINUTES,
                "is_live":            True,
                "note":               "Data sourced from Yahoo Finance. ~15-20 min delay during live market hours.",
            }

            self._quote_cache[clean_sym] = quote
            self._last_fetch_ts[clean_sym] = now
            return quote

        except Exception as e:
            logger.error(f"BSEMarketDataProvider: Error fetching BSE quote for {clean_sym}: {e}")
            return self._return_stale_cache_or_none(clean_sym)

    def _return_stale_cache_or_none(self, clean_sym: str) -> Optional[Dict[str, Any]]:
        """Return stale cache or None — NEVER a fake price."""
        if clean_sym in self._quote_cache:
            cached = self._quote_cache[clean_sym].copy()
            cached["data_status"] = "STALE"
            cached["is_live"] = False
            cached["data_source"] = "BSE_YFINANCE (STALE)"
            logger.warning(f"BSEMarketDataProvider: returning STALE cache for '{clean_sym}'.")
            return cached
        logger.warning(f"BSEMarketDataProvider: no data for '{clean_sym}'. Returning None.")
        return None

    def get_quotes(self, symbols: List[str]) -> List[Dict[str, Any]]:
        results = []
        for s in symbols:
            q = self.get_quote(s)
            if q:
                results.append(q)
        return results

    def get_instruments(self) -> List[Dict[str, Any]]:
        return [inst for inst in get_all_instruments() if inst["exchange"] == "BSE"]

    def get_historical_candles(self, symbol: str, timeframe: str = "1h", count: int = 100) -> List[Dict[str, Any]]:
        """Fetch BSE historical OHLCV from Yahoo Finance. Returns [] if unavailable."""
        clean_sym = symbol.upper().replace(".BO", "")
        ticker_symbol = "^BSESN" if clean_sym in ["SENSEX", "BSESENSEX"] else f"{clean_sym}.BO"

        yf_interval_map = {"1m": "1m", "5m": "5m", "15m": "15m", "1h": "1h", "1d": "1d", "1D": "1d"}
        yf_period_map   = {"1m": "5d", "5m": "5d", "15m": "5d", "1h": "1mo", "1d": "6mo"}

        yf_interval = yf_interval_map.get(timeframe, "1h")
        yf_period   = yf_period_map.get(yf_interval, "1mo")

        try:
            ticker = yf.Ticker(ticker_symbol)
            df = ticker.history(period=yf_period, interval=yf_interval)
            if df.empty:
                return []

            bars = []
            for ts, row in df.iterrows():
                dt = ts.to_pydatetime()
                bars.append({
                    "timestamp": dt.isoformat(),
                    "time":      int(dt.timestamp()),
                    "open":      round(float(row["Open"]),  2),
                    "high":      round(float(row["High"]),  2),
                    "low":       round(float(row["Low"]),   2),
                    "close":     round(float(row["Close"]), 2),
                    "volume":    int(row["Volume"]),
                    "data_source": "BSE_YFINANCE",
                })
            return bars[-count:]
        except Exception as e:
            logger.error(f"BSEMarketDataProvider: historical candles error for '{clean_sym}': {e}")
            return []

    def get_market_status(self) -> Dict[str, Any]:
        """Fetch BSE market session status."""
        from app.services.market_data.market_status_service import get_market_status_service
        return get_market_status_service().get_session_status(is_feed_connected=self.is_connected)
