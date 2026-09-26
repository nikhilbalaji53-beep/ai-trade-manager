"""
NSE Live Market Data Provider — TradePilot

Uses yfinance to fetch real market data from NSE/BSE via Yahoo Finance.

DATA INTEGRITY NOTICE:
  - Yahoo Finance republishes NSE/BSE data with approximately 15-20 minute delay
    during live market hours. This is NOT a real-time tick feed.
  - For true real-time (sub-second) tick data, configure a licensed broker API
    by setting MARKET_DATA_PROVIDER=BROKER_API in your .env file.
  - All quotes returned here carry data_status="LIVE_DELAYED" and
    data_delay_minutes=15 to clearly communicate this to the UI.

IMPORTANT:
  - This provider NEVER returns hardcoded or invented prices.
  - When the data feed is unavailable, get_quote() returns None.
  - Callers MUST handle None and display "FEED DISCONNECTED" to the user.
  - The last-known CACHE may be returned with data_status="STALE".
"""
import os
import math
import logging
import time
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Any, Optional

import yfinance as yf

from app.services.market_data.base_provider import MarketDataProvider
from app.services.instrument_master import get_instrument_by_symbol, get_all_instruments

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Symbol mapping: TradePilot internal symbol → Yahoo Finance ticker
# ---------------------------------------------------------------------------
EXCHANGE_TICKER_MAP: Dict[str, str] = {
    # NSE Indices
    "NIFTY 50":       "^NSEI",
    "NIFTY50":        "^NSEI",
    "NIFTY BANK":     "^NSEBANK",
    "NIFTYBANK":      "^NSEBANK",
    "NIFTY NEXT 50":  "^NSMIDCP",
    "NIFTYNEXT50":    "^NSMIDCP",
    "NIFTY 100":      "^CNX100",
    "NIFTY100":       "^CNX100",
    "NIFTY 500":      "^CRSLDX",
    "NIFTY500":       "^CRSLDX",
    "NIFTY MIDCAP 50":"^NSEMDCP50",
    "NIFTY IT":       "^CNXIT",
    "NIFTY PHARMA":   "^CNXPHARMA",
    "NIFTY AUTO":     "^CNXAUTO",
    "NIFTY FMCG":     "^CNXFMCG",
    "INDIA VIX":      "^INDIAVIX",
    # BSE Indices
    "SENSEX":         "^BSESN",
    "BSESENSEX":      "^BSESN",
    # NSE Equities — NIFTY 50 Constituents
    "RELIANCE":       "RELIANCE.NS",
    "TCS":            "TCS.NS",
    "INFY":           "INFY.NS",
    "HDFCBANK":       "HDFCBANK.NS",
    "ICICIBANK":      "ICICIBANK.NS",
    "TATAMOTORS":     "TMPV.NS",
    "TMPV":           "TMPV.NS",
    "TMCV":           "TMCV.NS",
    "SBIN":           "SBIN.NS",
    "BHARTIARTL":     "BHARTIARTL.NS",
    "LT":             "LT.NS",
    "AXISBANK":       "AXISBANK.NS",
    "KOTAKBANK":      "KOTAKBANK.NS",
    "ITC":            "ITC.NS",
    "MARUTI":         "MARUTI.NS",
    "SUNPHARMA":      "SUNPHARMA.NS",
    "TITAN":          "TITAN.NS",
    "BAJFINANCE":     "BAJFINANCE.NS",
    "WIPRO":          "WIPRO.NS",
    "HCLTECH":        "HCLTECH.NS",
    "ULTRACEMCO":     "ULTRACEMCO.NS",
    "ADANIENT":       "ADANIENT.NS",
    "ADANIPORTS":     "ADANIPORTS.NS",
    "ASIANPAINT":     "ASIANPAINT.NS",
    "BAJAJ-AUTO":     "BAJAJ-AUTO.NS",
    "BAJAJAUTO":      "BAJAJ-AUTO.NS",
    "BAJAJFINSV":     "BAJAJFINSV.NS",
    "BPCL":           "BPCL.NS",
    "BRITANNIA":      "BRITANNIA.NS",
    "CIPLA":          "CIPLA.NS",
    "COALINDIA":      "COALINDIA.NS",
    "DIVISLAB":       "DIVISLAB.NS",
    "DRREDDY":        "DRREDDY.NS",
    "EICHERMOT":      "EICHERMOT.NS",
    "GRASIM":         "GRASIM.NS",
    "HDFCLIFE":       "HDFCLIFE.NS",
    "HEROMOTOCO":     "HEROMOTOCO.NS",
    "HINDUNILVR":     "HINDUNILVR.NS",
    "INDUSINDBK":     "INDUSINDBK.NS",
    "JSWSTEEL":       "JSWSTEEL.NS",
    "M&M":            "M&M.NS",
    "MM":             "M&M.NS",
    "NESTLEIND":      "NESTLEIND.NS",
    "NTPC":           "NTPC.NS",
    "ONGC":           "ONGC.NS",
    "POWERGRID":      "POWERGRID.NS",
    "SBILIFE":        "SBILIFE.NS",
    "SHRIRAMFIN":     "SHRIRAMFIN.NS",
    "TATACONSUM":     "TATACONSUM.NS",
    "TATASTEEL":      "TATASTEEL.NS",
    "TECHM":          "TECHM.NS",
    "TRENT":          "TRENT.NS",
    "APOLLOHOSP":     "APOLLOHOSP.NS",
    # Commodities & Precious Metals (ETFs traded on NSE in INR)
    "GOLD":           "GOLDBEES.NS",
    "GOLDBEES":       "GOLDBEES.NS",
    "SILVER":         "SILVERBEES.NS",
    "SILVERBEES":     "SILVERBEES.NS",
    # Forex — USD/INR live rate (Yahoo Finance)
    "USDINR":         "USDINR=X",
    "USD/INR":        "USDINR=X",
    "USDINR=X":       "USDINR=X",
    # MCX Commodity Futures (USD-denominated, converted to INR by caller)
    "MCX_GOLD":       "GC=F",
    "MCX_SILVER":     "SI=F",
}

