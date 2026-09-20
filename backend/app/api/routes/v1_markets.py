"""
Markets API Route — TradePilot AI
Returns multi-market information for Indian (NSE, BSE) and International (NASDAQ, NYSE) exchanges.
"""
from datetime import datetime, timezone
import zoneinfo
from fastapi import APIRouter, HTTPException

from app.schemas.markets import MarketsListResponse, MarketRegion, ExchangeDetails

markets_router = APIRouter(prefix="/v1", tags=["v1-markets"])


def _check_market_open(tz_name: str, open_time_str: str, close_time_str: str) -> tuple[bool, str, str]:
    """Check if market is currently in open regular session based on local exchange timezone."""
    try:
        tz = zoneinfo.ZoneInfo(tz_name)
    except Exception:
        tz = timezone.utc

    now = datetime.now(tz)
    weekday = now.weekday()  # 0=Monday, 6=Sunday

    if weekday >= 5:
        return False, "CLOSED", "Market is closed for the weekend."

    # Parse open/close times HH:MM
    open_h, open_m = map(int, open_time_str.split(":"))
    close_h, close_m = map(int, close_time_str.split(":"))

    open_dt = now.replace(hour=open_h, minute=open_m, second=0, microsecond=0)
    close_dt = now.replace(hour=close_h, minute=close_m, second=0, microsecond=0)

    if now < open_dt:
        return False, "PRE_OPEN", f"Session opens at {open_time_str} {tz_name}."
    elif now > close_dt:
        return False, "CLOSED", f"Session closed at {close_time_str} {tz_name}."
    else:
        return True, "OPEN", f"Regular trading session active until {close_time_str} {tz_name}."


@markets_router.get("/markets", response_model=MarketsListResponse)
def get_supported_markets():
    """List all supported market regions, exchanges, active hours, and currency configurations."""
    # 1. Indian Markets (NSE & BSE)
    is_nse_open, nse_status, nse_msg = _check_market_open("Asia/Kolkata", "09:15", "15:30")
    is_bse_open, bse_status, bse_msg = _check_market_open("Asia/Kolkata", "09:15", "15:30")

    india_region = MarketRegion(
        id="IN",
        name="India",
        primary_currency="INR",
        currency_symbol="₹",
        default_timezone="Asia/Kolkata",
        benchmark_indices=["NIFTY 50", "NIFTY BANK", "SENSEX", "INDIA VIX"],
        tracked_instruments_count=53,
        is_supported=True,
        exchanges=[
            ExchangeDetails(
                code="NSE",
                name="National Stock Exchange of India",
                country="India",
                currency_symbol="₹",
                currency_code="INR",
                timezone="Asia/Kolkata",
                regular_open_time="09:15",
                regular_close_time="15:30",
                is_open=is_nse_open,
                session_status=nse_status,
                message=nse_msg,
            ),
            ExchangeDetails(
                code="BSE",
                name="Bombay Stock Exchange",
                country="India",
                currency_symbol="₹",
                currency_code="INR",
                timezone="Asia/Kolkata",
                regular_open_time="09:15",
                regular_close_time="15:30",
                is_open=is_bse_open,
                session_status=bse_status,
                message=bse_msg,
            ),
        ],
    )

    # 2. US Markets (NASDAQ & NYSE)
    is_us_open, us_status, us_msg = _check_market_open("America/New_York", "09:30", "16:00")

    us_region = MarketRegion(
        id="US",
        name="United States",
        primary_currency="USD",
        currency_symbol="$",
        default_timezone="America/New_York",
        benchmark_indices=["NASDAQ 100", "S&P 500", "DOW JONES", "VIX"],
        tracked_instruments_count=25,
        is_supported=True,
        exchanges=[
            ExchangeDetails(
                code="NASDAQ",
                name="Nasdaq Stock Market",
                country="United States",
                currency_symbol="$",
                currency_code="USD",
                timezone="America/New_York",
                regular_open_time="09:30",
                regular_close_time="16:00",
                is_open=is_us_open,
                session_status=us_status,
                message=us_msg,
            ),
            ExchangeDetails(
                code="NYSE",
                name="New York Stock Exchange",
                country="United States",
                currency_symbol="$",
                currency_code="USD",
                timezone="America/New_York",
                regular_open_time="09:30",
                regular_close_time="16:00",
                is_open=is_us_open,
                session_status=us_status,
                message=us_msg,
            ),
        ],
    )

    markets = [india_region, us_region]
    active_cnt = sum(1 for m in markets if any(e.is_open for e in m.exchanges))

    return MarketsListResponse(
        markets=markets,
        total_regions=len(markets),
        active_regions=active_cnt,
        server_time_utc=datetime.now(timezone.utc).isoformat(),
    )


@markets_router.get("/markets/{region_id}", response_model=MarketRegion)
def get_market_region(region_id: str):
    """Retrieve detailed exchange status for a specific market region ('IN' or 'US')."""
    res = get_supported_markets()
    for m in res.markets:
        if m.id.upper() == region_id.upper():
            return m
    raise HTTPException(status_code=404, detail=f"Market region '{region_id}' not found. Supported: 'IN', 'US'")
