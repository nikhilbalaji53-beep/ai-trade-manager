from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException

from app.api.routes.portfolio import manager
from app.schemas.trade import CloseTradeRequest, PositionResponse, TradeRequest
from app.services.trade_manager import TradeManager

router = APIRouter(prefix="/trades", tags=["trades"])


@router.post("", response_model=PositionResponse, status_code=201)
def create_trade(payload: TradeRequest, trade_manager: TradeManager = Depends(manager)):
    try:
        return trade_manager.open_trade(
            symbol=payload.symbol,
            side=payload.side,
            quantity=payload.quantity,
            order_type=payload.order_type,
            price=payload.price,
            stop_loss=payload.stop_loss,
            take_profit=payload.take_profit,
            trailing_stop_pct=payload.trailing_stop_pct,
            max_loss=payload.max_loss,
            broker=payload.broker or "ZERODHA_KITE",
            strategy=payload.strategy or "User Trade Config",
        )
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error


@router.delete("/{symbol}")
def close_trade(symbol: str, payload: Optional[CloseTradeRequest] = None, trade_manager: TradeManager = Depends(manager)):
    try:
        qty = payload.quantity if payload else None
        reason = payload.reason if payload and payload.reason else "MANUAL"
        return trade_manager.close_trade(symbol, quantity=qty, reason=reason)
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error


@router.post("/close-all")
def close_all_trades(trade_manager: TradeManager = Depends(manager)):
    return trade_manager.close_all_positions(reason="PANIC_CLOSE")


@router.get("/orders")
def get_orders(trade_manager: TradeManager = Depends(manager)):
    _, _, _, orders = trade_manager.store.snapshot()
    return orders
