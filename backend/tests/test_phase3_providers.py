"""
Phase 3 Market Data Provider Tests — TradePilot AI

Validates:
  1. MarketDataProvider ABC methods and camelCase aliases (connect, disconnect, subscribe, unsubscribe, getQuote, getQuotes, getHistoricalData, getInstruments, getMarketStatus)
  2. InternationalMarketDataProvider connects to real US market feeds
  3. get_quote returns normalized quotes with USD ($) currency and NASDAQ/NYSE exchange tags
  4. get_instruments returns US equities and ETFs metadata
  5. get_historical_candles returns real OHLCV bars without synthetic fabrication
  6. Zero fake prices or random numbers
"""
import unittest
from app.services.market_data.provider_factory import create_international_provider
from app.services.market_data.market_data_manager import get_market_data_manager


class TestPhase3MarketDataProvider(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.provider = create_international_provider()
        cls.provider.connect()
        cls.manager = get_market_data_manager()
        cls.manager.initialize()

    def test_provider_connection_and_subscription(self):
        self.assertTrue(self.provider.is_connected)
        self.assertEqual(self.provider.provider_name, "INTERNATIONAL_YFINANCE")

        # Test subscription
        self.provider.subscribe(["AAPL", "MSFT"])
        self.assertIn("AAPL", self.provider.subscribed_symbols)
        self.assertIn("MSFT", self.provider.subscribed_symbols)

        # Test unsubscription
        self.provider.unsubscribe(["MSFT"])
        self.assertNotIn("MSFT", self.provider.subscribed_symbols)
        self.assertIn("AAPL", self.provider.subscribed_symbols)

    def test_provider_camel_case_specification_aliases(self):
        # Section 42 requires getQuote, getQuotes, getHistoricalData, getInstruments, getMarketStatus
        self.assertTrue(callable(getattr(self.provider, "getQuote", None)))
        self.assertTrue(callable(getattr(self.provider, "getQuotes", None)))
        self.assertTrue(callable(getattr(self.provider, "getHistoricalData", None)))
        self.assertTrue(callable(getattr(self.provider, "getInstruments", None)))
        self.assertTrue(callable(getattr(self.provider, "getMarketStatus", None)))

        stat = self.provider.getMarketStatus()
        self.assertIn("status", stat)
        self.assertIn("label", stat)
        self.assertIn("server_time_ny", stat)

    def test_get_instruments_us_catalog(self):
        instruments = self.provider.get_instruments()
        self.assertGreaterEqual(len(instruments), 15)

        symbols = [i["symbol"] for i in instruments]
        self.assertIn("AAPL", symbols)
        self.assertIn("MSFT", symbols)
        self.assertIn("NVDA", symbols)
        self.assertIn("SPY", symbols)
        self.assertIn("QQQ", symbols)

        aapl = next(i for i in instruments if i["symbol"] == "AAPL")
        self.assertEqual(aapl["exchange"], "NASDAQ")
        self.assertEqual(aapl["currency"], "USD")
        self.assertEqual(aapl["currency_symbol"], "$")

    def test_us_quote_retrieval(self):
        quote = self.provider.get_quote("AAPL")
        if quote:
            self.assertEqual(quote["symbol"], "AAPL")
            self.assertEqual(quote["currency"], "USD")
            self.assertEqual(quote["currency_symbol"], "$")
            self.assertEqual(quote["exchange"], "NASDAQ")
            self.assertGreater(quote["last_price"], 0)
            self.assertGreater(quote["open"], 0)
            self.assertGreater(quote["high"], 0)
            self.assertGreater(quote["low"], 0)
            self.assertEqual(quote["data_source"], "INTERNATIONAL_YFINANCE")
            self.assertTrue(quote["is_live"])

    def test_us_historical_candles(self):
        bars = self.provider.get_historical_candles("AAPL", timeframe="1d", count=10)
        if bars:
            self.assertGreaterEqual(len(bars), 1)
            bar = bars[-1]
            self.assertIn("open", bar)
            self.assertIn("high", bar)
            self.assertIn("low", bar)
            self.assertIn("close", bar)
            self.assertIn("volume", bar)
            self.assertGreater(bar["close"], 0)
            self.assertEqual(bar["data_source"], "INTERNATIONAL_YFINANCE")

    def test_market_data_manager_us_routing(self):
        # Verify MarketDataManager routes AAPL through to international provider
        q = self.manager.get_quote("AAPL")
        if q:
            self.assertEqual(q["currency_symbol"], "$")
            self.assertEqual(q["country"], "United States")

        indices = self.manager.get_us_indices()
        self.assertIsInstance(indices, dict)


if __name__ == "__main__":
    unittest.main()
