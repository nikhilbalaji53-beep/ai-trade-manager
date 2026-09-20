from datetime import datetime, timezone, timedelta
from typing import Dict, Any


class MarketStatusService:
    """
    Evaluates real-time Indian Stock Market session status:
    - PRE_OPEN: 09:00 - 09:15 IST (Mon - Fri)
    - OPEN: 09:15 - 15:30 IST (Mon - Fri)
    - CLOSED: 15:30 - 09:00 IST / Weekends / Holidays
    - HALT
    - DATA_DELAYED
    - FEED_DISCONNECTED
    """

    # IST is UTC + 05:30
    IST_OFFSET = timedelta(hours=5, minutes=30)

    def get_ist_now(self) -> datetime:
        return datetime.now(timezone.utc) + self.IST_OFFSET

    def get_session_status(self, is_feed_connected: bool = True) -> Dict[str, Any]:
        if not is_feed_connected:
            return {
                "status": "FEED_DISCONNECTED",
                "label": "FEED DISCONNECTED",
                "is_trading_active": False,
                "message": "Market data provider is currently disconnected. Live updates paused.",
                "server_time_ist": self.get_ist_now().strftime("%Y-%m-%d %H:%M:%S IST"),
            }

        ist_now = self.get_ist_now()
        weekday = ist_now.weekday()  # 0=Monday, 6=Sunday
        hour = ist_now.hour
        minute = ist_now.minute
        time_minutes = hour * 60 + minute

        # Weekends (Saturday=5, Sunday=6)
        if weekday in [5, 6]:
            return {
                "status": "CLOSED",
                "label": "MARKET CLOSED (WEEKEND)",
                "is_trading_active": False,
                "message": "NSE / BSE regular trading session is closed for the weekend.",
                "server_time_ist": ist_now.strftime("%Y-%m-%d %H:%M:%S IST"),
            }

        # Pre-open session: 09:00 - 09:15 (540 to 555 minutes)
        if 540 <= time_minutes < 555:
            return {
                "status": "PRE_OPEN",
                "label": "PRE-OPEN SESSION",
                "is_trading_active": True,
                "message": "Order collection & price discovery session in progress.",
                "server_time_ist": ist_now.strftime("%Y-%m-%d %H:%M:%S IST"),
            }

        # Regular trading session: 09:15 - 15:30 (555 to 930 minutes)
        if 555 <= time_minutes <= 930:
            return {
                "status": "OPEN",
                "label": "NSE / BSE LIVE",
                "is_trading_active": True,
                "message": "Continuous trading active on NSE & BSE.",
                "server_time_ist": ist_now.strftime("%Y-%m-%d %H:%M:%S IST"),
            }

        # After hours / Market closed
        return {
            "status": "CLOSED",
            "label": "MARKET CLOSED",
            "is_trading_active": False,
            "message": "Trading session closed. Re-opens at 09:15 IST next trading day.",
            "server_time_ist": ist_now.strftime("%Y-%m-%d %H:%M:%S IST"),
        }


_market_status = MarketStatusService()


def get_market_status_service() -> MarketStatusService:
    return _market_status
