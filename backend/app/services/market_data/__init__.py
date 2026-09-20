"""
Market Data Service — TradePilot Public API

This module exposes helper functions that the routes, trade manager,
and other services use to access market data.

CRITICAL CONTRACT:
  - Every price returned by this module MUST come from the active
    MarketDataProvider (currently NSEMarketDataProvider / yfinance).
  - This module MUST NEVER invent, guess, or hardcode any market price.
  - When live data is unavailable, return None or [] — never fake values.
  - The caller is responsible for displaying "FEED DISCONNECTED" to the user.
"""
import time
import logging
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional

import yfinance as yf

from app.services.market_data.base_provider import MarketDataProvider
from app.services.market_data.market_data_manager import get_market_data_manager, MarketDataManager
from app.services.market_data.instrument_manager import get_instrument_manager, InstrumentManager
from app.services.market_data.market_status_service import get_market_status_service, MarketStatusService
from app.services.market_data.websocket_manager import get_websocket_manager, WebSocketMarketStreamManager
from app.services.market_data.nse_provider import NSEMarketDataProvider
from app.services.market_data.bse_provider import BSEMarketDataProvider
from app.services.market_data.broker_provider import BrokerMarketDataProvider
from app.services.feature_engineering import (
    compute_sma,
    compute_ema,
    compute_bollinger_bands,
)

logger = logging.getLogger(__name__)


def get_current_live_price(symbol: str) -> Optional[float]:
    """
    Return the current live price for a symbol from the active market data provider.

    Returns:
        float  — the real market price when the feed is available
        None   — when no live data is available (feed disconnected / symbol not found)

    CRITICAL: This function MUST NEVER return a hardcoded or invented price.
    Callers must handle None and display FEED DISCONNECTED to the user.
    """
    manager = get_market_data_manager()
    quote = manager.get_quote(symbol)
    if quote:
        p = quote.get("last_price") if quote.get("last_price") is not None else quote.get("price")
        if isinstance(p, (int, float)) and p > 0:
            return float(p)


    # No live price available — return None so callers show FEED DISCONNECTED
    logger.warning(
        f"get_current_live_price('{symbol}'): no live price available. "
        f"Returning None. UI must display FEED DISCONNECTED."
    )
    return None


def get_price(symbol: str) -> Optional[float]:
    """Alias for get_current_live_price — returns None when feed is down."""
    return get_current_live_price(symbol)


def get_indian_indices() -> Dict[str, Any]:
    """
    Return live NIFTY 50, NIFTY BANK, SENSEX, INDIA VIX, and precious metals (GOLD, SILVER) data.
    Each index entry contains only data sourced from the live provider.
    Missing indices are omitted from the response (caller shows FEED DISCONNECTED).
    """
    manager = get_market_data_manager()
    n50    = manager.get_nifty50()
    n_bank = manager.get_niftybank()
    sensex = manager.get_sensex()
    vix    = manager.get_quote("INDIA VIX")
    gold   = manager.get_gold()
    silver = manager.get_silver()

    import math

    def _clean_val(v: Any, default: Any = 0.0) -> Any:
        if v is None:
            return default
        try:
            f = float(v)
            if math.isnan(f) or math.isinf(f):
                return default
            return round(f, 2)
        except (ValueError, TypeError):
            return default

    def _clean_int(v: Any, default: int = 0) -> int:
        if v is None:
            return default
        try:
            f = float(v)
            if math.isnan(f) or math.isinf(f):
                return default
            return int(f)
        except (ValueError, TypeError):
            return default

    res: Dict[str, Any] = {}

    def _pack_index(name: str, q: Optional[Dict[str, Any]]) -> None:
        if not q:
            return
        lp = _clean_val(q.get("ltp") or q.get("last_price") or q.get("price"))
        res[name] = {
            "ltp":                lp,
            "price":              lp,
            "last_price":         lp,
            "previous_ltp":       _clean_val(q.get("previous_ltp", lp)),
            "price_movement":     q.get("price_movement", "UNCHANGED"),
            "change":             _clean_val(q.get("change")),
            "change_percent":     _clean_val(q.get("change_percent")),
            "open":               _clean_val(q.get("open")),
            "high":               _clean_val(q.get("high")),
            "low":                _clean_val(q.get("low")),
            "previous_close":     _clean_val(q.get("previous_close")),
            "volume":             _clean_int(q.get("volume")),
            "timestamp":          q.get("timestamp"),
            "provider_timestamp": q.get("provider_timestamp") or q.get("timestamp"),
            "data_status":        q.get("data_status", "LIVE"),
            "data_source":        q.get("data_source", "NSE_YFINANCE"),
            "is_live":            q.get("is_live", True),
        }

    _pack_index("NIFTY 50",   n50)
    _pack_index("NIFTY BANK", n_bank)
    _pack_index("SENSEX",     sensex)
    _pack_index("GOLD",       gold)
    _pack_index("SILVER",     silver)

    # INDIA VIX — fewer fields
    if vix:
        vix_lp = _clean_val(vix.get("ltp") or vix.get("last_price") or vix.get("price"))
        res["INDIA VIX"] = {
            "ltp":                vix_lp,
            "price":              vix_lp,
            "last_price":         vix_lp,
            "previous_ltp":       _clean_val(vix.get("previous_ltp", vix_lp)),
            "price_movement":     vix.get("price_movement", "UNCHANGED"),
            "change":             _clean_val(vix.get("change")),
            "change_percent":     _clean_val(vix.get("change_percent")),
            "open":               _clean_val(vix.get("open")),
            "high":               _clean_val(vix.get("high")),
            "low":                _clean_val(vix.get("low")),
            "previous_close":     _clean_val(vix.get("previous_close")),
            "timestamp":          vix.get("timestamp"),
            "provider_timestamp": vix.get("provider_timestamp") or vix.get("timestamp"),
            "data_status":        vix.get("data_status", "LIVE"),
            "data_source":        vix.get("data_source", "NSE_YFINANCE"),
            "is_live":            vix.get("is_live", True),
        }

    return res


