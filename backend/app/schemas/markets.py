"""
Market & Regional Exchange Schemas — TradePilot AI
Supports Indian (NSE, BSE) and International (NASDAQ, NYSE) markets.
"""
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class ExchangeDetails(BaseModel):
    code: str
    name: str
    country: str
    currency_symbol: str
    currency_code: str
    timezone: str
    regular_open_time: str
    regular_close_time: str
    is_open: bool
    session_status: str  # OPEN, CLOSED, PRE_OPEN, AFTER_HOURS, WEEKEND
    message: str


class MarketRegion(BaseModel):
    id: str  # "IN", "US", "GLOBAL"
    name: str
    primary_currency: str
    currency_symbol: str
    default_timezone: str
    exchanges: List[ExchangeDetails]
    benchmark_indices: List[str]
    tracked_instruments_count: int
    is_supported: bool = True


class MarketsListResponse(BaseModel):
    markets: List[MarketRegion]
    total_regions: int
    active_regions: int
    server_time_utc: str