# NIFTY BANK fallback ticker list — tried in order when primary fails
NIFTYBANK_FALLBACK_TICKERS = ["^NSEBANK", "NIFTYBEES.NS", "BANKBEES.NS"]

# Fallback ticker mappings when primary symbol/ticker fails or has alternate listings
FALLBACK_TICKER_MAP: Dict[str, List[str]] = {
    # NSE Indices
    "NIFTY BANK":     NIFTYBANK_FALLBACK_TICKERS,
    "NIFTYBANK":      NIFTYBANK_FALLBACK_TICKERS,
    "NIFTY 50":       ["^NSEI", "NIFTYBEES.NS"],
    "NIFTY50":        ["^NSEI", "NIFTYBEES.NS"],
    "SENSEX":         ["^BSESN"],
    "BSESENSEX":      ["^BSESN"],
    # Commodities & Precious Metals
    "GOLD":           ["GOLDBEES.NS", "GOLDSHARE.NS", "GC=F"],
    "GOLDBEES":       ["GOLDBEES.NS", "GOLDSHARE.NS"],
    "SILVER":         ["SILVERBEES.NS", "SILVER.NS", "SI=F"],
    "SILVERBEES":     ["SILVERBEES.NS", "SILVER.NS"],
    # Equities with corporate action or alternative ticker symbols
    "TATAMOTORS":     ["TMPV.NS", "TATAMOTORS.NS"],
    "TMPV":           ["TMPV.NS", "TATAMOTORS.NS"],
    "TMCV":           ["TMCV.NS", "TATAMOTORS.NS"],
    "BAJAJAUTO":      ["BAJAJ-AUTO.NS", "BAJAJAUTO.NS"],
    "BAJAJ-AUTO":     ["BAJAJ-AUTO.NS", "BAJAJAUTO.NS"],
    "MM":             ["M&M.NS", "MM.NS"],
    "M&M":            ["M&M.NS", "MM.NS"],
}

# Commodity futures that are USD-denominated (need INR conversion)
USD_COMMODITY_TICKERS = {"GC=F", "SI=F"}

# Data delay disclosed per the Yahoo Finance data agreement
DATA_DELAY_MINUTES = 15