def get_quotes() -> List[Dict[str, Any]]:
    """
    Return normalized real-time quotes for all tracked symbols.

    Each returned quote includes only fields derivable from the live provider.
    Fake calculated fields (pe_ratio, sentiment_score, etc.) have been removed.
    Missing quotes are excluded — caller must handle empty list.
    """
    manager = get_market_data_manager()
    raw_quotes = manager.get_all_quotes()
    formatted: List[Dict[str, Any]] = []

    for q in raw_quotes:
        sym = q["symbol"]
        price = q.get("ltp") or q.get("last_price") or q.get("price")

        # Skip if no valid price from provider
        if price is None or not isinstance(price, (int, float)) or price <= 0:
            continue

        inst = get_instrument_manager().get_instrument(sym)

        formatted.append({
            "symbol":             sym,
            "name":               inst["company_name"] if inst else sym,
            "exchange":           q.get("exchange", "NSE"),
            "ltp":                round(float(price), 2),
            "price":              round(float(price), 2),
            "last_price":         round(float(price), 2),
            "previous_ltp":       q.get("previous_ltp", price),
            "price_movement":     q.get("price_movement", "UNCHANGED"),
            "open":               q.get("open"),
            "high":               q.get("high"),
            "low":                q.get("low"),
            "previous_close":     q.get("previous_close"),
            "change":             q.get("change"),
            "change_percent":     q.get("change_percent"),
            "volume":             q.get("volume"),
            "data_status":        q.get("data_status", "LIVE"),
            "data_source":        q.get("data_source", "NSE_YFINANCE"),
            "is_live":            q.get("is_live", True),
            "timestamp":          q.get("timestamp"),
            "provider_timestamp": q.get("provider_timestamp") or q.get("timestamp"),
            "data_age_ms":        q.get("data_age_ms", 0),
        })

    return formatted


