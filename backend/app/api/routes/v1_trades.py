from typing import List, Dict, Any, Optional
from fastapi import APIRouter, HTTPException

from app.database import get_store
from app.config import get_settings
from app.services.trade_manager import TradeManager
from app.schemas.trade import OrderCreateRequest

v1_trades_router = APIRouter(prefix="/v1", tags=["v1-trades"])
settings = get_settings()


def get_tm() -> TradeManager:
    return TradeManager(get_store(settings.starting_capital))


@v1_trades_router.get("/positions")
def get_v1_positions():
    tm = get_tm()
    tm.evaluate_live_positions()
    portfolio = tm.portfolio()
    return {
        "positions": portfolio.get("positions", []),
        "open_positions_count": portfolio.get("open_positions_count", 0),
        "total_unrealized_pnl": portfolio.get("unrealized_pnl", 0.0),
    }


@v1_trades_router.get("/orders")
def get_v1_orders():
    tm = get_tm()
    return tm.store.orders


@v1_trades_router.get("/pnl")
def get_v1_pnl():
    tm = get_tm()
    tm.evaluate_live_positions()
    portfolio = tm.portfolio()
    return {
        "starting_capital": portfolio.get("starting_capital", 500000.0),
        "equity": portfolio.get("equity", 500000.0),
        "cash": portfolio.get("cash", 500000.0),
        "realized_pnl": portfolio.get("realized_pnl", 0.0),
        "unrealized_pnl": portfolio.get("unrealized_pnl", 0.0),
        "daily_pnl": portfolio.get("daily_pnl", 0.0),
        "total_pnl": portfolio.get("total_pnl", 0.0),
        "win_rate": portfolio.get("win_rate", 0.0),
        "profit_factor": portfolio.get("profit_factor", 0.0),
    }


@v1_trades_router.post("/trades/configure")
def configure_trade(req: OrderCreateRequest):
    tm = get_tm()
    try:
        pos = tm.open_trade(
            symbol=req.symbol,
            side=req.side,
            quantity=req.quantity,
            order_type=req.order_type,
            price=req.price,
            stop_loss=req.stop_loss,
            take_profit=req.take_profit,
            strategy=req.strategy,
            max_loss=req.max_loss,
            broker=req.broker,
        )
        return {
            "status": "APPROVED_AND_EXECUTED",
            "position": pos,
            "message": f"Trade configured and executed on NSE for {req.symbol}.",
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@v1_trades_router.post("/trading/paper-order")
def paper_order(req: OrderCreateRequest):
    req.broker = "PAPER_BROKER"
    return configure_trade(req)


@v1_trades_router.post("/trade-manager/evaluate")
def evaluate_trade_levels(req: Dict[str, Any]):
    """
    Phase 12: Dual-Manager AI Trade Manager Evaluation Endpoint.
    Directly evaluates a position or order parameters through the PROFIT MANAGER or LOSS MANAGER branch.
    """
    from app.services.trailing_stop import evaluate_ai_trade_manager

    symbol = req.get("symbol", "UNKNOWN").upper()
    side = req.get("side", "BUY").upper()
    entry_price = float(req.get("entry_price", 0.0))
    current_price = float(req.get("current_price", entry_price))
    stop_loss = float(req.get("stop_loss", entry_price * 0.975))
    trailing_stop = float(req.get("trailing_stop", stop_loss))
    take_profit = float(req.get("take_profit", entry_price * 1.05))
    take_profit_2 = float(req["take_profit_2"]) if req.get("take_profit_2") is not None else None
    highest_price = float(req.get("highest_price", max(entry_price, current_price)))
    lowest_price = float(req.get("lowest_price", min(entry_price, current_price)))
    quantity = float(req.get("quantity", 1.0))
    max_loss = float(req["max_loss"]) if req.get("max_loss") is not None else None

    eval_res = evaluate_ai_trade_manager(
        side=side,
        entry_price=entry_price,
        current_price=current_price,
        stop_loss=stop_loss,
        trailing_stop=trailing_stop,
        take_profit=take_profit,
        highest_price=highest_price,
        lowest_price=lowest_price,
        quantity=quantity,
        max_loss=max_loss,
        take_profit_2=take_profit_2,
    )

    return {
        "symbol": symbol,
        "branch": eval_res["branch"],
        "decision": eval_res["decision"],
        "pnl_state": eval_res["pnl_state"],
        "new_stop": eval_res["new_stop"],
        "new_high": eval_res["new_high"],
        "new_low": eval_res["new_low"],
        "detail": eval_res["detail"],
        "disclaimer": "AI predictions and management rules are probabilistic and do not guarantee future returns.",
    }


@v1_trades_router.get("/trade-manager/status")
def get_trade_manager_status():
    """
    Phase 12: Evaluates all open positions via Dual-Manager architecture,
    updating trailing ratchets and checking safety cutoffs.
    """
    tm = get_tm()
    tm.evaluate_live_positions()
    portfolio = tm.portfolio()
    return {
        "status": "ACTIVE",
        "open_positions": portfolio.get("positions", []),
        "open_positions_count": portfolio.get("open_positions_count", 0),
        "total_unrealized_pnl": portfolio.get("unrealized_pnl", 0.0),
        "disclaimer": "AI trade management actions are automated and probabilistic.",
    }


@v1_trades_router.post("/risk/kill-switch")
def emergency_kill_switch():
    """
    Phase 15: Emergency Kill Switch.
    Immediately liquidates all open positions and logs a panic square-off audit event.
    """
    tm = get_tm()
    results = tm.close_all_positions(reason="EMERGENCY_KILL_SWITCH")
    return {
        "status": "EXECUTED",
        "message": f"Kill switch triggered. Liquidated {len(results)} positions.",
        "results": results,
    }