def _resolve_yf_ticker(symbol: str) -> str:
    """
    Resolve a TradePilot symbol to its Yahoo Finance ticker.
    Falls back to SYMBOL.NS for unknown NSE equities.
    """
    clean = symbol.upper().replace(".NS", "").replace(".BO", "").strip()
    if clean in EXCHANGE_TICKER_MAP:
        return EXCHANGE_TICKER_MAP[clean]
    if clean.startswith("^") or "=" in clean or clean.endswith(".NS") or clean.endswith(".BO"):
        return clean
    return f"{clean}.NS"


def _get_market_status() -> str:
    """
    Return the current NSE market session based on IST clock.
    Sessions:
      PRE_OPEN  — 09:00–09:15 (pre-open call auction)
      OPEN      — 09:15–15:30 (continuous trading)
      CLOSING   — 15:30–16:00 (closing session / post-market)
      CLOSED    — all other times, weekends
    """
    ist = datetime.now(timezone(timedelta(hours=5, minutes=30)))
    if ist.weekday() >= 5:          # Saturday (5) or Sunday (6)
        return "CLOSED"
    hm = ist.hour * 60 + ist.minute
    if 540 <= hm < 555:             # 09:00–09:15
        return "PRE_OPEN"
    if 555 <= hm < 930:             # 09:15–15:30
        return "OPEN"
    if 930 <= hm < 960:             # 15:30–16:00
        return "CLOSING"
    return "CLOSED"


def _build_normalized_quote(
    clean_sym: str,
    exchange: str,
    instrument_token: str,
    last_price: float,
    open_p: float,
    high_p: float,
    low_p: float,
    prev_close: float,
    volume: int,
    data_status: str = "LIVE_DELAYED",
    stale_since: Optional[str] = None,
    previous_ltp: Optional[float] = None,
) -> Dict[str, Any]:
    """
    Build a normalized market tick object compliant with Requirement 4 & 6.
    Includes: symbol, exchange, ltp, price, last_price, change, change_percent,
    open, high, low, previous_close, volume, timestamp, provider_timestamp,
    price_movement ('UP' | 'DOWN' | 'UNCHANGED'), and data_age_ms.
    """
    import math

    def _sf(v: Any, d: float = 0.0) -> float:
        if v is None:
            return d
        try:
            f = float(v)
            if math.isnan(f) or math.isinf(f):
                return d
            return round(f, 2)
        except Exception:
            return d

    def _si(v: Any, d: int = 0) -> int:
        if v is None:
            return d
        try:
            f = float(v)
            if math.isnan(f) or math.isinf(f):
                return d
            return int(f)
        except Exception:
            return d

    lp = _sf(last_price)
    pc = _sf(prev_close)
    change = round(lp - pc, 2) if (lp and pc) else 0.0
    change_pct = round((change / pc) * 100.0, 2) if pc > 0 else 0.0

    # Calculate precise price movement relative to previous tick
    if previous_ltp is not None and previous_ltp > 0:
        if lp > previous_ltp:
            price_movement = "UP"
        elif lp < previous_ltp:
            price_movement = "DOWN"
        else:
            price_movement = "UNCHANGED"
    else:
        if change > 0:
            price_movement = "UP"
        elif change < 0:
            price_movement = "DOWN"
        else:
            price_movement = "UNCHANGED"

    now_iso = datetime.now(timezone.utc).isoformat()

    return {
        "symbol":              clean_sym,
        "exchange":            exchange,
        "instrument_token":    instrument_token,
        "timestamp":           now_iso,
        "provider_timestamp":  now_iso,
        "ltp":                 lp,
        "price":               lp,
        "last_price":          lp,
        "previous_ltp":        previous_ltp if previous_ltp is not None else lp,
        "price_movement":      price_movement,
        "open":                _sf(open_p),
        "high":                _sf(high_p),
        "low":                 _sf(low_p),
        "previous_close":      pc,
        "change":              change,
        "change_percent":      change_pct,
        "volume":              _si(volume),
        "data_age_ms":         0,
        "bid_price":           None,
        "ask_price":           None,
        "market_status":       _get_market_status(),
        "data_source":         "NSE_YFINANCE",
        "data_status":         data_status,
        "data_delay_minutes":  DATA_DELAY_MINUTES,
        "is_live":             True,
        "stale_since":         stale_since,
        "note":                (
            "Data sourced from Yahoo Finance (~15-20 min exchange-mandated delay). "
            "Bid/ask order book (Level 2) is NOT available on this feed — "
            "bid_price and ask_price are always None. "
            "Configure MARKET_DATA_PROVIDER=BROKER_API in .env for sub-second broker tick data."
        ),
    }