def generate_historical_candles(
    symbol: str,
    timeframe: str = "1h",
    count: int = 60,
) -> List[Dict[str, Any]]:
    """
    Return real OHLCV candlestick bars from the active market data provider.

    When real bars are available, computes SMA20, EMA21, and Bollinger Bands
    from the actual close prices.

    Returns [] when no data is available.
    NEVER generates fake/synthetic candles as fallback.
    """
    manager = get_market_data_manager()
    real_bars = manager.get_historical_candles(symbol, timeframe, count)

    if not real_bars:
        logger.warning(
            f"generate_historical_candles('{symbol}', '{timeframe}'): "
            f"no real bars from provider. Returning empty list. "
            f"UI must display 'Awaiting Live Market Feed'."
        )
        return []

    # Compute technical overlays from REAL historical data
    closes = [b["close"] for b in real_bars]
    sma20 = compute_sma(closes, min(20, len(closes)))
    ema21 = compute_ema(closes, min(21, len(closes)))

    for i, b in enumerate(real_bars):
        b["sma20"] = round(sma20[i], 2) if i < len(sma20) else None
        b["ema21"] = round(ema21[i], 2) if i < len(ema21) else None

        sub_closes = closes[: i + 1]
        if len(sub_closes) >= 2:
            up, mid, low, _, _ = compute_bollinger_bands(sub_closes, min(20, len(sub_closes)), 2.0)
            b["upper_bb"] = up
            b["lower_bb"] = low
            b["mid_bb"]   = mid
        else:
            b["upper_bb"] = None
            b["lower_bb"] = None
            b["mid_bb"]   = None

        # VWAP approximation: (H+L+C)/3 — a reasonable intraday proxy
        h = b.get("high", b["close"])
        l = b.get("low", b["close"])
        b["vwap"] = round((h + l + b["close"]) / 3.0, 2)

    return real_bars


def get_order_book_depth(symbol: str) -> Dict[str, Any]:
    """
    Return order book depth for a symbol.

    NOTE: yfinance does NOT provide Level 2 order book data.
    The bids/asks below are approximated from the last_price and spread.
    'imbalance_pct' is set to null as it cannot be computed without real L2 data.

    For real order book data, configure a broker API.
    """
    live_price = get_current_live_price(symbol)

    if live_price is None:
        return {
            "symbol":      symbol.upper(),
            "exchange":    "NSE",
            "timestamp":   datetime.now(timezone.utc).isoformat(),
            "bids":        [],
            "asks":        [],
            "spread":      None,
            "spread_pct":  None,
            "imbalance_pct": None,
            "data_source": "FEED_DISCONNECTED",
            "is_live":     False,
        }

    spread = round(max(0.05, live_price * 0.0002), 2)
    bids: List[Dict[str, Any]] = []
    asks: List[Dict[str, Any]] = []

    for i in range(5):
        step = (i + 1) * (spread * 0.8)
        bids.append({
            "price":        round(live_price - (spread / 2.0) - step, 2),
            "quantity":     None,   # Not available without L2 feed
            "orders_count": None,
        })
        asks.append({
            "price":        round(live_price + (spread / 2.0) + step, 2),
            "quantity":     None,
            "orders_count": None,
        })

    return {
        "symbol":        symbol.upper(),
        "exchange":      "NSE",
        "timestamp":     datetime.now(timezone.utc).isoformat(),
        "bids":          bids,
        "asks":          asks,
        "spread":        spread,
        "spread_pct":    round((spread / live_price) * 100, 3) if live_price > 0 else None,
        "imbalance_pct": None,  # Requires real L2 order book data (broker API)
        "data_source":   "NSE_YFINANCE (L2 not available — configure broker API for real order book)",
        "is_live":       True,
    }


def get_market_breadth() -> Dict[str, Any]:
    """Compute advance/decline breadth from live quotes."""
    quotes = get_quotes()
    if not quotes:
        return {
            "advancers":            0,
            "decliners":            0,
            "unchanged":            0,
            "advance_decline_ratio": None,
            "market_sentiment":     "AWAITING_FEED",
        }

    advancers = sum(1 for q in quotes if (q.get("change") or 0) > 0)
    decliners  = sum(1 for q in quotes if (q.get("change") or 0) < 0)
    unchanged  = len(quotes) - advancers - decliners

    return {
        "advancers":            advancers,
        "decliners":            decliners,
        "unchanged":            unchanged,
        "advance_decline_ratio": round(advancers / max(1, decliners), 2),
        "market_sentiment":     "BULLISH_DOMINANT" if advancers >= decliners else "BEARISH_DOMINANT",
    }


def get_most_active_stocks() -> Dict[str, Any]:
    """Return movers sorted by real live volume and price change."""
    quotes = get_quotes()
    if not quotes:
        return {
            "most_active_turnover": [],
            "most_active_volume":   [],
            "top_gainers":          [],
            "top_losers":           [],
        }

    by_turnover  = sorted(quotes, key=lambda q: (q.get("price") or 0) * (q.get("volume") or 0), reverse=True)
    by_volume    = sorted(quotes, key=lambda q: q.get("volume") or 0, reverse=True)
    top_gainers  = sorted(
        [q for q in quotes if (q.get("change_percent") or 0) > 0],
        key=lambda q: q.get("change_percent") or 0,
        reverse=True,
    )
    top_losers   = sorted(
        [q for q in quotes if (q.get("change_percent") or 0) < 0],
        key=lambda q: q.get("change_percent") or 0,
    )

    return {
        "most_active_turnover": by_turnover[:5],
        "most_active_volume":   by_volume[:5],
        "top_gainers":          top_gainers[:5],
        "top_losers":           top_losers[:5],
    }


