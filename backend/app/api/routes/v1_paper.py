"""
Paper Trading API Routes — TradePilot AI

Implements Section 43 endpoints:
  GET  /api/v1/paper/account
  POST /api/v1/paper/account/reset
  GET  /api/v1/paper/positions
  GET  /api/v1/paper/orders
  POST /api/v1/paper/orders
  POST /api/v1/paper/orders/cancel
  GET  /api/v1/paper/pnl
"""
from datetime import datetime, timezone
import uuid
from typing import List, Optional
from fastapi import APIRouter, HTTPException, Query

from app.schemas.paper import (
    PaperAccountResponse,
    PaperAccountResetRequest,
    PaperOrderCreateRequest,
    PaperOrderResponse,
    PaperOrderCancelRequest,
    PaperPositionResponse,
    PaperPnLSummary,
)
from app.database import get_store
from app.services.trade_manager import TradeManager
from app.services.market_data import get_current_live_price
from app.config import get_settings

paper_router = APIRouter(prefix="/v1/paper", tags=["v1-paper"])


@paper_router.get("/account", response_model=PaperAccountResponse)
def get_paper_account():
    """Returns virtual paper trading account summary, cash, buying power, and metrics."""
    settings = get_settings()
    store = get_store(settings.starting_capital)
    tm = TradeManager(store)
    port = tm.portfolio()

    equity = port.get("equity", store.starting_capital)
    cash = port.get("cash", store.starting_capital)
    margin_used = port.get("margin_used", 0.0)
    invested = round(equity - cash, 2) if equity > cash else 0.0

    return PaperAccountResponse(
        account_id="PAPER-MAIN-001",
        account_type="PAPER_TRADING",
        is_paper_trading=True,
        starting_capital=store.starting_capital,
        total_virtual_capital=equity,
        available_cash=cash,
        invested_value=invested,
        current_value=equity,
        realized_pnl=port.get("realized_pnl", 0.0),
        unrealized_pnl=port.get("unrealized_pnl", 0.0),
        daily_pnl=port.get("daily_pnl", 0.0),
        total_return_pct=round(((equity - store.starting_capital) / store.starting_capital) * 100.0, 2) if store.starting_capital > 0 else 0.0,
        win_rate=port.get("win_rate", 0.0),
        total_trades_count=port.get("total_trades_count", 0),
        open_positions_count=port.get("open_positions_count", 0),
        margin_used=margin_used,
        buying_power=cash,
        currency="INR",
        currency_symbol="₹",
        last_updated=datetime.now(timezone.utc).isoformat(),
    )


@paper_router.post("/account/reset", response_model=PaperAccountResponse)
def reset_paper_account(req: PaperAccountResetRequest):
    """
    Configure virtual starting capital or mirror user's desired portfolio size
    (e.g., ₹10,000, ₹50,000, ₹1,00,000, ₹5,00,000 or custom).
    """
    store = get_store()
    with store._lock:
        store.starting_capital = req.starting_capital
        store.cash = req.starting_capital
        if req.clear_existing_positions:
            store.positions.clear()
            store.orders.clear()
            store.trades.clear()

    store.log_audit(
        "PAPER_ACCOUNT_RESET",
        "INFO",
        f"Paper trading account initialized with virtual capital ₹{req.starting_capital:,.2f}.",
        {"currency": req.currency, "cleared_positions": req.clear_existing_positions},
    )
    store.add_alert(
        "PAPER_ACCOUNT_CONFIGURED",
        f"Virtual paper account set to ₹{req.starting_capital:,.2f}.",
        severity="blue",
    )
    return get_paper_account()


@paper_router.get("/positions", response_model=List[PaperPositionResponse])
def get_paper_positions():
    """Retrieve all active open paper trading positions."""
    store = get_store()
    tm = TradeManager(store)
    # Refresh live evaluation against real market prices
    tm.evaluate_live_positions()

    positions = []
    for pos in store.positions.values():
        positions.append(
            PaperPositionResponse(
                symbol=pos.symbol,
                exchange="NSE",
                side=pos.side,
                quantity=pos.quantity,
                entry_price=pos.entry_price,
                current_price=pos.current_price,
                market_value=pos.market_value,
                unrealized_pnl=pos.unrealized_pnl,
                pnl_percent=pos.pnl_percent,
                stop_loss=pos.stop_loss,
                target=pos.take_profit,
                trailing_stop=pos.trailing_stop,
                risk_level=pos.risk_level,
                opened_at=pos.opened_at,
                updated_at=pos.updated_at,
                currency_symbol="₹",
                is_paper=True,
            )
        )
    return positions


@paper_router.get("/orders", response_model=List[PaperOrderResponse])
def get_paper_orders():
    """Retrieve paper order history."""
    store = get_store()
    orders = []
    for o in reversed(store.orders):
        orders.append(
            PaperOrderResponse(
                order_id=o.id,
                symbol=o.symbol,
                exchange="NSE",
                side=o.side,
                quantity=o.quantity,
                price=o.price,
                filled_price=o.filled_price,
                order_type=o.order_type,
                status=o.status,
                slippage=o.slippage,
                commission=o.commission,
                created_at=o.created_at,
                filled_at=o.filled_at,
                notes=o.notes,
                is_paper=True,
            )
        )
    return orders


