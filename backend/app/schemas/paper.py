"""
Paper Trading Schemas — TradePilot AI

Contracts for virtual paper trading:
  - Starting virtual capital configuration / account mirroring
  - Paper orders, positions, and executions
  - Real-time paper P&L and metrics
  - Paper mode is explicitly labeled on all operations
"""
from typing import List, Optional, Dict, Any
from enum import Enum
from pydantic import BaseModel, Field


class PaperOrderSide(str, Enum):
    BUY = "BUY"
    SELL = "SELL"


class PaperOrderType(str, Enum):
    MARKET = "MARKET"
    LIMIT = "LIMIT"
    STOP_LIMIT = "STOP_LIMIT"


class PaperOrderStatus(str, Enum):
    PENDING = "PENDING"
    OPEN = "OPEN"
    FILLED = "FILLED"
    PARTIALLY_FILLED = "PARTIALLY_FILLED"
    CANCELLED = "CANCELLED"
    REJECTED = "REJECTED"


class PaperOrderCreateRequest(BaseModel):
    symbol: str = Field(..., min_length=1, max_length=20)
    exchange: Optional[str] = "NSE"
    side: PaperOrderSide
    quantity: float = Field(..., gt=0)
    order_type: PaperOrderType = PaperOrderType.MARKET
    price: Optional[float] = Field(default=None, gt=0)  # Required for LIMIT
    stop_loss: Optional[float] = Field(default=None, gt=0)
    target: Optional[float] = Field(default=None, gt=0)
    trailing_stop_pct: Optional[float] = Field(default=None, ge=0.1, le=25.0)
    notes: Optional[str] = "Paper Trade Execution"


class PaperOrderCancelRequest(BaseModel):
    order_id: str
    reason: Optional[str] = "User Cancelled"


class PaperOrderResponse(BaseModel):
    order_id: str
    symbol: str
    exchange: str
    side: str
    quantity: float
    price: float
    filled_price: Optional[float] = None
    order_type: str
    status: str
    slippage: float = 0.0
    commission: float = 0.0
    created_at: str
    filled_at: Optional[str] = None
    rejection_reason: Optional[str] = None
    notes: str = ""
    is_paper: bool = True


class PaperPositionResponse(BaseModel):
    symbol: str
    exchange: str
    side: str
    quantity: float
    entry_price: float
    current_price: float
    market_value: float
    unrealized_pnl: float
    pnl_percent: float
    stop_loss: float
    target: float
    trailing_stop: float
    risk_level: str
    opened_at: str
    updated_at: str
    currency_symbol: str = "₹"
    is_paper: bool = True


class PaperAccountResponse(BaseModel):
    account_id: str = "PAPER-MAIN-001"
    account_type: str = "PAPER_TRADING"
    is_paper_trading: bool = True
    starting_capital: float
    total_virtual_capital: float  # equity
    available_cash: float
    invested_value: float
    current_value: float
    realized_pnl: float
    unrealized_pnl: float
    daily_pnl: float
    total_return_pct: float
    win_rate: float
    total_trades_count: int
    open_positions_count: int
    margin_used: float
    buying_power: float
    currency: str = "INR"
    currency_symbol: str = "₹"
    last_updated: str


class PaperAccountResetRequest(BaseModel):
    starting_capital: float = Field(..., ge=1000.0, le=100_000_000.0)
    currency: Optional[str] = "INR"
    clear_existing_positions: bool = True


class PaperPnLSummary(BaseModel):
    total_equity: float
    cash: float
    starting_capital: float
    realized_pnl: float
    unrealized_pnl: float
    net_pnl: float
    total_return_pct: float
    total_fees_paid: float
    winning_trades_count: int
    losing_trades_count: int
    win_rate_pct: float
    profit_factor: float
    currency_symbol: str = "₹"
    is_paper: bool = True
    as_of: str
