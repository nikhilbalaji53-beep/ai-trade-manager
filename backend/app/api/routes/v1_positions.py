from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field
from fastapi import APIRouter, HTTPException

from app.database import get_store
from app.config import get_settings
from app.services.trade_manager import TradeManager
from app.services.pnl_engine import position_summary

v1_pos_router = APIRouter(prefix="/v1", tags=["v1-positions-orders"])
settings = get_settings()


class PaperOrderRequest(BaseModel):
    symbol: str
    side: str = Field(..., description="BUY or SELL")
    quantity: float = Field(..., gt=0)
    order_type: str = Field(default="MARKET", description="MARKET or LIMIT")
    price: Optional[float] = None
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    trailing_stop_pct: Optional[float] = None
    max_loss: Optional[float] = None
    strategy: str = "Paper Trading Desk"


@v1_pos_router.get("/positions")
def get_v1_positions():
    store = get_store(settings.starting_capital)
    trade_mgr = TradeManager(store)
    trade_mgr.evaluate_live_positions()
    _, positions_map, _, _ = store.snapshot()
    return [position_summary(pos) for pos in positions_map.values()]


@v1_pos_router.get("/orders")
def get_v1_orders():
    store = get_store(settings.starting_capital)
    _, _, _, orders = store.snapshot()
    return [o.model_dump() for o in orders]


@v1_pos_router.get("/pnl")
def get_v1_pnl():
    store = get_store(settings.starting_capital)
    trade_mgr = TradeManager(store)
    trade_mgr.evaluate_live_positions()
    port = trade_mgr.portfolio()
    return {
        "starting_capital": settings.starting_capital,
        "cash": port["cash"],
        "equity": port["equity"],
        "margin_used": port["margin_used"],
        "realized_pnl": port["realized_pnl"],
        "unrealized_pnl": port["unrealized_pnl"],
        "daily_pnl": port["daily_pnl"],
        "total_pnl": round(port["realized_pnl"] + port["unrealized_pnl"], 2),
        "win_rate": port["win_rate"],
        "open_positions_count": len(port["positions"]),
    }


@v1_pos_router.get("/alerts")
def get_v1_alerts():
    store = get_store(settings.starting_capital)
    return store.alerts


@v1_pos_router.post("/trading/paper-order")
def create_paper_order(order: PaperOrderRequest):
    store = get_store(settings.starting_capital)
    trade_mgr = TradeManager(store)
    try:
        res = trade_mgr.open_trade(
            symbol=order.symbol,
            side=order.side.upper(),
            quantity=order.quantity,
            order_type=order.order_type.upper(),
            price=order.price,
            stop_loss=order.stop_loss,
            take_profit=order.take_profit,
            trailing_stop_pct=order.trailing_stop_pct,
            max_loss=order.max_loss,
            broker="PAPER_BROKER",
            strategy=order.strategy,
        )
        return {
            "status": "SUCCESS",
            "message": f"Paper trade order executed for {order.quantity} {order.symbol}",
            "trade": res,
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
