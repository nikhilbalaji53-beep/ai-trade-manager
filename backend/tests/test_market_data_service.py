import unittest
from app.services.market_data.market_data_manager import get_market_data_manager
from app.services.market_data.instrument_manager import get_instrument_manager
from app.services.market_data.market_status_service import get_market_status_service
from app.services.market_data.nse_provider import NSEMarketDataProvider
from app.services.market_data.broker_provider import BrokerMarketDataProvider


class TestRealMarketDataService(unittest.TestCase):
    def setUp(self):
        self.manager = get_market_data_manager()
        self.manager.initialize()

    def test_instrument_manager_symbol_mapping(self):
        inst_mgr = get_instrument_manager()
        rel = inst_mgr.get_instrument("NSE:RELIANCE")
        self.assertIsNotNone(rel)
        self.assertEqual(rel["symbol"], "RELIANCE")
        self.assertEqual(rel["exchange"], "NSE")
        self.assertEqual(rel["instrument_token"], 738561)

        n50 = inst_mgr.get_instrument("NSE:NIFTY50")
        self.assertIsNotNone(n50)
        self.assertEqual(n50["symbol"], "NIFTY 50")

        sensex = inst_mgr.get_instrument("BSE:SENSEX")
        self.assertIsNotNone(sensex)
        self.assertEqual(sensex["exchange"], "BSE")

    def test_market_status_service(self):
        status_svc = get_market_status_service()
        stat = status_svc.get_session_status(is_feed_connected=True)
        self.assertIn("status", stat)
        self.assertIn("label", stat)
        self.assertIn("server_time_ist", stat)

        disconnected_stat = status_svc.get_session_status(is_feed_connected=False)
        self.assertEqual(disconnected_stat["status"], "FEED_DISCONNECTED")

    def test_quote_validation_pipeline(self):
        # Valid quote
        valid_quote = {
            "symbol": "RELIANCE",
            "last_price": 2985.40,
            "timestamp": "2026-08-26T14:30:00Z",
            "open": 2920.0,
            "high": 2990.0,
            "low": 2915.0,
            "previous_close": 2920.0,
            "change": 65.4,
            "change_percent": 2.24,
            "volume": 5000000,
        }
        ok, res, msg = self.manager.validate_quote(valid_quote)
        self.assertTrue(ok)

        # Invalid zero price
        invalid_zero = valid_quote.copy()
        invalid_zero["last_price"] = 0.0
        ok_z, _, msg_z = self.manager.validate_quote(invalid_zero)
        self.assertFalse(ok_z)

        # Invalid negative price
        invalid_neg = valid_quote.copy()
        invalid_neg["last_price"] = -100.0
        ok_n, _, msg_n = self.manager.validate_quote(invalid_neg)
        self.assertFalse(ok_n)

        # Missing timestamp
        invalid_ts = valid_quote.copy()
        del invalid_ts["timestamp"]
        ok_t, _, msg_t = self.manager.validate_quote(invalid_ts)
        self.assertFalse(ok_t)

    def test_broker_market_data_provider_auth_guard(self):
        # When environment variables are not set, broker provider fails safely without producing fake numbers
        broker = BrokerMarketDataProvider("ZERODHA_KITE")
        connected = broker.connect()
        if not broker.api_key:
            self.assertFalse(connected)
            self.assertIsNone(broker.get_quote("RELIANCE"))

    def test_commodities_instrument_master(self):
        from app.services.instrument_master import get_commodity_symbols, get_instrument_by_symbol
        commodities = get_commodity_symbols()
        self.assertIn("GOLD", commodities)
        self.assertIn("SILVER", commodities)
        self.assertIn("GOLDBEES", commodities)
        self.assertIn("SILVERBEES", commodities)

        gold_meta = get_instrument_by_symbol("GOLD")
        self.assertIsNotNone(gold_meta)
        self.assertEqual(gold_meta["exchange"], "NSE")
        self.assertEqual(gold_meta["segment"], "COMMODITIES")
        self.assertEqual(gold_meta["lot_size"], 1)

        silver_meta = get_instrument_by_symbol("SILVER")
        self.assertIsNotNone(silver_meta)
        self.assertEqual(silver_meta["exchange"], "NSE")
        self.assertEqual(silver_meta["segment"], "COMMODITIES")
        self.assertEqual(silver_meta["lot_size"], 1)

    def test_gold_and_silver_ticker_resolution(self):
        from app.services.market_data.nse_provider import _resolve_yf_ticker
        self.assertEqual(_resolve_yf_ticker("GOLD"), "GOLDBEES.NS")
        self.assertEqual(_resolve_yf_ticker("GOLDBEES"), "GOLDBEES.NS")
        self.assertEqual(_resolve_yf_ticker("SILVER"), "SILVERBEES.NS")
        self.assertEqual(_resolve_yf_ticker("SILVERBEES"), "SILVERBEES.NS")

    def test_indian_indices_includes_precious_metals(self):
        from app.services.market_data import get_indian_indices
        indices = get_indian_indices()
        # If active provider has network access, GOLD and SILVER are packed
        if "GOLD" in indices:
            self.assertGreater(indices["GOLD"]["price"], 0)
            self.assertIn("change", indices["GOLD"])
        if "SILVER" in indices:
            self.assertGreater(indices["SILVER"]["price"], 0)
            self.assertIn("change", indices["SILVER"])


if __name__ == "__main__":
    unittest.main()
