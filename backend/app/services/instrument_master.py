"""
Instrument Master Catalog — TradePilot (NSE / BSE)

This module contains METADATA for supported instruments.

CRITICAL: The `reference_price_stale` field below is PURELY METADATA
for reference only (e.g., circuit-breaker sanity checking).

IT MUST NEVER BE USED AS A LIVE MARKET PRICE.
IT MUST NEVER BE DISPLAYED TO THE USER AS A CURRENT PRICE.
IT MUST NEVER BE RETURNED IN A QUOTE RESPONSE.

Live prices MUST ALWAYS come from the active MarketDataProvider
(NSEMarketDataProvider / BSEMarketDataProvider / BrokerMarketDataProvider).

When no live price is available, the system MUST show:
    "CONNECT A LIVE MARKET DATA PROVIDER"
and NOT display any stale reference price.
"""
from typing import Dict, List, Any, Optional

# ---------------------------------------------------------------------------
# INSTRUMENT MASTER CATALOG
# Fields:
#   symbol             — Exchange ticker symbol (e.g., "RELIANCE")
#   exchange           — "NSE" or "BSE"
#   instrument_token   — Broker instrument token (Zerodha / Upstox / etc.)
#   isin               — ISIN code
#   lot_size           — Minimum lot size (1 for EQ, 25/50/75 for F&O)
#   segment            — "EQ", "INDICES", "FO", "CDS"
#   company_name       — Full legal name
#   sector             — Broad sector classification
#   tick_size          — Minimum price increment
#   reference_price_stale — METADATA ONLY — stale reference for circuit
#                           breaker validation. NEVER USE AS LIVE PRICE.
# ---------------------------------------------------------------------------
INSTRUMENT_MASTER_CATALOG: List[Dict[str, Any]] = [
    # ── NSE EQUITIES ────────────────────────────────────────────────────────
    {
        "symbol": "RELIANCE",
        "exchange": "NSE",
        "instrument_token": 738561,
        "isin": "INE002A01018",
        "lot_size": 1,
        "segment": "EQ",
        "series": "EQ",
        "company_name": "Reliance Industries Limited",
        "sector": "Energy / Oil & Gas / Telecom",
        "tick_size": 0.05,
        "reference_price_stale": None,  # DO NOT USE AS LIVE PRICE
    },
    {
        "symbol": "TCS",
        "exchange": "NSE",
        "instrument_token": 2953217,
        "isin": "INE467B01029",
        "lot_size": 1,
        "segment": "EQ",
        "series": "EQ",
        "company_name": "Tata Consultancy Services Limited",
        "sector": "Information Technology",
        "tick_size": 0.05,
        "reference_price_stale": None,
    },
    {
        "symbol": "INFY",
        "exchange": "NSE",
        "instrument_token": 408065,
        "isin": "INE009A01021",
        "lot_size": 1,
        "segment": "EQ",
        "series": "EQ",
        "company_name": "Infosys Limited",
        "sector": "Information Technology",
        "tick_size": 0.05,
        "reference_price_stale": None,
    },
    {
        "symbol": "HDFCBANK",
        "exchange": "NSE",
        "instrument_token": 341249,
        "isin": "INE040A01034",
        "lot_size": 1,
        "segment": "EQ",
        "series": "EQ",
        "company_name": "HDFC Bank Limited",
        "sector": "Banking & Financial Services",
        "tick_size": 0.05,
        "reference_price_stale": None,
    },
    {
        "symbol": "ICICIBANK",
        "exchange": "NSE",
        "instrument_token": 1270529,
        "isin": "INE090A01021",
        "lot_size": 1,
        "segment": "EQ",
        "series": "EQ",
        "company_name": "ICICI Bank Limited",
        "sector": "Banking & Financial Services",
        "tick_size": 0.05,
        "reference_price_stale": None,
    },
    {
        "symbol": "TATAMOTORS",
        "exchange": "NSE",
        "instrument_token": 884737,
        "isin": "INE155A01022",
        "lot_size": 1,
        "segment": "EQ",
        "series": "EQ",
        "company_name": "Tata Motors Limited",
        "sector": "Automobile & EV",
        "tick_size": 0.05,
        "reference_price_stale": None,
    },
    {
        "symbol": "SBIN",
        "exchange": "NSE",
        "instrument_token": 779521,
        "isin": "INE062A01020",
        "lot_size": 1,
        "segment": "EQ",
        "series": "EQ",
        "company_name": "State Bank of India",
        "sector": "Public Sector Banking",
        "tick_size": 0.05,
        "reference_price_stale": None,
    },
    {
        "symbol": "BHARTIARTL",
        "exchange": "NSE",
        "instrument_token": 2714625,
        "isin": "INE397D01024",
        "lot_size": 1,
        "segment": "EQ",
        "series": "EQ",
        "company_name": "Bharti Airtel Limited",
        "sector": "Telecommunications",
        "tick_size": 0.05,
        "reference_price_stale": None,
    },
    {
        "symbol": "LT",
        "exchange": "NSE",
        "instrument_token": 2939649,
        "isin": "INE018A01030",
        "lot_size": 1,
        "segment": "EQ",
        "series": "EQ",
        "company_name": "Larsen & Toubro Limited",
        "sector": "Capital Goods & Infrastructure",
        "tick_size": 0.05,
        "reference_price_stale": None,
    },
    {
        "symbol": "AXISBANK",
        "exchange": "NSE",
        "instrument_token": 1510401,
        "isin": "INE238A01034",
        "lot_size": 1,
        "segment": "EQ",
        "series": "EQ",
        "company_name": "Axis Bank Limited",
        "sector": "Banking & Financial Services",
        "tick_size": 0.05,
        "reference_price_stale": None,
    },
    {
        "symbol": "KOTAKBANK",
        "exchange": "NSE",
        "instrument_token": 492033,
        "isin": "INE237A01028",
        "lot_size": 1,
        "segment": "EQ",
        "series": "EQ",
        "company_name": "Kotak Mahindra Bank Limited",
        "sector": "Banking & Financial Services",
        "tick_size": 0.05,
        "reference_price_stale": None,
    },
    {
        "symbol": "ITC",
        "exchange": "NSE",
        "instrument_token": 424961,
        "isin": "INE154A01025",
        "lot_size": 1,
        "segment": "EQ",
        "series": "EQ",
        "company_name": "ITC Limited",
        "sector": "FMCG / Diversified",
        "tick_size": 0.05,
        "reference_price_stale": None,
    },
    {
        "symbol": "MARUTI",
        "exchange": "NSE",
        "instrument_token": 2815745,
        "isin": "INE585B01010",
        "lot_size": 1,
        "segment": "EQ",
        "series": "EQ",
        "company_name": "Maruti Suzuki India Limited",
        "sector": "Automobile",
        "tick_size": 0.05,
        "reference_price_stale": None,
    },
    {
        "symbol": "SUNPHARMA",
        "exchange": "NSE",
        "instrument_token": 857857,
        "isin": "INE044A01036",
        "lot_size": 1,
        "segment": "EQ",
        "series": "EQ",
        "company_name": "Sun Pharmaceutical Industries Limited",
        "sector": "Pharmaceuticals",
        "tick_size": 0.05,
        "reference_price_stale": None,
    },
    {
        "symbol": "TITAN",
        "exchange": "NSE",
        "instrument_token": 897537,
        "isin": "INE280A01028",
        "lot_size": 1,
        "segment": "EQ",
        "series": "EQ",
        "company_name": "Titan Company Limited",
        "sector": "Jewellery & Consumer Goods",
        "tick_size": 0.05,
        "reference_price_stale": None,
    },
    {
        "symbol": "BAJFINANCE",
        "exchange": "NSE",
        "instrument_token": 81153,
        "isin": "INE296A01024",
        "lot_size": 1,
        "segment": "EQ",
        "series": "EQ",
        "company_name": "Bajaj Finance Limited",
        "sector": "Non-Banking Financial Company",
        "tick_size": 0.05,
        "reference_price_stale": None,
    },
    {
        "symbol": "WIPRO",
        "exchange": "NSE",
        "instrument_token": 969473,
        "isin": "INE075A01022",
        "lot_size": 1,
        "segment": "EQ",
        "series": "EQ",
        "company_name": "Wipro Limited",
        "sector": "Information Technology",
        "tick_size": 0.05,
        "reference_price_stale": None,
    },
    {
        "symbol": "HCLTECH",
        "exchange": "NSE",
        "instrument_token": 1850625,
        "isin": "INE860A01027",
        "lot_size": 1,
        "segment": "EQ",
        "series": "EQ",
        "company_name": "HCL Technologies Limited",
        "sector": "Information Technology",
        "tick_size": 0.05,
        "reference_price_stale": None,
    },
    {
        "symbol": "ULTRACEMCO",
        "exchange": "NSE",
        "instrument_token": 2952193,
        "isin": "INE481G01011",
        "lot_size": 1,
        "segment": "EQ",
        "series": "EQ",
        "company_name": "UltraTech Cement Limited",
        "sector": "Cement & Construction Materials",
        "tick_size": 0.05,
        "reference_price_stale": None,
    },
    {
        "symbol": "ADANIENT",
        "exchange": "NSE",
        "instrument_token": 25,
        "isin": "INE423A01024",
        "lot_size": 1,
        "segment": "EQ",
        "series": "EQ",
        "company_name": "Adani Enterprises Limited",
        "sector": "Diversified / Infrastructure",
        "tick_size": 0.05,
        "reference_price_stale": None,
    },
    # ── NSE INDICES ──────────────────────────────────────────────────────────
    {
        "symbol": "NIFTY 50",
        "exchange": "NSE",
        "instrument_token": 256265,
        "isin": "INDEX_NIFTY50",
        "lot_size": 25,
        "segment": "INDICES",
        "series": "INDEX",
        "company_name": "NIFTY 50 Benchmark Index",
        "sector": "Benchmark Index",
        "tick_size": 0.05,
        "reference_price_stale": None,  # DO NOT USE AS LIVE PRICE
    },
    {
        "symbol": "NIFTY BANK",
        "exchange": "NSE",
        "instrument_token": 260105,
        "isin": "INDEX_BANKNIFTY",
        "lot_size": 15,
        "segment": "INDICES",
        "series": "INDEX",
        "company_name": "NIFTY Bank Sectoral Index",
        "sector": "Banking Index",
        "tick_size": 0.05,
        "reference_price_stale": None,  # DO NOT USE AS LIVE PRICE
    },
    {
        "symbol": "NIFTY NEXT 50",
        "exchange": "NSE",
        "instrument_token": 256585,
        "isin": "INDEX_NIFTYNEXT50",
        "lot_size": 40,
        "segment": "INDICES",
        "series": "INDEX",
        "company_name": "NIFTY Next 50 Index",
        "sector": "Benchmark Index",
        "tick_size": 0.05,
        "reference_price_stale": None,
    },
    {
        "symbol": "NIFTY 100",
        "exchange": "NSE",
        "instrument_token": 256601,
        "isin": "INDEX_NIFTY100",
        "lot_size": 50,
        "segment": "INDICES",
        "series": "INDEX",
        "company_name": "NIFTY 100 Index",
        "sector": "Benchmark Index",
        "tick_size": 0.05,
        "reference_price_stale": None,
    },
    {
        "symbol": "INDIA VIX",
        "exchange": "NSE",
        "instrument_token": 264969,
        "isin": "INDEX_INDIAVIX",
        "lot_size": 1,
        "segment": "INDICES",
        "series": "INDEX",
        "company_name": "India Volatility Index",
        "sector": "Volatility Index",
        "tick_size": 0.01,
        "reference_price_stale": None,
    },
    # ── BSE INDICES ──────────────────────────────────────────────────────────
    {
        "symbol": "SENSEX",
        "exchange": "BSE",
        "instrument_token": 265,
        "isin": "INDEX_SENSEX",
        "lot_size": 10,
        "segment": "INDICES",
        "series": "INDEX",
        "company_name": "BSE SENSEX 30 Benchmark Index",
        "sector": "Benchmark Index",
        "tick_size": 0.05,
        "reference_price_stale": None,  # DO NOT USE AS LIVE PRICE
    },
    # ── COMMODITIES & PRECIOUS METALS ────────────────────────────────────────
    {
        "symbol": "GOLD",
        "exchange": "NSE",
        "instrument_token": 999001,
        "isin": "INF204KB14I2",
        "lot_size": 1,
        "segment": "COMMODITIES",
        "series": "EQ",
        "company_name": "Gold / Nippon India ETF Gold BeES",
        "sector": "Precious Metals / Commodity",
        "tick_size": 0.01,
        "reference_price_stale": None,
    },
    {
        "symbol": "GOLDBEES",
        "exchange": "NSE",
        "instrument_token": 999002,
        "isin": "INF204KB14I2",
        "lot_size": 1,
        "segment": "COMMODITIES",
        "series": "EQ",
        "company_name": "Nippon India ETF Gold BeES",
        "sector": "Precious Metals / Commodity",
        "tick_size": 0.01,
        "reference_price_stale": None,
    },
    {
        "symbol": "SILVER",
        "exchange": "NSE",
        "instrument_token": 999003,
        "isin": "INF204KB1854",
        "lot_size": 1,
        "segment": "COMMODITIES",
        "series": "EQ",
        "company_name": "Silver / Nippon India ETF Silver BeES",
        "sector": "Precious Metals / Commodity",
        "tick_size": 0.01,
        "reference_price_stale": None,
    },
    {
        "symbol": "SILVERBEES",
        "exchange": "NSE",
        "instrument_token": 999004,
        "isin": "INF204KB1854",
        "lot_size": 1,
        "segment": "COMMODITIES",
        "series": "EQ",
        "company_name": "Nippon India ETF Silver BeES",
        "sector": "Precious Metals / Commodity",
        "tick_size": 0.01,
        "reference_price_stale": None,
    },
]

