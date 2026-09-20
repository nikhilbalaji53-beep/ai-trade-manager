from datetime import datetime, timezone
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any


@dataclass
class PositionModel:
    symbol: str
    side: str  # BUY or SELL
    quantity: float
    entry_price: float
    current_price: float
    market_value: float = 0.0
    unrealized_pnl: float = 0.0
    pnl_percent: float = 0.0
    stop_loss: float = 0.0
    trailing_stop: float = 0.0
    take_profit: float = 0.0
    take_profit_2: Optional[float] = None
    risk_level: str = "Low"
    highest_price: float = 0.0
    lowest_price: float = 0.0
    break_even_activated: bool = False
    opened_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


@dataclass
class OrderModel:
    id: str
    symbol: str
    side: str
    order_type: str  # MARKET, LIMIT, STOP_LIMIT
    quantity: float
    price: float
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    trailing_stop_pct: Optional[float] = None
    status: str = "PENDING"  # PENDING, FILLED, PARTIALLY_FILLED, REJECTED, CANCELLED
    filled_price: Optional[float] = None
    slippage: float = 0.0
    commission: float = 1.50
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    filled_at: Optional[str] = None
    notes: str = ""


@dataclass
class TradeRecordModel:
    id: str
    symbol: str
    side: str
    quantity: float
    entry_price: float
    exit_price: float
    realized_pnl: float
    pnl_percent: float
    duration: str
    strategy: str
    exit_reason: str  # TAKE_PROFIT, STOP_LOSS, TRAILING_STOP, MANUAL, PANIC_CLOSE
    status: str = "CLOSED"
    opened_at: str = ""
    closed_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


@dataclass
class AuditLogModel:
    id: str
    timestamp: str
    event_type: str  # ORDER_PLACED, RISK_BREACH, STOP_TRIGGERED, POSITION_CLOSED, SYSTEM_CONFIG
    severity: str    # INFO, WARNING, ERROR, SUCCESS
    message: str
    details: Dict[str, Any] = field(default_factory=dict)


@dataclass
class AlertNotificationModel:
    id: str
    type: str
    message: str
    symbol: Optional[str] = None
    age: str = "Just now"
    severity: str = "green"  # green, amber, coral, blue
    read: bool = False
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