@paper_router.post("/orders", response_model=PaperOrderResponse)
def place_paper_order(req: PaperOrderCreateRequest):
    """
    Simulate placing a paper order based on REAL live market price.
    Validates pre-trade risk engine before approving.
    """
    clean_sym = req.symbol.upper().replace(".NS", "").replace(".BO", "").strip()
    store = get_store()
    tm = TradeManager(store)

    try:
        trade_res = tm.open_trade(
            symbol=clean_sym,
            side=req.side.value,
            quantity=req.quantity,
            order_type=req.order_type.value,
            price=req.price,
            stop_loss=req.stop_loss,
            take_profit=req.target,
            trailing_stop_pct=req.trailing_stop_pct,
            broker="PAPER_BROKER",
            strategy=req.notes or "Manual Paper Trade",
        )
    except ValueError as e:
        # Create a rejected paper order record in audit book
        order_id = f"P-ORD-{uuid.uuid4().hex[:8].upper()}"
        rejected_ord = PaperOrderResponse(
            order_id=order_id,
            symbol=clean_sym,
            exchange=req.exchange or "NSE",
            side=req.side.value,
            quantity=req.quantity,
            price=req.price or 0.0,
            order_type=req.order_type.value,
            status="REJECTED",
            created_at=datetime.now(timezone.utc).isoformat(),
            rejection_reason=str(e),
            notes=f"Risk Engine Rejected: {e}",
            is_paper=True,
        )
        raise HTTPException(
            status_code=400,
            detail={
                "error": "PAPER_ORDER_REJECTED",
                "symbol": clean_sym,
                "reason": str(e),
                "order": rejected_ord.model_dump(),
            }
        )

    # Order was approved & filled
    order_data = trade_res.get("order", {})
    return PaperOrderResponse(
        order_id=order_data.get("id", f"P-ORD-{uuid.uuid4().hex[:8].upper()}"),
        symbol=clean_sym,
        exchange=req.exchange or "NSE",
        side=req.side.value,
        quantity=req.quantity,
        price=order_data.get("price", trade_res.get("entry_price", 0.0)),
        filled_price=order_data.get("filled_price", trade_res.get("entry_price", 0.0)),
        order_type=req.order_type.value,
        status="FILLED",
        slippage=order_data.get("slippage", 0.0),
        commission=order_data.get("commission", 0.0),
        created_at=order_data.get("created_at", datetime.now(timezone.utc).isoformat()),
        filled_at=order_data.get("filled_at", datetime.now(timezone.utc).isoformat()),
        notes=req.notes or "Simulated Execution at Real Market Price",
        is_paper=True,
    )


@paper_router.post("/orders/cancel")
def cancel_paper_order(req: PaperOrderCancelRequest):
    """Cancel an open/pending paper order."""
    store = get_store()
    with store._lock:
        target = next((o for o in store.orders if o.id == req.order_id), None)
        if not target:
            raise HTTPException(status_code=404, detail=f"Order '{req.order_id}' not found")
        if target.status in ["FILLED", "CANCELLED", "REJECTED"]:
            raise HTTPException(status_code=400, detail=f"Cannot cancel order in state '{target.status}'")
        target.status = "CANCELLED"
        target.notes = f"Cancelled: {req.reason}"

    store.log_audit("ORDER_CANCELLED", "INFO", f"Paper order {req.order_id} cancelled.", {"order_id": req.order_id})
    return {"status": "SUCCESS", "order_id": req.order_id, "message": "Paper order cancelled"}


@paper_router.get("/pnl", response_model=PaperPnLSummary)
def get_paper_pnl():
    """Retrieve detailed Real-Time Paper P&L Summary."""
    store = get_store()
    tm = TradeManager(store)
    port = tm.portfolio()

    equity = port.get("equity", store.starting_capital)
    cash = port.get("cash", store.starting_capital)
    realized = port.get("realized_pnl", 0.0)
    unrealized = port.get("unrealized_pnl", 0.0)
    net_pnl = round(realized + unrealized, 2)

    winning = sum(1 for t in store.trades if t.realized_pnl > 0)
    losing = sum(1 for t in store.trades if t.realized_pnl < 0)
    total_closed = len(store.trades)
    win_rate = round((winning / total_closed) * 100.0, 1) if total_closed > 0 else 0.0

    gross_profit = sum(t.realized_pnl for t in store.trades if t.realized_pnl > 0)
    gross_loss = abs(sum(t.realized_pnl for t in store.trades if t.realized_pnl < 0))
    profit_factor = round(gross_profit / gross_loss, 2) if gross_loss > 0 else (gross_profit if gross_profit > 0 else 0.0)

    total_fees = round(sum(o.commission for o in store.orders if o.status == "FILLED"), 2)

    return PaperPnLSummary(
        total_equity=equity,
        cash=cash,
        starting_capital=store.starting_capital,
        realized_pnl=realized,
        unrealized_pnl=unrealized,
        net_pnl=net_pnl,
        total_return_pct=round(((equity - store.starting_capital) / store.starting_capital) * 100.0, 2) if store.starting_capital > 0 else 0.0,
        total_fees_paid=total_fees,
        winning_trades_count=winning,
        losing_trades_count=losing,
        win_rate_pct=win_rate,
        profit_factor=profit_factor,
        currency_symbol="₹",
        is_paper=True,
        as_of=datetime.now(timezone.utc).isoformat(),
    )
