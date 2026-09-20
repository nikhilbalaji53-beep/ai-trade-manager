"""
Phase 2 Architecture & Contract Tests — TradePilot AI

Validates:
  1. get_supported_markets() returns multi-market definitions (India & US) with timezones, currencies, and session status
  2. get_market_region() resolves valid regions ('IN', 'US') and rejects invalid ones
  3. predict_trade_pnl() produces probabilistic predictions (profit/loss prob, pnl range, risk score, confidence)
  4. get_trade_plan() produces structured trade plan (entry zone, SL, targets, buy conditions, do not buy conditions)
  5. get_paper_account() returns virtual account metrics (starting capital, cash, buying power)
  6. reset_paper_account() allows configuring virtual starting capital
  7. get_paper_pnl() returns real-time paper P&L summary
  8. Strict safety rule: mandatory probabilistic disclaimer present on all AI outputs; zero guaranteed profit claims
"""
import unittest
from fastapi import HTTPException

from app.api.routes.v1_markets import get_supported_markets, get_market_region
from app.api.routes.v1_ai import predict_trade_pnl, get_trade_plan, analyze_symbol
from app.api.routes.v1_paper import (
    get_paper_account,
    reset_paper_account,
    get_paper_positions,
    get_paper_orders,
    get_paper_pnl,
)
from app.schemas.ai import PnLPredictionRequest
from app.schemas.paper import PaperAccountResetRequest
from app.services.market_data.market_data_manager import get_market_data_manager


class TestPhase2Architecture(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        mgr = get_market_data_manager()
        mgr.initialize()

    def test_markets_endpoint(self):
        data = get_supported_markets()
        self.assertGreaterEqual(len(data.markets), 2)

        # Check India
        india = next((m for m in data.markets if m.id == "IN"), None)
        self.assertIsNotNone(india)
        self.assertEqual(india.primary_currency, "INR")
        self.assertEqual(india.default_timezone, "Asia/Kolkata")
        self.assertTrue(any(e.code == "NSE" for e in india.exchanges))

        # Check US
        us = next((m for m in data.markets if m.id == "US"), None)
        self.assertIsNotNone(us)
        self.assertEqual(us.primary_currency, "USD")
        self.assertEqual(us.currency_symbol, "$")
        self.assertEqual(us.default_timezone, "America/New_York")
        self.assertTrue(any(e.code == "NASDAQ" for e in us.exchanges))

    def test_market_region_by_id(self):
        res_in = get_market_region("IN")
        self.assertEqual(res_in.name, "India")

        res_us = get_market_region("US")
        self.assertEqual(res_us.name, "United States")

        with self.assertRaises(HTTPException):
            get_market_region("INVALID")

    def test_paper_account_endpoints(self):
        data = get_paper_account()
        self.assertTrue(data.is_paper_trading)
        self.assertGreater(data.starting_capital, 0)
        self.assertGreaterEqual(data.available_cash, 0)
        self.assertGreaterEqual(data.buying_power, 0)

        # Test account reset with custom capital
        reset_req = PaperAccountResetRequest(
            starting_capital=100000.0,
            currency="INR",
            clear_existing_positions=True
        )
        reset_data = reset_paper_account(reset_req)
        self.assertEqual(reset_data.starting_capital, 100000.0)
        self.assertEqual(reset_data.available_cash, 100000.0)

        # Test PnL summary
        pnl_data = get_paper_pnl()
        self.assertTrue(pnl_data.is_paper)
        self.assertIsNotNone(pnl_data.net_pnl)

        # Test orders & positions lists
        positions = get_paper_positions()
        self.assertIsInstance(positions, list)
        orders = get_paper_orders()
        self.assertIsInstance(orders, list)

    def test_ai_predict_pnl_contract_and_safety(self):
        req = PnLPredictionRequest(symbol="RELIANCE", direction="BUY", quantity=10.0)
        try:
            data = predict_trade_pnl(req)
            self.assertIsNotNone(data.profit_probability)
            self.assertIsNotNone(data.loss_probability)
            self.assertIsNotNone(data.expected_profit)
            self.assertIsNotNone(data.expected_loss)
            self.assertIsNotNone(data.expected_pnl_range)
            self.assertIsNotNone(data.confidence)
            self.assertIsNotNone(data.risk_score)
            self.assertIsNotNone(data.recommended_action)

            # Mandatory safety checks
            self.assertEqual(data.disclaimer, "AI predictions are probabilistic and do not guarantee future returns.")
            raw_str = str(data.model_dump())
            self.assertNotIn("100% Accuracy", raw_str)
            self.assertNotIn("Guaranteed Profit", raw_str)
            self.assertNotIn("Risk Free", raw_str)

            # Probability bounds
            self.assertGreaterEqual(data.profit_probability, 0.0)
            self.assertLessEqual(data.profit_probability, 1.0)
            self.assertGreaterEqual(data.loss_probability, 0.0)
            self.assertLessEqual(data.loss_probability, 1.0)
        except HTTPException as e:
            # If market feed is disconnected, it must return 503 rather than mock price
            self.assertEqual(e.status_code, 503)

    def test_ai_trade_plan_contract(self):
        try:
            data = get_trade_plan("RELIANCE")
            self.assertEqual(data.symbol, "RELIANCE")
            self.assertIsNotNone(data.entry_zone)
            self.assertIsNotNone(data.stop_loss)
            self.assertIsNotNone(data.target_1)
            self.assertIsNotNone(data.target_2)
            self.assertGreaterEqual(len(data.buy_conditions), 1)
            self.assertGreaterEqual(len(data.do_not_buy_conditions), 1)
            self.assertIsNotNone(data.trade_score)
            self.assertIsNotNone(data.decision)
            self.assertEqual(data.disclaimer, "AI predictions are probabilistic and do not guarantee future returns.")
        except HTTPException as e:
            self.assertEqual(e.status_code, 503)


if __name__ == "__main__":
    unittest.main()
