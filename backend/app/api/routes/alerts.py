from typing import List, Dict, Any
from fastapi import APIRouter, Depends

from app.api.routes.portfolio import manager
from app.services.trade_manager import TradeManager
from app.schemas.trade import AlertCreateRequest

router = APIRouter(prefix="/alerts", tags=["alerts"])


@router.get("")
def get_alerts(trade_manager: TradeManager = Depends(manager)):
    return trade_manager.store.alerts


@router.post("", status_code=201)
def create_alert(req: AlertCreateRequest, trade_manager: TradeManager = Depends(manager)):
    trade_manager.store.add_alert(
        alert_type=req.alert_type,
        message=f"{req.alert_type} trigger set for {req.symbol} at {req.target_value}. {req.notes or ''}".strip(),
        symbol=req.symbol.upper(),
        severity=req.severity or "yellow",
    )
    return {"status": "created", "alert": trade_manager.store.alerts[0]}


@router.post("/{alert_id}/read")
def mark_read(alert_id: str, trade_manager: TradeManager = Depends(manager)):

    with trade_manager.store._lock:
        for alert in trade_manager.store.alerts:
            if alert.id == alert_id:
                alert.read = True
                break
    return {"status": "ok"}


@router.post("/clear")
def clear_all(trade_manager: TradeManager = Depends(manager)):
    with trade_manager.store._lock:
        trade_manager.store.alerts.clear()
    return {"status": "ok"}