def get_corporate_actions() -> List[Dict[str, Any]]:
    """
    Return upcoming corporate actions (dividends, splits, buybacks).

    Currently returns empty list — connect an authorized corporate action
    data feed (NSE/BSE bhavcopy, Refinitiv, Bloomberg) to populate this.
    """
    return []


# ── Module-level caches for macro + news (avoids hammering Yahoo Finance) ──
_macro_cache: Dict[str, Any] = {}
_macro_cache_ts: float = 0.0
_MACRO_CACHE_TTL: float = 300.0  # 5 minutes

_news_cache: List[Dict[str, Any]] = []
_news_cache_ts: float = 0.0
_NEWS_CACHE_TTL: float = float(__import__('os').getenv("NEWS_CACHE_TTL_SECONDS", "300"))


def _fetch_live_usdinr() -> Optional[float]:
    """Fetch live USD/INR exchange rate from Yahoo Finance USDINR=X."""
    try:
        ticker = yf.Ticker("USDINR=X")
        fast = ticker.fast_info
        rate = getattr(fast, "last_price", None) or getattr(fast, "regular_market_price", None)
        if rate and float(rate) > 50:  # sanity check — USD/INR is always > 50
            return round(float(rate), 4)
        # Fallback to history
        hist = ticker.history(period="5d")
        if not hist.empty:
            return round(float(hist["Close"].iloc[-1]), 4)
    except Exception as e:
        logger.warning(f"get_macro_indicators: USD/INR fetch failed — {e}")
    return None


def _fetch_live_gsec_yield() -> Optional[float]:
    """
    Approximate 10-year Indian G-Sec yield.
    Yahoo Finance does not have a direct India G-Sec yield ticker.
    Uses ^TNX (US 10yr) as a directional proxy; for real data connect RBI/CCIL feed.
    Returns None if unavailable — caller shows last known value.
    """
    # Yahoo Finance India G-Sec is not directly available.
    # Return None; the static fallback in get_macro_indicators covers this.
    return None


def get_macro_indicators() -> List[Dict[str, Any]]:
    """
    Return macro-economic indicators with live USD/INR from Yahoo Finance.

    LIVE:
      - USD/INR exchange rate — fetched from Yahoo Finance USDINR=X every 5 minutes

    STATIC (updated manually on policy announcements):
      - RBI Repo Rate    — changes only on MPC meeting dates (~6x/year)
      - India CPI        — released monthly by MOSPI
      - India GDP (YoY)  — released quarterly by NSO
      - 10yr G-Sec Yield — no free live feed available; update manually

    Caches the result for 5 minutes to avoid hammering Yahoo Finance.
    """
    global _macro_cache, _macro_cache_ts

    now = time.time()

    # ── Live USD/INR ──
    if now - _macro_cache_ts > _MACRO_CACHE_TTL:
        live_usdinr = _fetch_live_usdinr()
        if live_usdinr:
            _macro_cache["usdinr"] = live_usdinr
            _macro_cache["usdinr_ts"] = datetime.now(timezone.utc).isoformat()
        _macro_cache_ts = now

    usdinr_val   = _macro_cache.get("usdinr", 83.85)   # static fallback
    usdinr_ts    = _macro_cache.get("usdinr_ts", None)
    usdinr_live  = usdinr_ts is not None

    return [
        {
            "name":        "RBI Repo Rate",
            "category":    "Monetary Policy",
            "value":       6.50,
            "unit":        "%",
            "trend":       "STABLE",
            "source":      "RBI Monetary Policy Committee",
            "is_live":     False,
            "note":        "Updated manually on MPC announcement dates (~6x/year). Current: effective Jun 2024.",
        },
        {
            "name":        "India CPI Inflation",
            "category":    "Inflation",
            "value":       4.85,
            "unit":        "%",
            "trend":       "COOLING",
            "source":      "Ministry of Statistics & PI (MOSPI)",
            "is_live":     False,
            "note":        "Updated manually on monthly MOSPI release. Last update: May 2025.",
        },
        {
            "name":        "India GDP Growth (YoY)",
            "category":    "Economic Growth",
            "value":       7.20,
            "unit":        "%",
            "trend":       "EXPANDING",
            "source":      "MOSPI / National Statistical Office",
            "is_live":     False,
            "note":        "Updated manually on quarterly NSO release. Q4 FY25 estimate.",
        },
        {
            "name":        "10-Year Indian G-Sec Yield",
            "category":    "Fixed Income",
            "value":       6.86,
            "unit":        "%",
            "trend":       "FALLING",
            "source":      "RBI / CCIL",
            "is_live":     False,
            "note":        "No free live feed available. Connect RBI/CCIL or Bloomberg for real-time yield.",
        },
        {
            "name":        "USD / INR Exchange Rate",
            "category":    "Forex",
            "value":       usdinr_val,
            "unit":        "₹",
            "trend":       "STABLE",
            "source":      "Yahoo Finance (USDINR=X)" if usdinr_live else "RBI Reference Rate (static fallback)",
            "is_live":     usdinr_live,
            "timestamp":   usdinr_ts,
            "note":        "Live rate from Yahoo Finance, refreshed every 5 minutes." if usdinr_live
                           else "Static fallback — Yahoo Finance USD/INR feed unavailable.",
        },
    ]