# ── US & INTERNATIONAL INSTRUMENTS ───────────────────────────────────────
US_INSTRUMENTS: List[Dict[str, Any]] = [
    {
        "symbol": "AAPL",
        "exchange": "NASDAQ",
        "instrument_token": 800001,
        "isin": "US0378331005",
        "lot_size": 1,
        "segment": "EQ",
        "series": "EQ",
        "company_name": "Apple Inc.",
        "sector": "Technology / Consumer Electronics",
        "tick_size": 0.01,
        "reference_price_stale": None,
        "currency": "USD",
        "currency_symbol": "$",
        "country": "United States",
        "timezone": "America/New_York",
        "market": "US",
    },
    {
        "symbol": "MSFT",
        "exchange": "NASDAQ",
        "instrument_token": 800002,
        "isin": "US5949181045",
        "lot_size": 1,
        "segment": "EQ",
        "series": "EQ",
        "company_name": "Microsoft Corporation",
        "sector": "Technology / Enterprise Software & Cloud",
        "tick_size": 0.01,
        "reference_price_stale": None,
        "currency": "USD",
        "currency_symbol": "$",
        "country": "United States",
        "timezone": "America/New_York",
        "market": "US",
    },
    {
        "symbol": "NVDA",
        "exchange": "NASDAQ",
        "instrument_token": 800003,
        "isin": "US67066G1040",
        "lot_size": 1,
        "segment": "EQ",
        "series": "EQ",
        "company_name": "NVIDIA Corporation",
        "sector": "Technology / AI & Semiconductors",
        "tick_size": 0.01,
        "reference_price_stale": None,
        "currency": "USD",
        "currency_symbol": "$",
        "country": "United States",
        "timezone": "America/New_York",
        "market": "US",
    },
    {
        "symbol": "GOOGL",
        "exchange": "NASDAQ",
        "instrument_token": 800004,
        "isin": "US02079K3059",
        "lot_size": 1,
        "segment": "EQ",
        "series": "EQ",
        "company_name": "Alphabet Inc.",
        "sector": "Technology / Internet Services",
        "tick_size": 0.01,
        "reference_price_stale": None,
        "currency": "USD",
        "currency_symbol": "$",
        "country": "United States",
        "timezone": "America/New_York",
        "market": "US",
    },
    {
        "symbol": "AMZN",
        "exchange": "NASDAQ",
        "instrument_token": 800005,
        "isin": "US0231351067",
        "lot_size": 1,
        "segment": "EQ",
        "series": "EQ",
        "company_name": "Amazon.com Inc.",
        "sector": "Consumer Cyclical / E-Commerce & AWS",
        "tick_size": 0.01,
        "reference_price_stale": None,
        "currency": "USD",
        "currency_symbol": "$",
        "country": "United States",
        "timezone": "America/New_York",
        "market": "US",
    },
    {
        "symbol": "META",
        "exchange": "NASDAQ",
        "instrument_token": 800006,
        "isin": "US30303M1027",
        "lot_size": 1,
        "segment": "EQ",
        "series": "EQ",
        "company_name": "Meta Platforms Inc.",
        "sector": "Technology / Social Platforms & AI",
        "tick_size": 0.01,
        "reference_price_stale": None,
        "currency": "USD",
        "currency_symbol": "$",
        "country": "United States",
        "timezone": "America/New_York",
        "market": "US",
    },
    {
        "symbol": "TSLA",
        "exchange": "NASDAQ",
        "instrument_token": 800007,
        "isin": "US88160R1014",
        "lot_size": 1,
        "segment": "EQ",
        "series": "EQ",
        "company_name": "Tesla Inc.",
        "sector": "Automotive / EV & Clean Energy",
        "tick_size": 0.01,
        "reference_price_stale": None,
        "currency": "USD",
        "currency_symbol": "$",
        "country": "United States",
        "timezone": "America/New_York",
        "market": "US",
    },
    {
        "symbol": "JPM",
        "exchange": "NYSE",
        "instrument_token": 800008,
        "isin": "US46625H1005",
        "lot_size": 1,
        "segment": "EQ",
        "series": "EQ",
        "company_name": "JPMorgan Chase & Co.",
        "sector": "Financial Services / Banking",
        "tick_size": 0.01,
        "reference_price_stale": None,
        "currency": "USD",
        "currency_symbol": "$",
        "country": "United States",
        "timezone": "America/New_York",
        "market": "US",
    },
    {
        "symbol": "V",
        "exchange": "NYSE",
        "instrument_token": 800009,
        "isin": "US92826C8394",
        "lot_size": 1,
        "segment": "EQ",
        "series": "EQ",
        "company_name": "Visa Inc.",
        "sector": "Financial Services / Payments",
        "tick_size": 0.01,
        "reference_price_stale": None,
        "currency": "USD",
        "currency_symbol": "$",
        "country": "United States",
        "timezone": "America/New_York",
        "market": "US",
    },
    {
        "symbol": "MA",
        "exchange": "NYSE",
        "instrument_token": 800010,
        "isin": "US57636Q1040",
        "lot_size": 1,
        "segment": "EQ",
        "series": "EQ",
        "company_name": "Mastercard Incorporated",
        "sector": "Financial Services / Payments",
        "tick_size": 0.01,
        "reference_price_stale": None,
        "currency": "USD",
        "currency_symbol": "$",
        "country": "United States",
        "timezone": "America/New_York",
        "market": "US",
    },
    {
        "symbol": "CAT",
        "exchange": "NYSE",
        "instrument_token": 800011,
        "isin": "US1491231015",
        "lot_size": 1,
        "segment": "EQ",
        "series": "EQ",
        "company_name": "Caterpillar Inc.",
        "sector": "Industrials / Heavy Machinery",
        "tick_size": 0.01,
        "reference_price_stale": None,
        "currency": "USD",
        "currency_symbol": "$",
        "country": "United States",
        "timezone": "America/New_York",
        "market": "US",
    },
    {
        "symbol": "BA",
        "exchange": "NYSE",
        "instrument_token": 800012,
        "isin": "US0970231058",
        "lot_size": 1,
        "segment": "EQ",
        "series": "EQ",
        "company_name": "The Boeing Company",
        "sector": "Industrials / Aerospace & Defense",
        "tick_size": 0.01,
        "reference_price_stale": None,
        "currency": "USD",
        "currency_symbol": "$",
        "country": "United States",
        "timezone": "America/New_York",
        "market": "US",
    },
    # US Index ETFs
    {
        "symbol": "SPY",
        "exchange": "NYSE",
        "instrument_token": 800013,
        "isin": "US78462F1030",
        "lot_size": 1,
        "segment": "ETF",
        "series": "EQ",
        "company_name": "SPDR S&P 500 ETF Trust",
        "sector": "Index ETF / S&P 500",
        "tick_size": 0.01,
        "reference_price_stale": None,
        "currency": "USD",
        "currency_symbol": "$",
        "country": "United States",
        "timezone": "America/New_York",
        "market": "US",
    },
    {
        "symbol": "QQQ",
        "exchange": "NASDAQ",
        "instrument_token": 800014,
        "isin": "US46090E1038",
        "lot_size": 1,
        "segment": "ETF",
        "series": "EQ",
        "company_name": "Invesco QQQ Trust (NASDAQ 100)",
        "sector": "Index ETF / NASDAQ 100",
        "tick_size": 0.01,
        "reference_price_stale": None,
        "currency": "USD",
        "currency_symbol": "$",
        "country": "United States",
        "timezone": "America/New_York",
        "market": "US",
    },
    {
        "symbol": "DIA",
        "exchange": "NYSE",
        "instrument_token": 800015,
        "isin": "US78467X1090",
        "lot_size": 1,
        "segment": "ETF",
        "series": "EQ",
        "company_name": "SPDR Dow Jones Industrial Average ETF",
        "sector": "Index ETF / Dow Jones",
        "tick_size": 0.01,
        "reference_price_stale": None,
        "currency": "USD",
        "currency_symbol": "$",
        "country": "United States",
        "timezone": "America/New_York",
        "market": "US",
    },
    # US Sector ETFs
    {
        "symbol": "XLK",
        "exchange": "NYSE",
        "instrument_token": 800016,
        "isin": "US81369Y8030",
        "lot_size": 1,
        "segment": "ETF",
        "series": "EQ",
        "company_name": "Technology Select Sector SPDR Fund",
        "sector": "Sector ETF / Technology",
        "tick_size": 0.01,
        "reference_price_stale": None,
        "currency": "USD",
        "currency_symbol": "$",
        "country": "United States",
        "timezone": "America/New_York",
        "market": "US",
    },
    {
        "symbol": "XLF",
        "exchange": "NYSE",
        "instrument_token": 800017,
        "isin": "US81369Y6059",
        "lot_size": 1,
        "segment": "ETF",
        "series": "EQ",
        "company_name": "Financial Select Sector SPDR Fund",
        "sector": "Sector ETF / Financials",
        "tick_size": 0.01,
        "reference_price_stale": None,
        "currency": "USD",
        "currency_symbol": "$",
        "country": "United States",
        "timezone": "America/New_York",
        "market": "US",
    },
    {
        "symbol": "XLE",
        "exchange": "NYSE",
        "instrument_token": 800018,
        "isin": "US81369Y5069",
        "lot_size": 1,
        "segment": "ETF",
        "series": "EQ",
        "company_name": "Energy Select Sector SPDR Fund",
        "sector": "Sector ETF / Energy",
        "tick_size": 0.01,
        "reference_price_stale": None,
        "currency": "USD",
        "currency_symbol": "$",
        "country": "United States",
        "timezone": "America/New_York",
        "market": "US",
    },
    {
        "symbol": "XLV",
        "exchange": "NYSE",
        "instrument_token": 800019,
        "isin": "US81369Y2090",
        "lot_size": 1,
        "segment": "ETF",
        "series": "EQ",
        "company_name": "Health Care Select Sector SPDR Fund",
        "sector": "Sector ETF / Healthcare",
        "tick_size": 0.01,
        "reference_price_stale": None,
        "currency": "USD",
        "currency_symbol": "$",
        "country": "United States",
        "timezone": "America/New_York",
        "market": "US",
    },
    # US Benchmark Indices
    {
        "symbol": "NASDAQ 100",
        "exchange": "NASDAQ",
        "instrument_token": 800020,
        "isin": "USINDEX00001",
        "lot_size": 1,
        "segment": "INDICES",
        "series": "INDEX",
        "company_name": "NASDAQ 100 Index",
        "sector": "Index / US Benchmark",
        "tick_size": 0.01,
        "reference_price_stale": None,
        "currency": "USD",
        "currency_symbol": "$",
        "country": "United States",
        "timezone": "America/New_York",
        "market": "US",
    },
    {
        "symbol": "S&P 500",
        "exchange": "NYSE",
        "instrument_token": 800021,
        "isin": "USINDEX00002",
        "lot_size": 1,
        "segment": "INDICES",
        "series": "INDEX",
        "company_name": "S&P 500 Index",
        "sector": "Index / US Benchmark",
        "tick_size": 0.01,
        "reference_price_stale": None,
        "currency": "USD",
        "currency_symbol": "$",
        "country": "United States",
        "timezone": "America/New_York",
        "market": "US",
    },
    {
        "symbol": "DOW JONES",
        "exchange": "NYSE",
        "instrument_token": 800022,
        "isin": "USINDEX00003",
        "lot_size": 1,
        "segment": "INDICES",
        "series": "INDEX",
        "company_name": "Dow Jones Industrial Average",
        "sector": "Index / US Benchmark",
        "tick_size": 0.01,
        "reference_price_stale": None,
        "currency": "USD",
        "currency_symbol": "$",
        "country": "United States",
        "timezone": "America/New_York",
        "market": "US",
    },
    {
        "symbol": "US VIX",
        "exchange": "CBOE",
        "instrument_token": 800023,
        "isin": "USINDEX00004",
        "lot_size": 1,
        "segment": "INDICES",
        "series": "INDEX",
        "company_name": "CBOE Volatility Index",
        "sector": "Volatility Index",
        "tick_size": 0.01,
        "reference_price_stale": None,
        "currency": "USD",
        "currency_symbol": "$",
        "country": "United States",
        "timezone": "America/New_York",
        "market": "US",
    },
]

