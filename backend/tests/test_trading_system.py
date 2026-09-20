import unittest
from app.database import get_store
from app.services.instrument_master import get_all_instruments, get_instrument_by_symbol, search_instruments
from app.services.market_data import (
    get_quotes,
    generate_historical_candles,
    get_order_book_depth,
    get_indian_indices,
    get_market_breadth,
    get_most_active_stocks,
)
from app.services.feature_engineering import extract_all_features, compute_rsi, compute_macd, compute_bollinger_bands
from app.services.ml_engine import get_ml_prediction, get_sentiment_analytics
from app.services.market_scanner import scan_market
from app.services.backtesting_engine import run_strategy_backtest
from app.services.trade_manager import TradeManager
from app.services.risk_engine import assess_portfolio
from app.services.indian_brokerage import calculate_indian_charges
from app.services.trailing_stop import evaluate_profit_protection_step, evaluate_ai_trade_manager
from app.services.data_validation import get_validator
from app.services.broker_connector import get_broker_connector


class TestIndianTradingSystem(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from app.services.market_data.market_data_manager import get_market_data_manager
        mgr = get_market_data_manager()
        mgr.initialize()

    def test_instrument_master_catalog(self):
        instruments = get_all_instruments()
        self.assertGreaterEqual(len(instruments), 10)
        rel = get_instrument_by_symbol("RELIANCE")
        self.assertIsNotNone(rel)
        self.assertEqual(rel["instrument_token"], 738561)
        self.assertEqual(rel["isin"], "INE002A01018")
        self.assertEqual(rel["segment"], "EQ")

        search_res = search_instruments("Tata")
        self.assertTrue(any(i["symbol"] in ["TCS", "TATAMOTORS"] for i in search_res))

    def test_indian_market_quotes_and_breadth(self):
        quotes = get_quotes()
        self.assertIsInstance(quotes, list)
        breadth = get_market_breadth()
        self.assertIn("advancers", breadth)
        self.assertIn("decliners", breadth)

        active = get_most_active_stocks()
        self.assertIn("most_active_turnover", active)
        self.assertIn("top_gainers", active)

    def test_multi_timeframe_historical_candles_and_pivots(self):
        bars = generate_historical_candles("RELIANCE", "1h", 30)
        self.assertIsInstance(bars, list)
        if bars:
            self.assertIn("open", bars[0])
            self.assertIn("close", bars[0])
            tech = extract_all_features("RELIANCE", bars)
            self.assertIn("pivot", tech)
            self.assertIn("r1", tech)
            self.assertIn("s1", tech)

    def test_ml_ensemble_prediction_models(self):
        pred = get_ml_prediction("RELIANCE")
        self.assertEqual(pred["symbol"], "RELIANCE")
        self.assertIn(pred["direction"], ["UP", "DOWN", "SIDEWAYS"])
        self.assertTrue("data_source" in pred or "status" in pred)

    def test_indian_statutory_taxes_and_brokerage(self):
        charges = calculate_indian_charges(
            side="BUY",
            quantity=50,
            entry_price=2920.00,
            exit_price=2985.00,
            trade_type="INTRADAY",
            exchange="NSE",
        )
        self.assertEqual(charges["gross_pnl"], 3250.00)
        self.assertGreater(charges["brokerage"], 0)
        self.assertGreater(charges["stt"], 0)
        self.assertGreater(charges["exchange_charges"], 0)
        self.assertGreater(charges["gst"], 0)
        self.assertGreater(charges["net_pnl"], 0)

    def test_dual_manager_branching_and_ai_decisions(self):
        # 1. Profit Manager Branch
        profit_eval = evaluate_ai_trade_manager(
            side="BUY",
            entry_price=1000.0,
            current_price=1040.0,
            stop_loss=950.0,
            trailing_stop=950.0,
            take_profit=1100.0,
            highest_price=1040.0,
            lowest_price=1000.0,
        )
        self.assertEqual(profit_eval["branch"], "PROFIT_MANAGER")
        self.assertEqual(profit_eval["new_stop"], 1020.0)

        # 2. Loss Manager Branch
        loss_eval = evaluate_ai_trade_manager(
            side="BUY",
            entry_price=1000.0,
            current_price=980.0,
            stop_loss=950.0,
            trailing_stop=950.0,
            take_profit=1100.0,
            highest_price=1000.0,
            lowest_price=980.0,
        )
        self.assertEqual(loss_eval["branch"], "LOSS_MANAGER")
        self.assertIn(loss_eval["decision"], ["HOLD", "RECOVER_WATCH"])

    def test_7step_validation_pipeline_and_broker_gateway(self):
        validator = get_validator()
        raw_tick = {
            "symbol": "RELIANCE",
            "price": 2985.40,
            "open": 2920.00,
            "high": 2995.00,
            "low": 2915.00,
            "previous_close": 2920.00,
            "volume": 6800000,
        }
        ok, normalized, msg = validator.process_incoming_tick(raw_tick)
        self.assertTrue(ok)
        self.assertEqual(normalized["instrument_token"], 738561)
        self.assertEqual(normalized["isin"], "INE002A01018")

        # Multi-broker connector test
        for broker in ["ZERODHA_KITE", "UPSTOX_API", "ANGEL_ONE", "FYERS_API", "SHOONYA_FINVASIA", "DHAN_HQ", "PAPER_BROKER"]:
            conn = get_broker_connector(broker)
            res = conn.place_order("RELIANCE", "BUY", 10, "MARKET", 2985.40)
            self.assertEqual(res["broker"], broker)
            self.assertEqual(res["status"], "FILLED")


if __name__ == "__main__":
    unittest.main()
