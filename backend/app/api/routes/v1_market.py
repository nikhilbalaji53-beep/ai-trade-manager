import asyncio
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, HTTPException, Query

from app.services.market_data.market_data_manager import get_market_data_manager
from app.services.market_data.instrument_manager import get_instrument_manager
from app.services.market_data.websocket_manager import get_websocket_manager
from app.services.market_data.nifty50_constituents import get_nifty50_constituents
from app.services.market_data import (
    get_macro_indicators,
    get_news_feed,
    get_indian_indices,
    get_market_breadth,
    get_most_active_stocks,
)
from app.schemas.trade import ScannerResult
from app.services.market_scanner import scan_market

v1_router = APIRouter(prefix="/v1", tags=["v1-market"])


@v1_router.get("/market/quote/{symbol}")
def get_v1_quote(symbol: str):
    manager = get_market_data_manager()
    quote = manager.get_quote(symbol)
    if not quote:
        raise HTTPException(
            status_code=404,
            detail={
                "error": "QUOTE_NOT_AVAILABLE",
                "symbol": symbol,
                "message": f"Real-time market quote for '{symbol}' not available from active provider.",
                "action_required": "Ensure market data provider connection is active and symbol is listed on NSE/BSE."
            }
        )
    return quote


@v1_router.get("/market/quotes")
def get_v1_quotes(symbols: Optional[str] = Query(default=None, description="Comma-separated symbols")):
    manager = get_market_data_manager()
    symbol_list = [s.strip().upper() for s in symbols.split(",")] if symbols else None
    quotes = manager.get_quotes(symbol_list)
    return quotes


@v1_router.get("/market/nifty50")
def get_v1_nifty50():
    manager = get_market_data_manager()
    quote = manager.get_nifty50()
    if not quote:
        raise HTTPException(
            status_code=503,
            detail={
                "error": "NIFTY50_FEED_DISCONNECTED",
                "message": "NIFTY 50 live feed is currently disconnected or unavailable.",
                "data_source": "FEED_DISCONNECTED",
                "is_live": False,
            }
        )
    return quote


@v1_router.get("/market/niftybank")
def get_v1_niftybank():
    manager = get_market_data_manager()
    quote = manager.get_niftybank()
    if not quote:
        raise HTTPException(
            status_code=503,
            detail={
                "error": "NIFTYBANK_FEED_DISCONNECTED",
                "message": "NIFTY BANK live feed is currently disconnected or unavailable.",
                "data_source": "FEED_DISCONNECTED",
                "is_live": False,
            }
        )
    return quote


@v1_router.get("/market/sensex")
def get_v1_sensex():
    manager = get_market_data_manager()
    quote = manager.get_sensex()
    if not quote:
        raise HTTPException(
            status_code=503,
            detail={
                "error": "SENSEX_FEED_DISCONNECTED",
                "message": "SENSEX live feed is currently disconnected or unavailable.",
                "data_source": "FEED_DISCONNECTED",
                "is_live": False,
            }
        )
    return quote


@v1_router.get("/market/gold")
def get_v1_gold():
    manager = get_market_data_manager()
    quote = manager.get_gold()
    if not quote:
        raise HTTPException(
            status_code=503,
            detail={
                "error": "GOLD_FEED_DISCONNECTED",
                "message": "GOLD live feed is currently disconnected or unavailable.",
                "data_source": "FEED_DISCONNECTED",
                "is_live": False,
            }
        )
    return quote


@v1_router.get("/market/silver")
def get_v1_silver():
    manager = get_market_data_manager()
    quote = manager.get_silver()
    if not quote:
        raise HTTPException(
            status_code=503,
            detail={
                "error": "SILVER_FEED_DISCONNECTED",
                "message": "SILVER live feed is currently disconnected or unavailable.",
                "data_source": "FEED_DISCONNECTED",
                "is_live": False,
            }
        )
    return quote