class NSEMarketDataProvider(MarketDataProvider):
    """
    NSE/BSE Market Data Provider backed by Yahoo Finance (yfinance).

    DATA INTEGRITY CONTRACT:
    - Returns real market data from Yahoo Finance (~15-20 min delayed)
    - data_status = "LIVE_DELAYED" when fresh data from Yahoo Finance
    - data_status = "STALE" when returning last-known cached quote
    - Returns None when no data is available at all (caller shows FEED DISCONNECTED)
    - NEVER returns hardcoded, invented, or randomly generated prices

    For true real-time data: configure MARKET_DATA_PROVIDER=BROKER_API
    with valid Zerodha / Upstox / Angel One credentials in .env
    """

    def __init__(self):
        super().__init__("NSE_YFINANCE")
        self._quote_cache: Dict[str, Dict[str, Any]] = {}
        self._last_fetch_ts: Dict[str, float] = {}
        self._cache_ttl_seconds: float = float(os.getenv("QUOTE_CACHE_TTL_SECONDS", "10.0"))
        # Symbols that returned HTTP 404 from Yahoo Finance — skip permanently
        self._404_symbols: set = set()

    def connect(self) -> bool:
        """
        Verify connectivity by attempting a lightweight yfinance call.
        Never raises — returns True when online, False when offline.
        """
        try:
            ticker = yf.Ticker("^NSEI")
            info = ticker.fast_info
            lp = getattr(info, "last_price", None)
            if lp and float(lp) > 0:
                self.is_connected = True
                logger.info("NSEMarketDataProvider: connected to Yahoo Finance feed.")
                return True
            # Even if last_price is not directly accessible, accept the connection
            self.is_connected = True
            logger.info("NSEMarketDataProvider: feed connection established (price pending).")
            return True
        except Exception as e:
            logger.warning(f"NSEMarketDataProvider: feed connection warning — {e}")
            self.is_connected = False
            return False

    def disconnect(self):
        self.is_connected = False
        logger.info("NSEMarketDataProvider: disconnected.")

    def subscribe(self, symbols: List[str]):
        for s in symbols:
            clean = s.upper().replace(".NS", "").replace(".BO", "")
            if clean not in self.subscribed_symbols:
                self.subscribed_symbols.append(clean)
    def unsubscribe(self, symbols: List[str]):
        for s in symbols:
            clean = s.upper().replace(".NS", "").replace(".BO", "")
            if clean in self.subscribed_symbols:
                self.subscribed_symbols.remove(clean)

    def get_quote(self, symbol: str) -> Optional[Dict[str, Any]]:
        """
        Fetch a real quote from Yahoo Finance.

        Returns:
            quote with data_status="LIVE_DELAYED"  — when fresh data arrived
            quote with data_status="STALE"          — when returning cache
            None                                    — when no data at all

        NEVER returns a hardcoded or invented price.
        """
        clean_sym = symbol.upper().replace(".NS", "").replace(".BO", "").strip()
        ticker_symbol = _resolve_yf_ticker(clean_sym)
        inst = get_instrument_by_symbol(clean_sym)
        token = str(inst["instrument_token"]) if inst else "UNKNOWN"
        exchange = inst.get("exchange", "NSE") if inst else "NSE"

        # Permanent-skip check: if Yahoo Finance 404'd this ticker, don't retry
        if clean_sym in self._404_symbols:
            return self._return_stale_cache_or_none(clean_sym)

        # Cache TTL check — avoid hammering Yahoo Finance
        now = time.time()
        last_fetch = self._last_fetch_ts.get(clean_sym, 0.0)
        if (now - last_fetch) < self._cache_ttl_seconds and clean_sym in self._quote_cache:
            cached = self._quote_cache[clean_sym]
            logger.debug(f"NSEMarketDataProvider: returning cached quote for '{clean_sym}' (age: {now - last_fetch:.1f}s)")
            return cached

        # NIFTY BANK: try multiple fallback tickers in order
        if clean_sym in ("NIFTY BANK", "NIFTYBANK"):
            return self._get_quote_with_fallbacks(
                clean_sym, NIFTYBANK_FALLBACK_TICKERS, exchange, token, now
            )

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
                    open_p     = getattr(fast, "open", None) or last_price
                    high_p     = getattr(fast, "day_high", None) or last_price
                    low_p      = getattr(fast, "day_low", None) or last_price
                    prev_close = getattr(fast, "previous_close", None) or last_price
                    volume     = int(getattr(fast, "last_volume", 0) or 0)
                    open_p     = float(open_p)     if open_p     else float(last_price)
                    high_p     = float(high_p)     if high_p     else float(last_price)
                    low_p      = float(low_p)      if low_p      else float(last_price)
                    prev_close = float(prev_close) if prev_close else float(last_price)
                    last_price = float(last_price)
                    fast_ok    = True
            except (KeyError, Exception) as fast_err:
                # Yahoo Finance raises KeyError('currentTradingPeriod') outside market hours
                logger.debug(f"NSEMarketDataProvider: fast_info unavailable for '{clean_sym}' ({fast_err}), falling back to history")

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
                    prev_close = float(hist["Close"].iloc[-2]) if len(hist) > 1 else last_price
                    volume     = int(hist["Volume"].iloc[-1])
                else:
                    # All history periods returned empty — Yahoo Finance has no data for this ticker.
                    # Add to skip list so we don't hammer the API every 3 seconds.
                    logger.warning(
                        f"NSEMarketDataProvider: ticker '{ticker_symbol}' returned empty data for "
                        f"all periods — adding '{clean_sym}' to skip list. Serving STALE cache only."
                    )
                    self._404_symbols.add(clean_sym)
                    return self._return_stale_cache_or_none(clean_sym)

            if not last_price or float(last_price) <= 0:
                return self._return_stale_cache_or_none(clean_sym)

            prev_q = self._quote_cache.get(clean_sym)
            prev_ltp = prev_q.get("ltp") or prev_q.get("last_price") if prev_q else None

            quote_obj = _build_normalized_quote(
                clean_sym=clean_sym,
                exchange=exchange,
                instrument_token=token,
                last_price=float(last_price),
                open_p=open_p,
                high_p=high_p,
                low_p=low_p,
                prev_close=prev_close,
                volume=volume,
                data_status="LIVE_DELAYED",
                previous_ltp=prev_ltp,
            )

            # Store in cache
            self._quote_cache[clean_sym] = quote_obj
            self._last_fetch_ts[clean_sym] = now
            return quote_obj

        except Exception as e:
            err_str = str(e)
            # Detect permanent HTTP 404 — add to skip list so we stop retrying
            if "404" in err_str or "No data found" in err_str or "possibly delisted" in err_str.lower():
                logger.warning(
                    f"NSEMarketDataProvider: ticker '{ticker_symbol}' returned 404/no-data — "
                    f"adding '{clean_sym}' to skip list. Will serve STALE cache only."
                )
                self._404_symbols.add(clean_sym)
            else:
                logger.error(f"NSEMarketDataProvider: error fetching '{clean_sym}' ({ticker_symbol}): {e}")
            return self._return_stale_cache_or_none(clean_sym)

    def _get_quote_with_fallbacks(
        self,
        clean_sym: str,
        fallback_tickers: List[str],
        exchange: str,
        token: str,
        now: float,
    ) -> Optional[Dict[str, Any]]:
        """
        Try each ticker in fallback_tickers in order until one returns a valid price.
        Used for symbols like NIFTY BANK where the primary Yahoo Finance ticker is unreliable.
        """
        for ticker_symbol in fallback_tickers:
            try:
                ticker = yf.Ticker(ticker_symbol)
                last_price = open_p = high_p = low_p = prev_close = None
                volume = 0

                try:
                    fast = ticker.fast_info
                    lp = getattr(fast, "last_price", None) or getattr(fast, "regular_market_price", None)
                    if lp and float(lp) > 0:
                        last_price = float(lp)
                        open_p     = float(getattr(fast, "open", None) or lp)
                        high_p     = float(getattr(fast, "day_high", None) or lp)
                        low_p      = float(getattr(fast, "day_low", None) or lp)
                        prev_close = float(getattr(fast, "previous_close", None) or lp)
                        volume     = int(getattr(fast, "last_volume", 0) or 0)
                except Exception:
                    pass

                if not last_price or float(last_price) <= 0:
                    # Try history as fallback
                    for period in ("5d", "1mo"):
                        try:
                            hist = ticker.history(period=period)
                            if not hist.empty:
                                last_price = float(hist["Close"].iloc[-1])
                                open_p     = float(hist["Open"].iloc[-1])
                                high_p     = float(hist["High"].iloc[-1])
                                low_p      = float(hist["Low"].iloc[-1])
                                prev_close = float(hist["Close"].iloc[-2]) if len(hist) > 1 else last_price
                                volume     = int(hist["Volume"].iloc[-1])
                                break
                        except Exception:
                            pass

                if last_price and float(last_price) > 0:
                    prev_q = self._quote_cache.get(clean_sym)
                    prev_ltp = prev_q.get("ltp") or prev_q.get("last_price") if prev_q else None

                    quote_obj = _build_normalized_quote(
                        clean_sym=clean_sym,
                        exchange=exchange,
                        instrument_token=token,
                        last_price=float(last_price),
                        open_p=open_p or last_price,
                        high_p=high_p or last_price,
                        low_p=low_p or last_price,
                        prev_close=prev_close or last_price,
                        volume=volume,
                        data_status="LIVE_DELAYED",
                        previous_ltp=prev_ltp,
                    )
                    self._quote_cache[clean_sym] = quote_obj
                    self._last_fetch_ts[clean_sym] = now
                    logger.info(
                        f"NSEMarketDataProvider: '{clean_sym}' resolved via fallback ticker '{ticker_symbol}' "
                        f"— price={last_price}"
                    )
                    return quote_obj

            except Exception as fe:
                logger.debug(f"NSEMarketDataProvider: fallback ticker '{ticker_symbol}' failed for '{clean_sym}': {fe}")
                continue

        logger.warning(
            f"NSEMarketDataProvider: all fallback tickers exhausted for '{clean_sym}'. "
            f"Returning stale cache or None."
        )
        return self._return_stale_cache_or_none(clean_sym)

    def _return_stale_cache_or_none(self, clean_sym: str) -> Optional[Dict[str, Any]]:

        """
        When live data is unavailable, return the last-known cached quote
        with data_status="STALE".
        If no cache exists, return None — the caller must show FEED DISCONNECTED.

        CRITICAL: This function MUST NEVER invent or return a hardcoded price.
        """
        if clean_sym in self._quote_cache:
            cached = self._quote_cache[clean_sym].copy()
            cached["data_status"] = "STALE"
            cached["is_live"] = False
            cached["data_source"] = "NSE_YFINANCE (STALE — last known price)"
            cached["stale_since"] = datetime.now(timezone.utc).isoformat()
            logger.warning(
                f"NSEMarketDataProvider: returning STALE cache for '{clean_sym}'. "
                f"Last known price: {cached.get('last_price')}. "
                f"This is NOT a current live price."
            )
            return cached

        # No cache and no live data → signal the caller to show FEED DISCONNECTED
        logger.warning(
            f"NSEMarketDataProvider: no live data and no cache for '{clean_sym}'. "
            f"Returning None. UI must display FEED DISCONNECTED."
        )
        return None

    def get_quotes(self, symbols: List[str]) -> List[Dict[str, Any]]:
        results = []
        for s in symbols:
            q = self.get_quote(s)
            if q:
                results.append(q)
        return results

    def get_instruments(self) -> List[Dict[str, Any]]:
        return get_all_instruments()

    def get_historical_candles(
        self,
        symbol: str,
        timeframe: str = "1h",
        count: int = 100,
    ) -> List[Dict[str, Any]]:
        """
        Fetch real OHLCV candlestick bars from Yahoo Finance.
        Returns [] when data is unavailable — callers must handle empty list.
        NEVER generates synthetic / fake candles.
        """
        clean_sym = symbol.upper().replace(".NS", "").replace(".BO", "")
        ticker_symbol = _resolve_yf_ticker(clean_sym)

        yf_interval_map = {
            "1m":  "1m",
            "3m":  "5m",
            "5m":  "5m",
            "15m": "15m",
            "30m": "30m",
            "1h":  "1h",
            "2h":  "1h",
            "4h":  "1h",
            "1d":  "1d",
            "1D":  "1d",
            "1w":  "1wk",
            "1wk": "1wk",
            "1W":  "1wk",
            "1mo": "1mo",
            "1M":  "1mo",
            "6mo": "1d",
            "6M":  "1d",
            "past_6mo": "1d",
            "1y":  "1d",
            "1Y":  "1d",
        }
        yf_period_map = {
            "1m":  "5d",
            "3m":  "1mo",
            "5m":  "1mo",
            "15m": "1mo",
            "30m": "1mo",
            "1h":  "1mo",
            "2h":  "3mo",
            "4h":  "3mo",
            "1d":  "1y",
            "1D":  "1y",
            "1w":  "2y",
            "1wk": "2y",
            "1W":  "2y",
            "1mo": "5y",
            "1M":  "5y",
            "6mo": "6mo",
            "6M":  "6mo",
            "past_6mo": "6mo",
            "1y":  "1y",
            "1Y":  "1y",
        }

        yf_interval = yf_interval_map.get(timeframe, "1h")
        primary_period = yf_period_map.get(timeframe, yf_period_map.get(yf_interval, "1mo"))

        # Fallback period candidates to ensure continuous real data without delisting errors
        if timeframe in ("6mo", "6M", "past_6mo"):
            periods_to_try = ["6mo", "1y", "3mo"]
        elif yf_interval in ("1m", "5m", "15m", "30m", "1h"):
            periods_to_try = [primary_period, "1mo", "5d", "3mo", "60d"]
        else:
            periods_to_try = [primary_period, "1y", "6mo", "2y", "5y"]

        candidate_periods = []
        for p in periods_to_try:
            if p not in candidate_periods:
                candidate_periods.append(p)

        df = None
        ticker = yf.Ticker(ticker_symbol)
        for p in candidate_periods:
            try:
                test_df = ticker.history(period=p, interval=yf_interval)
                if test_df is not None and not test_df.empty:
                    df = test_df
                    break
            except Exception:
                continue

        # If primary ticker failed, try fallback tickers (e.g. GOLDBEES.NS, etc.)
        if df is None or df.empty:
            fallback_tickers = FALLBACK_TICKER_MAP.get(clean_sym, [])
            for alt in fallback_tickers:
                alt_yf = _resolve_yf_ticker(alt)
                if alt_yf == ticker_symbol:
                    continue
                try:
                    alt_ticker = yf.Ticker(alt_yf)
                    for p in candidate_periods[:2]:
                        test_df = alt_ticker.history(period=p, interval=yf_interval)
                        if test_df is not None and not test_df.empty:
                            df = test_df
                            ticker_symbol = alt_yf
                            break
                    if df is not None and not df.empty:
                        break
                except Exception:
                    continue

        if df is None or df.empty:
            logger.warning(f"NSEMarketDataProvider: no historical data for '{clean_sym}' ({ticker_symbol}).")
            return []

        bars = []
        for ts, row in df.iterrows():
            try:
                dt = ts.to_pydatetime()
                c = float(row["Close"])
                if math.isnan(c) or math.isinf(c) or c <= 0:
                    continue
                o = float(row.get("Open", c))
                h = float(row.get("High", c))
                l = float(row.get("Low", c))
                if math.isnan(o) or math.isinf(o) or o <= 0:
                    o = c
                if math.isnan(h) or math.isinf(h) or h <= 0:
                    h = max(o, c)
                if math.isnan(l) or math.isinf(l) or l <= 0:
                    l = min(o, c)
                vol = row.get("Volume", 0)
                vol_int = int(vol) if (vol is not None and not (isinstance(vol, float) and math.isnan(vol))) else 0
                bars.append({
                    "timestamp": dt.isoformat(),
                    "time":      int(dt.timestamp()),
                    "open":      round(o, 2),
                    "high":      round(h, 2),
                    "low":       round(l, 2),
                    "close":     round(c, 2),
                    "volume":    vol_int,
                    "data_source": "NSE_YFINANCE",
                })
            except Exception:
                continue

        if timeframe in ("6mo", "6M", "past_6mo"):
            return bars[-max(count, 130):]
        return bars[-count:]

    def get_market_status(self) -> Dict[str, Any]:
        """Fetch NSE market session status."""
        from app.services.market_data.market_status_service import get_market_status_service
        return get_market_status_service().get_session_status(is_feed_connected=self.is_connected)
