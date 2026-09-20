from typing import Dict, Any
from fastapi import APIRouter, Depends, HTTPException

from app.config import get_settings
from app.database import get_store
from app.schemas.trade import (
    PortfolioResponse,
    RiskResponse,
    RiskSettingsUpdateRequest,
    UpdatePositionLevelsRequest,
    PositionResponse,
)
from app.services.risk_engine import assess_portfolio
from app.services.trade_manager import TradeManager

router = APIRouter(prefix="/portfolio", tags=["portfolio"])


def manager() -> TradeManager:
    settings = get_settings()
    return TradeManager(get_store(settings.starting_capital))


@router.get("", response_model=PortfolioResponse)
def portfolio(trade_manager: TradeManager = Depends(manager)):
    return trade_manager.portfolio()


@router.get("/risk", response_model=RiskResponse)
def risk(trade_manager: TradeManager = Depends(manager)):
    portfolio_data = trade_manager.portfolio()
    return assess_portfolio(
        cash=portfolio_data["cash"],
        starting_capital=portfolio_data["starting_capital"],
        positions=portfolio_data["positions"],
        risk_settings=trade_manager.store.risk_settings,
    )


@router.post("/risk/settings")
def update_risk_settings(req: RiskSettingsUpdateRequest, trade_manager: TradeManager = Depends(manager)):
    rs = trade_manager.store.risk_settings
    if req.max_portfolio_risk_pct is not None:
        rs.max_portfolio_risk_pct = req.max_portfolio_risk_pct
    if req.max_single_position_pct is not None:
        rs.max_single_position_pct = req.max_single_position_pct
    if req.max_daily_loss is not None:
        rs.max_daily_loss = req.max_daily_loss
    if req.default_stop_loss_pct is not None:
        rs.default_stop_loss_pct = req.default_stop_loss_pct
    if req.default_take_profit_pct is not None:
        rs.default_take_profit_pct = req.default_take_profit_pct
    if req.trailing_stop_enabled is not None:
        rs.trailing_stop_enabled = req.trailing_stop_enabled
    if req.auto_break_even_pct is not None:
        rs.auto_break_even_pct = req.auto_break_even_pct
    if req.kelly_fraction is not None:
        rs.kelly_fraction = req.kelly_fraction

    trade_manager.store.log_audit("SYSTEM_CONFIG", "INFO", "Risk settings updated.", {"updated_fields": req.model_dump(exclude_unset=True)})
    return {"status": "success", "message": "Risk settings updated successfully"}


@router.put("/positions/{symbol}/levels", response_model=PositionResponse)
def update_position_levels(symbol: str, req: UpdatePositionLevelsRequest, trade_manager: TradeManager = Depends(manager)):
    try:
        return trade_manager.update_position_levels(
            symbol=symbol,
            stop_loss=req.stop_loss,
            take_profit=req.take_profit,
            trailing_stop=req.trailing_stop,
        )
    except ValueError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