@v1_router.get("/market/commodities")
def get_v1_commodities():
    manager = get_market_data_manager()
    return manager.get_commodities_live()


@v1_router.get("/market/nifty50/constituents")
def get_v1_nifty50_constituents(live: bool = Query(default=True, description="Fetch live quotes if true")):
    manager = get_market_data_manager()
    if live:
        return manager.get_nifty50_constituents_live()
    return get_nifty50_constituents()


@v1_router.get("/market/instruments")
def get_v1_instruments(query: Optional[str] = None):
    inst_mgr = get_instrument_manager()
    if query:
        return inst_mgr.search(query)
    return inst_mgr.get_all()


@v1_router.get("/market/breadth")
def get_v1_market_breadth():
    from app.services.market_data import get_market_breadth
    return get_market_breadth()


@v1_router.get("/market/history/{symbol}/indicators")
@v1_router.get("/market/history/{symbol}/package")
def get_v1_history_package(
    symbol: str,
    timeframe: str = Query(default="1h", description="Timeframe: 1m, 5m, 15m, 30m, 1h, 1D, 1wk, 1mo"),
    count: int = Query(default=60, ge=1, le=1000, description="Number of candle bars"),
):
    """
    Fetch dynamic historical candle package enriched with comprehensive indicators
    (SMA, EMA, RSI, MACD, Bollinger Bands, ATR, Supertrend, Stochastic, Pivots, Regime).
    """
    manager = get_market_data_manager()
    tf_clean = timeframe if isinstance(timeframe, str) else "1h"
    cnt_clean = count if isinstance(count, int) else 60
    return manager.get_historical_candles_package(symbol, timeframe=tf_clean, count=cnt_clean)


@v1_router.get("/market/history/{symbol}")
def get_v1_history(
    symbol: str,
    timeframe: str = Query(default="1h", description="Timeframe: 1m, 5m, 15m, 30m, 1h, 1D, 1wk, 1mo"),
    count: int = Query(default=60, ge=1, le=1000, description="Number of candle bars"),
    format: Optional[str] = Query(default=None, description="'full' for package with indicators, 'list' for plain array"),
):
    """
    Fetch dynamic historical OHLCV candlestick bars.
    Returns enriched bars with technical overlays (SMA, EMA, Bollinger Bands, VWAP).
    Pass format=full or format=package to receive the complete indicator summary.
    """
    manager = get_market_data_manager()
    tf_clean = timeframe if isinstance(timeframe, str) else "1h"
    cnt_clean = count if isinstance(count, int) else 60
    package = manager.get_historical_candles_package(symbol, timeframe=tf_clean, count=cnt_clean)

    if format in ["full", "package", "dict"]:
        return package
    return package["candles"]


@v1_router.get("/market/feed-health")
def get_v1_feed_health():
    manager = get_market_data_manager()
    health = manager.get_feed_health()
    health["data_quality"] = manager.get_data_quality()
    return health


@v1_router.get("/market/status")
def get_v1_market_status():
    manager = get_market_data_manager()
    return manager.get_market_status()


@v1_router.get("/market/macro")
def get_v1_macro():
    """Return macro-economic indicators. USD/INR is fetched live from Yahoo Finance."""
    return get_macro_indicators()


@v1_router.get("/market/news")
def get_v1_news():
    """Return live market news headlines from Yahoo Finance (cached 5 min)."""
    return get_news_feed()


@v1_router.get("/market/indices")
def get_v1_indices():
    """Return live Indian indices: NIFTY 50, NIFTY BANK, SENSEX, INDIA VIX, GOLD, SILVER."""
    return get_indian_indices()


@v1_router.get("/market/breadth")
def get_v1_breadth():
    """Return advance/decline breadth from live quotes."""
    return get_market_breadth()


@v1_router.get("/market/most-active")
def get_v1_most_active():
    """Return top gainers, losers, and most active by volume."""
    return get_most_active_stocks()