# Ensure Indian instruments carry appropriate country, currency, and timezone tags
for inst in INSTRUMENT_MASTER_CATALOG:
    inst.setdefault("currency", "INR")
    inst.setdefault("currency_symbol", "₹")
    inst.setdefault("country", "India")
    inst.setdefault("timezone", "Asia/Kolkata")
    inst.setdefault("market", "IN")

# Combine Indian & US into the master catalog
INSTRUMENT_MASTER_CATALOG.extend(US_INSTRUMENTS)


def get_all_instruments() -> List[Dict[str, Any]]:
    """Return the full unified instrument catalog (metadata only — no live prices)."""
    return INSTRUMENT_MASTER_CATALOG


def get_instrument_by_symbol(symbol: str) -> Optional[Dict[str, Any]]:
    """Look up instrument metadata by symbol. Returns None if not found."""
    clean = (
        symbol.upper()
        .replace(".NS", "")
        .replace(".BO", "")
        .replace("NSE:", "")
        .replace("BSE:", "")
        .replace("NASDAQ:", "")
        .replace("NYSE:", "")
        .strip()
    )
    return next(
        (inst for inst in INSTRUMENT_MASTER_CATALOG if inst["symbol"].upper() == clean),
        None,
    )


def search_instruments(query: str) -> List[Dict[str, Any]]:
    """Search instruments globally by symbol, company name, sector, exchange, country, or ISIN."""
    q = query.lower().strip()
    if not q:
        return INSTRUMENT_MASTER_CATALOG[:50]
    return [
        inst for inst in INSTRUMENT_MASTER_CATALOG
        if (
            q in inst["symbol"].lower()
            or q in inst.get("company_name", "").lower()
            or q in inst.get("sector", "").lower()
            or q in inst.get("exchange", "").lower()
            or q in inst.get("country", "").lower()
            or q in inst.get("isin", "").lower()
        )
    ]


