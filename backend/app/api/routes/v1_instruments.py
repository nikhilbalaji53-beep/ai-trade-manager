"""
Instrument Master API Routes — TradePilot AI

Endpoints:
  GET /api/v1/market/instruments
  GET /api/v1/market/instruments/{symbol}
  GET /api/v1/market/search
"""
from typing import List, Optional
from fastapi import APIRouter, HTTPException, Query

from app.schemas.instruments import (
    InstrumentMetadata,
    InstrumentSearchResult,
    InstrumentSearchResponse,
    InstrumentListResponse,
)
from app.services.market_data.instrument_manager import get_instrument_manager
from app.services.market_data.market_data_manager import get_market_data_manager

instruments_router = APIRouter(prefix="/v1/market", tags=["v1-instruments"])


@instruments_router.get("/instruments", response_model=InstrumentListResponse)
def list_instruments(
    market: Optional[str] = Query(default=None, description="Market region ('IN' or 'US')"),
    exchange: Optional[str] = Query(default=None, description="Exchange code ('NSE', 'BSE', 'NASDAQ', 'NYSE')"),
    segment: Optional[str] = Query(default=None, description="Segment ('EQ', 'ETF', 'INDICES', 'COMMODITIES')"),
    search: Optional[str] = Query(default=None, description="Search term for symbol or name"),
    limit: int = Query(default=100, ge=1, le=500),
):
    """Retrieve catalog of all supported instruments across Indian and International markets."""
    market_str = market if isinstance(market, str) else None
    exchange_str = exchange if isinstance(exchange, str) else None
    segment_str = segment if isinstance(segment, str) else None
    search_str = search if isinstance(search, str) else None
    limit_int = limit if isinstance(limit, int) else 100

    inst_mgr = get_instrument_manager()
    instruments = inst_mgr.search_advanced(
        query=search_str,
        market=market_str,
        exchange=exchange_str,
        segment=segment_str,
        limit=limit_int,
    )
    return InstrumentListResponse(
        total_count=len(instruments),
        market=market_str,
        exchange=exchange_str,
        instruments=[InstrumentMetadata(**i) for i in instruments],
    )


@instruments_router.get("/instruments/search", response_model=InstrumentSearchResponse)
@instruments_router.get("/search", response_model=InstrumentSearchResponse)
def search_stocks(q: str = Query(..., min_length=1, description="Symbol or company name to search")):
    """
    Global search for any Indian or US stock / ETF (Section 36).
    Examples: RELIANCE, TCS, INFY, AAPL, MSFT, NVDA, or company name.
    Returns: Symbol, Company, Exchange, Country, Currency, Market status.
    """
    q_str = q if isinstance(q, str) else ""
    inst_mgr = get_instrument_manager()
    data_mgr = get_market_data_manager()

    matches = inst_mgr.search(q_str)
    results = []

    # Get market status helper
    in_status = data_mgr.get_market_status().get("status", "CLOSED")
    us_status = "CLOSED"
    if data_mgr.international_provider:
        us_status = data_mgr.international_provider.get_market_status().get("status", "CLOSED")

    for item in matches[:25]:
        mkt = item.get("market", "IN")
        stat = in_status if mkt == "IN" else us_status
        results.append(
            InstrumentSearchResult(
                symbol=item["symbol"],
                company_name=item.get("company_name", item["symbol"]),
                exchange=item.get("exchange", "NSE"),
                country=item.get("country", "India"),
                currency=item.get("currency", "INR"),
                currency_symbol=item.get("currency_symbol", "₹"),
                market=mkt,
                sector=item.get("sector", "Equities"),
                segment=item.get("segment", "EQ"),
                market_status=stat,
            )
        )

    return InstrumentSearchResponse(
        query=q,
        total_found=len(results),
        results=results,
    )


@instruments_router.get("/instruments/{symbol}", response_model=InstrumentMetadata)
def get_instrument_details(symbol: str):
    """Retrieve detailed instrument metadata by symbol."""
    inst_mgr = get_instrument_manager()
    inst = inst_mgr.get_instrument(symbol)
    if not inst:
        raise HTTPException(
            status_code=404,
            detail={
                "error": "INSTRUMENT_NOT_FOUND",
                "symbol": symbol,
                "message": f"Instrument '{symbol}' not found in unified catalog.",
                "action": "Verify symbol name or query /api/v1/market/instruments/search.",
            },
        )
    return InstrumentMetadata(**inst)