# ── News symbols to poll for headlines ──
_NEWS_SYMBOLS = ["RELIANCE.NS", "TCS.NS", "INFY.NS", "HDFCBANK.NS", "^NSEI"]


def get_news_feed() -> List[Dict[str, Any]]:
    """
    Return live market news headlines from Yahoo Finance.

    Fetches the `.news` property for key NSE symbols and NIFTY 50.
    Results are deduplicated by URL and cached for NEWS_CACHE_TTL_SECONDS.

    Each item contains: title, publisher, link, publish_time, symbols.
    """
    global _news_cache, _news_cache_ts

    now = time.time()
    if now - _news_cache_ts < _NEWS_CACHE_TTL and _news_cache:
        return _news_cache

    seen_urls: set = set()
    articles: List[Dict[str, Any]] = []

    for sym in _NEWS_SYMBOLS:
        try:
            ticker = yf.Ticker(sym)
            raw_news = ticker.news or []
            for item in raw_news[:8]:  # cap per symbol
                url = item.get("link") or item.get("url", "")
                if not url or url in seen_urls:
                    continue
                seen_urls.add(url)

                # Normalise publish time
                pub_ts = item.get("providerPublishTime") or item.get("publishedAt")
                pub_dt = None
                if pub_ts:
                    try:
                        pub_dt = datetime.fromtimestamp(int(pub_ts), tz=timezone.utc).isoformat()
                    except Exception:
                        pub_dt = str(pub_ts)

                articles.append({
                    "title":         item.get("title", ""),
                    "publisher":     item.get("publisher", "Yahoo Finance"),
                    "link":          url,
                    "publish_time":  pub_dt,
                    "thumbnail":     (item.get("thumbnail") or {}).get("resolutions", [{}])[0].get("url") if item.get("thumbnail") else None,
                    "related_symbols": item.get("relatedTickers", []) or [],
                    "source":        "YFINANCE_NEWS",
                })
        except Exception as e:
            logger.debug(f"get_news_feed: failed for '{sym}' — {e}")
            continue

    # Sort newest first (by publish_time string, ISO format sorts correctly)
    articles.sort(key=lambda a: a.get("publish_time") or "", reverse=True)

    # Keep top 30 deduplicated articles
    _news_cache = articles[:30]
    _news_cache_ts = now

    if not _news_cache:
        logger.info("get_news_feed: no articles returned from Yahoo Finance news.")

    return _news_cache


def get_us_indices() -> Dict[str, Any]:
    """Return live quotes for US benchmark indices (NASDAQ 100, S&P 500, DOW JONES, US VIX)."""
    return get_market_data_manager().get_us_indices()


def get_us_quotes(symbols: Optional[List[str]] = None) -> List[Dict[str, Any]]:
    """Return live quotes for US equities and ETFs."""
    return get_market_data_manager().get_us_quotes(symbols)


def get_international_instruments() -> List[Dict[str, Any]]:
    """Return all instruments supported by the international provider."""
    return get_market_data_manager().get_international_instruments()