def search_instruments_advanced(
    query: Optional[str] = None,
    market: Optional[str] = None,
    exchange: Optional[str] = None,
    segment: Optional[str] = None,
    limit: int = 50,
) -> List[Dict[str, Any]]:
    """Advanced filtered search across market, exchange, and segment."""
    results = INSTRUMENT_MASTER_CATALOG

    if isinstance(market, str) and market.strip():
        m_upper = market.upper().strip()
        results = [i for i in results if i.get("market", "").upper() == m_upper]

    if isinstance(exchange, str) and exchange.strip():
        e_upper = exchange.upper().strip()
        results = [i for i in results if i.get("exchange", "").upper() == e_upper]

    if isinstance(segment, str) and segment.strip():
        s_upper = segment.upper().strip()
        results = [i for i in results if i.get("segment", "").upper() == s_upper]

    if isinstance(query, str) and query.strip():
        q = query.lower().strip()
        results = [
            i for i in results
            if (
                q in i["symbol"].lower()
                or q in i.get("company_name", "").lower()
                or q in i.get("sector", "").lower()
                or q in i.get("exchange", "").lower()
                or q in i.get("country", "").lower()
            )
        ]

    return results[:limit]


def get_instruments_by_market(market: str) -> List[Dict[str, Any]]:
    """Return instruments for a given market ('IN' or 'US')."""
    m = market.upper().strip()
    return [i for i in INSTRUMENT_MASTER_CATALOG if i.get("market", "").upper() == m]


