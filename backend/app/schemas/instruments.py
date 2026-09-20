"""
Instrument Master Schemas — TradePilot AI
Provides data models for multi-market stock searching, instrument details, and regional metadata.
"""
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class InstrumentMetadata(BaseModel):
    symbol: str
    company_name: str
    exchange: str
    segment: str
    sector: str
    country: str
    currency: str
    currency_symbol: str
    timezone: str
    market: str  # "IN" or "US"
    tick_size: float = 0.05
    lot_size: int = 1
    isin: Optional[str] = None
    instrument_token: Optional[int] = None
    market_status: Optional[str] = None


class InstrumentSearchResult(BaseModel):
    symbol: str
    company_name: str
    exchange: str
    country: str
    currency: str
    currency_symbol: str
    market: str
    sector: str
    segment: str
    market_status: Optional[str] = None


class InstrumentSearchResponse(BaseModel):
    query: str
    total_found: int
    results: List[InstrumentSearchResult]


class InstrumentListResponse(BaseModel):
    total_count: int
    market: Optional[str] = None
    exchange: Optional[str] = None
    instruments: List[InstrumentMetadata]
