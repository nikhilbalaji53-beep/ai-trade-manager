"""
24/7 Live Crypto & Bitcoin Market Data API Routes — TradePilot AI
Provides /api/v1/crypto/quotes, /api/v1/crypto/quote/{symbol},
/api/v1/crypto/candles/{symbol}, and /api/v1/crypto/instruments.
"""
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, HTTPException, Query, status

from app.services.market_data.crypto_provider import get_crypto_provider, CRYPTO_INSTRUMENT_CATALOG
from app.services.market_data.market_data_manager import MarketDataManager

crypto_router = APIRouter(prefix="/v1/crypto", tags=["v1-crypto"])


@crypto_router.get("/quotes", status_code=status.HTTP_200_OK)
def get_all_crypto_quotes():
    """
    Return real-time live quotes for all major 24/7 cryptocurrencies and Bitcoin.
    Updated every second directly from exchange order books.
    """
    provider = get_crypto_provider()
    quotes = provider.get_all_crypto_quotes()
    return {
        "market": "CRYPTO_24_7",
        "market_status": "LIVE_24_7",
        "is_24_7": True,
        "count": len(quotes),
        "quotes": quotes,
        "data": quotes,
    }


@crypto_router.get("/quote/{symbol}", status_code=status.HTTP_200_OK)
def get_single_crypto_quote(symbol: str):
    """
    Get live quote for a specific cryptocurrency (e.g. BTC, ETH, SOL, XRP).
    """
    provider = get_crypto_provider()
    quote = provider.get_quote(symbol)
    if not quote:
        raise HTTPException(status_code=404, detail=f"Crypto currency '{symbol}' not found in 24/7 catalog.")
    return quote


@crypto_router.get("/candles/{symbol}", status_code=status.HTTP_200_OK)
def get_crypto_candles(
    symbol: str,
    timeframe: Optional[str] = Query(default=None, description="Candle interval: 1m, 5m, 15m, 1h, 4h, 1D, 1W, 1M, 6M"),
    interval: Optional[str] = Query(default=None, description="Alias for timeframe"),
    limit: int = Query(default=60, ge=10, le=500, description="Number of historical bars")
):
    """
    Return 24/7 live candlestick data for crypto assets.
    """
    tf = interval or timeframe or "1h"
    provider = get_crypto_provider()
    candles = provider.get_crypto_candles(symbol, timeframe=tf, limit=limit)
    return {
        "symbol": symbol.upper(),
        "timeframe": tf,
        "count": len(candles),
        "candles": candles,
    }


@crypto_router.get("/instruments", status_code=status.HTTP_200_OK)
def get_crypto_instruments():
    """
    Return full metadata catalog of supported 24/7 cryptocurrencies.
    """
    return {
        "market": "CRYPTO_24_7",
        "trading_hours": "24 Hours / 7 Days Non-Stop",
        "instruments": list(CRYPTO_INSTRUMENT_CATALOG)
    }