@v1_router.get("/market/us/indices")
def get_v1_us_indices():
    """Return live US benchmark indices: NASDAQ 100, S&P 500, DOW JONES, US VIX."""
    from app.services.market_data import get_us_indices
    return get_us_indices()


@v1_router.get("/market/us/quotes")
def get_v1_us_quotes(symbols: Optional[str] = Query(default=None, description="Comma-separated US tickers")):
    """Return live quotes for US equities and ETFs (e.g., AAPL, MSFT, NVDA, SPY, QQQ)."""
    from app.services.market_data import get_us_quotes
    symbol_list = [s.strip().upper() for s in symbols.split(",")] if symbols else None
    return get_us_quotes(symbol_list)


@v1_router.get("/market/international/instruments")
def get_v1_international_instruments():
    """Return catalog of supported international and US instruments."""
    from app.services.market_data import get_international_instruments
    return get_international_instruments()


@v1_router.get("/market/quality")
def get_v1_market_quality(symbol: Optional[str] = Query(default=None, description="Optional symbol to inspect data quality")):
    """
    Return real-time data quality metrics, tick age, latency, and AI safety status.
    If 'symbol' is provided, evaluates that symbol; otherwise returns global feed health.
    """
    manager = get_market_data_manager()
    clean_sym = symbol if isinstance(symbol, str) else None
    return manager.get_data_quality(clean_sym)


@v1_router.get("/market/analysis/{symbol}")
def get_v1_market_analysis(symbol: str):
    """
    Return comprehensive multi-timeframe market analysis across Daily (HTF), Hourly (ITF),
    and 15m (LTF) horizons with confluence scoring and safety boundaries.
    """
    from app.services.multi_timeframe_engine import run_symbol_multi_timeframe_analysis
    clean_sym = symbol.upper().replace(".NS", "").replace(".BO", "").strip()
    return run_symbol_multi_timeframe_analysis(clean_sym)


@v1_router.get("/market/scanner", response_model=List[ScannerResult])
def get_v1_market_scanner(
    category: str = Query(default="ALL", description="Scanner category: ALL, BREAKOUT, MOMENTUM, RSI, MACD, CANDLESTICK, GAINER, LOSER"),
    market: Optional[str] = Query(default=None, description="Market filter: IN (India) or US (United States)"),
    min_confidence: int = Query(default=60, ge=0, le=100, description="Minimum confidence filter (0-100)"),
    timeframe: str = Query(default="1h", description="Timeframe: 1m, 5m, 15m, 1h, 1D"),
):
    """
    Real-time Live Market Scanner & Pattern Detection:
    Scans live market feeds for breakouts, reversals, candlestick patterns, and momentum across Indian & US tickers.
    """
    return scan_market(
        filter_category=category,
        market_filter=market,
        min_confidence=min_confidence,
        timeframe=timeframe,
    )


@v1_router.websocket("/market/stream")
@v1_router.websocket("/market-stream")
async def market_stream_websocket(websocket: WebSocket):
    ws_mgr = get_websocket_manager()
    await ws_mgr.connect(websocket)
    manager = get_market_data_manager()

    try:
        # Send initial snapshot of live quotes, status, and data quality (instant from cache or core symbols)
        if manager._cached_quotes:
            snapshot = list(manager._cached_quotes.values())
        else:
            snapshot = manager.get_quotes(["NIFTY 50", "RELIANCE", "TCS", "INFY", "HDFCBANK", "ICICIBANK", "AAPL"])

        status = manager.get_market_status()
        quality = manager.get_data_quality()
        await websocket.send_json({
            "type": "SNAPSHOT",
            "market_status": status,
            "data_quality": quality,
            "quotes": snapshot,
        })

        while True:
            raw_msg = await websocket.receive_text()
            await ws_mgr.handle_client_message(websocket, raw_msg)
    except (WebSocketDisconnect, RuntimeError):
        await ws_mgr.disconnect(websocket)
