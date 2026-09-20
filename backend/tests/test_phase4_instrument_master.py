"""
Phase 4 Instrument Master Tests — TradePilot AI

Validates:
  1. Unified catalog contains both Indian (NSE/BSE) and US (NASDAQ/NYSE) instruments
  2. Currency bindings: INR (₹) for Indian instruments, USD ($) for US instruments
  3. Timezone bindings: Asia/Kolkata for Indian, America/New_York for US
  4. Lookups with exchange prefixes (NSE:RELIANCE, NASDAQ:AAPL, NYSE:SPY, BSE:SENSEX)
  5. Global search by symbol, company name, exchange, and country
  6. Filtered search by market region ('IN' vs 'US')
  7. API route endpoints (/api/v1/market/instruments, /api/v1/market/instruments/search, /api/v1/market/instruments/{symbol})
"""
import unittest
from app.services.instrument_master import (
    get_all_instruments,
    get_instrument_by_symbol,
    search_instruments,
    search_instruments_advanced,
    get_instruments_by_market,
    get_instruments_by_exchange,
    get_us_symbols,
)
from app.services.market_data.instrument_manager import get_instrument_manager
from app.api.routes.v1_instruments import list_instruments, search_stocks, get_instrument_details


class TestPhase4InstrumentMaster(unittest.TestCase):
    def test_catalog_composition(self):
        catalog = get_all_instruments()
        self.assertGreaterEqual(len(catalog), 50)

        # Check Indian instruments presence
        rel = next((i for i in catalog if i["symbol"] == "RELIANCE"), None)
        self.assertIsNotNone(rel)
        self.assertEqual(rel["market"], "IN")
        self.assertEqual(rel["currency"], "INR")
        self.assertEqual(rel["currency_symbol"], "₹")
        self.assertEqual(rel["country"], "India")
        self.assertEqual(rel["timezone"], "Asia/Kolkata")

        # Check US instruments presence
        aapl = next((i for i in catalog if i["symbol"] == "AAPL"), None)
        self.assertIsNotNone(aapl)
        self.assertEqual(aapl["market"], "US")
        self.assertEqual(aapl["currency"], "USD")
        self.assertEqual(aapl["currency_symbol"], "$")
        self.assertEqual(aapl["country"], "United States")
        self.assertEqual(aapl["timezone"], "America/New_York")
        self.assertEqual(aapl["exchange"], "NASDAQ")

    def test_instrument_manager_lookups_and_prefixes(self):
        mgr = get_instrument_manager()

        # Plain symbol lookups
        self.assertIsNotNone(mgr.get_instrument("RELIANCE"))
        self.assertIsNotNone(mgr.get_instrument("AAPL"))
        self.assertIsNotNone(mgr.get_instrument("NVDA"))
        self.assertIsNotNone(mgr.get_instrument("SPY"))

        # Prefixed lookups
        self.assertEqual(mgr.get_instrument("NSE:RELIANCE")["symbol"], "RELIANCE")
        self.assertEqual(mgr.get_instrument("NASDAQ:AAPL")["symbol"], "AAPL")
        self.assertEqual(mgr.get_instrument("NYSE:SPY")["symbol"], "SPY")
        self.assertEqual(mgr.get_instrument("NASDAQ:NVDA")["symbol"], "NVDA")
        self.assertEqual(mgr.get_instrument("BSE:SENSEX")["symbol"], "SENSEX")

        # Suffix lookups
        self.assertEqual(mgr.get_instrument("RELIANCE.NS")["symbol"], "RELIANCE")

    def test_global_search(self):
        # Search by symbol
        res_aapl = search_instruments("AAPL")
        self.assertTrue(any(i["symbol"] == "AAPL" for i in res_aapl))

        # Search by company name
        res_apple = search_instruments("Apple")
        self.assertTrue(any(i["symbol"] == "AAPL" for i in res_apple))

        # Search Indian company
        res_tata = search_instruments("Tata")
        self.assertTrue(any(i["symbol"] in ["TCS", "TATAMOTORS"] for i in res_tata))

        # Search by country
        res_us = search_instruments("United States")
        self.assertGreaterEqual(len(res_us), 10)

    def test_advanced_filtering(self):
        us_only = search_instruments_advanced(market="US")
        self.assertTrue(all(i["market"] == "US" for i in us_only))
        self.assertGreaterEqual(len(us_only), 15)

        in_only = search_instruments_advanced(market="IN")
        self.assertTrue(all(i["market"] == "IN" for i in in_only))
        self.assertGreaterEqual(len(in_only), 30)

        nasdaq_only = search_instruments_advanced(exchange="NASDAQ")
        self.assertTrue(all(i["exchange"] == "NASDAQ" for i in nasdaq_only))

    def test_api_routes(self):
        # 1. list_instruments route
        res_list = list_instruments(market="US", limit=10)
        self.assertLessEqual(len(res_list.instruments), 10)
        self.assertTrue(all(i.market == "US" for i in res_list.instruments))

        # 2. search_stocks route
        search_res = search_stocks(q="Microsoft")
        self.assertGreaterEqual(search_res.total_found, 1)
        self.assertEqual(search_res.results[0].symbol, "MSFT")
        self.assertEqual(search_res.results[0].currency, "USD")
        self.assertEqual(search_res.results[0].currency_symbol, "$")

        # 3. get_instrument_details route
        detail = get_instrument_details("NVDA")
        self.assertEqual(detail.symbol, "NVDA")
        self.assertEqual(detail.exchange, "NASDAQ")
        self.assertEqual(detail.market, "US")


if __name__ == "__main__":
    unittest.main()
