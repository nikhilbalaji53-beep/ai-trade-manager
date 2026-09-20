import asyncio
from typing import List, Optional
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query, HTTPException

from app.schemas.trade import (
    MarketQuote,
    OrderBookDepth,
    CandleBar,
    TechnicalIndicators,
    MacroIndicator,
    CorporateAction,
    ScannerResult,
)
from app.services.market_data import (
    get_quotes,
    get_price,
    get_current_live_price,
    generate_historical_candles,
    get_order_book_depth,
    get_macro_indicators,
    get_corporate_actions,
    get_indian_indices,
    get_market_breadth,
    get_most_active_stocks,
)
from app.services.instrument_master import get_all_instruments, search_instruments
from app.services.feature_engineering import extract_all_features
from app.services.market_scanner import scan_market

router = APIRouter(prefix="/market", tags=["market"])


@router.get("/instrument-master")
def instrument_master(query: Optional[str] = None):
    if query:
        return search_instruments(query)
    return get_all_instruments()


@router.get("/breadth")
def market_breadth():
    return get_market_breadth()


@router.get("/most-active")
def most_active():
    return get_most_active_stocks()


@router.get("/indices")
def indian_indices():
    return get_indian_indices()


@router.get("/quotes", response_model=List[MarketQuote])
def quotes():
    return get_quotes()


@router.get("/quote/{symbol}", response_model=MarketQuote)
def single_quote(symbol: str):
    quotes_list = get_quotes()
    quote = next((q for q in quotes_list if q["symbol"] == symbol.upper()), None)
    if not quote:
        from app.services.market_data.market_data_manager import get_market_data_manager
        mgr_quote = get_market_data_manager().get_quote(symbol)
        if mgr_quote:
            quote = mgr_quote
    if not quote:
        raise HTTPException(status_code=404, detail=f"Symbol {symbol} not found")
    return quote


from app.services.market_data.instrument_manager import get_instrument_manager


@router.get("/depth/{symbol}", response_model=OrderBookDepth)
def order_book_depth(symbol: str):
    inst = get_instrument_manager().get_instrument(symbol)
    if not inst:
        raise HTTPException(status_code=404, detail=f"Symbol {symbol} not supported")
    return get_order_book_depth(symbol)


@router.get("/history/{symbol}", response_model=List[CandleBar])
def historical_candles(
    symbol: str,
    timeframe: str = Query(default="1h", pattern="^(1m|3m|5m|15m|1h|1D)$"),
    count: int = Query(default=120, ge=10, le=500),
):
    inst = get_instrument_manager().get_instrument(symbol)
    if not inst:
        raise HTTPException(status_code=404, detail=f"Symbol {symbol} not supported")
    return generate_historical_candles(symbol, timeframe, count)


@router.get("/indicators/{symbol}", response_model=TechnicalIndicators)
def technical_indicators(symbol: str):
    bars = generate_historical_candles(symbol, "1h", 60)
    features = extract_all_features(symbol.upper(), bars)
    return features


@router.get("/scanner", response_model=List[ScannerResult])
def market_scanner(category: str = "ALL"):
    return scan_market(category)


@router.get("/macro", response_model=List[MacroIndicator])
def macro_indicators():
    return get_macro_indicators()


@router.get("/corporate-actions", response_model=List[CorporateAction])
def corporate_actions():
    return get_corporate_actions()


@router.websocket("/stream")
async def quote_stream(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            await websocket.send_json({
                "type": "QUOTES_UPDATE",
                "data": get_quotes(),
            })
            await asyncio.sleep(2)
    except (WebSocketDisconnect, RuntimeError):
        return
