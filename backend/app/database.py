from datetime import datetime, timezone
import uuid
from threading import Lock
from typing import Dict, List, Optional, Tuple, Any

from app.models.db_models import (
    PositionModel,
    OrderModel,
    TradeRecordModel,
    AuditLogModel,
    AlertNotificationModel,
)


class RiskSettings:
    def __init__(self):
        self.max_portfolio_risk_pct: float = 80.0
        self.max_single_position_pct: float = 30.0
        self.max_daily_loss: float = 15000.0  # ₹15,000 Max Daily Loss
        self.default_stop_loss_pct: float = 2.5
        self.default_take_profit_pct: float = 5.0
        self.trailing_stop_enabled: bool = True
        self.trailing_stop_distance_pct: float = 2.5
        self.auto_break_even_pct: float = 1.5
        self.require_stop_loss: bool = True
        self.kelly_fraction: float = 0.5


class PortfolioStore:
    def __init__(self, starting_capital: float = 500_000.0) -> None:  # ₹5 Lakhs INR
        self._lock = Lock()
        self.starting_capital: float = starting_capital
        self.cash: float = starting_capital
        self.positions: Dict[str, PositionModel] = {}
        self.orders: List[OrderModel] = []
        self.trades: List[TradeRecordModel] = []
        self.audit_logs: List[AuditLogModel] = []
        self.alerts: List[AlertNotificationModel] = []
        self.risk_settings = RiskSettings()
        self.system_status = {
            "automation_active": True,
            "trade_manager_active": True,
            "position_monitor_active": True,
            "broker_active": True,
            "active_broker": "ZERODHA_KITE",
            "exchange": "NSE/BSE",
            "websocket_active": True,
            "last_heartbeat": datetime.now(timezone.utc).isoformat(),
        }
        self._log_startup()

    def _log_startup(self):
        """
        Log system startup — no fake positions, trades, or market prices.
        The portfolio starts empty. Users must place real trades.
        """
        self.audit_logs = [
            AuditLogModel(
                id=str(uuid.uuid4())[:8],
                timestamp=datetime.now(timezone.utc).isoformat(),
                event_type="SYSTEM_BOOT",
                severity="INFO",
                message=(
                    "TradePilot initialized. Portfolio is empty — place real trades to begin. "
                    "Market data is sourced from the active market data provider."
                ),
                details={"exchange": "NSE/BSE", "data_source": "NSE_YFINANCE"},
            ),
        ]
        # NOTE: No positions, trades, orders, or alerts are seeded.
        # Fake pre-loaded data with hardcoded prices has been removed.
        # The application will display live data once the market data
        # provider establishes a connection.

    def snapshot(self) -> Tuple[float, Dict[str, PositionModel], List[TradeRecordModel], List[OrderModel]]:
        with self._lock:
            return (
                self.cash,
                {k: v for k, v in self.positions.items()},
                self.trades.copy(),
                self.orders.copy(),
            )

    def log_audit(self, event_type: str, severity: str, message: str, details: Optional[Dict[str, Any]] = None):
        with self._lock:
            log_item = AuditLogModel(
                id=str(uuid.uuid4())[:8],
                timestamp=datetime.now(timezone.utc).isoformat(),
                event_type=event_type,
                severity=severity,
                message=message,
                details=details or {},
            )
            self.audit_logs.insert(0, log_item)
            if len(self.audit_logs) > 200:
                self.audit_logs.pop()

    def add_alert(self, alert_type: str, message: str, symbol: Optional[str] = None, severity: str = "green"):
        with self._lock:
            alert = AlertNotificationModel(
                id=str(uuid.uuid4())[:8],
                type=alert_type,
                message=message,
                symbol=symbol,
                age="Just now",
                severity=severity,
                read=False,
            )
            self.alerts.insert(0, alert)
            if len(self.alerts) > 50:
                self.alerts.pop()


_store: Optional[PortfolioStore] = None


def get_store(starting_capital: float = 500_000.0) -> PortfolioStore:
    global _store
    if _store is None:
        _store = PortfolioStore(starting_capital)
    return _store