def get_instruments_by_exchange(exchange: str) -> List[Dict[str, Any]]:
    """Return instruments for a given exchange ('NSE', 'BSE', 'NASDAQ', 'NYSE')."""
    ex = exchange.upper().strip()
    return [i for i in INSTRUMENT_MASTER_CATALOG if i.get("exchange", "").upper() == ex]


def get_equity_symbols_nse() -> List[str]:
    """Return all NSE equity symbols (excludes indices)."""
    return [
        inst["symbol"]
        for inst in INSTRUMENT_MASTER_CATALOG
        if inst.get("exchange") == "NSE" and inst.get("segment") == "EQ"
    ]


def get_index_symbols() -> List[str]:
    """Return all index symbols."""
    return [
        inst["symbol"]
        for inst in INSTRUMENT_MASTER_CATALOG
        if inst.get("segment") == "INDICES"
    ]


def get_commodity_symbols() -> List[str]:
    """Return all commodity and precious metals symbols."""
    return [
        inst["symbol"]
        for inst in INSTRUMENT_MASTER_CATALOG
        if inst.get("segment") == "COMMODITIES"
    ]


def get_us_symbols() -> List[str]:
    """Return all US equity and ETF symbols."""
    return [
        inst["symbol"]
        for inst in INSTRUMENT_MASTER_CATALOG
        if inst.get("market") == "US"
    ]
