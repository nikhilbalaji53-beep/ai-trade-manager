"""
NIFTY 50 Constituents Service — TradePilot

Provides real-time data for all 50 NIFTY 50 constituent stocks.
Constituent list sourced from NSE India (as of August 2025).

IMPORTANT:
  - The constituent list is maintained here as static metadata
  - Prices are NOT hardcoded — they are fetched live from the market data provider
  - Update the constituent list when NSE announces index reconstitution

NSE NIFTY 50 Constituents (50 stocks as of August 2025):
Source: https://www.nseindia.com/products-services/indices-nifty50-index
"""
import logging
from typing import Dict, List, Any, Optional

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# NIFTY 50 Constituent List
# Metadata only — prices must come from the live market data provider
# ---------------------------------------------------------------------------
NIFTY50_CONSTITUENTS: List[Dict[str, Any]] = [
    {"symbol": "ADANIENT",   "company_name": "Adani Enterprises Ltd",      "sector": "Diversified",           "weight_approx_pct": 1.8},
    {"symbol": "ADANIPORTS", "company_name": "Adani Ports & SEZ Ltd",       "sector": "Infrastructure",        "weight_approx_pct": 1.4},
    {"symbol": "APOLLOHOSP", "company_name": "Apollo Hospitals Enterprise", "sector": "Healthcare",            "weight_approx_pct": 0.9},
    {"symbol": "ASIANPAINT", "company_name": "Asian Paints Ltd",            "sector": "Consumer Goods",        "weight_approx_pct": 1.2},
    {"symbol": "AXISBANK",   "company_name": "Axis Bank Ltd",               "sector": "Banking",               "weight_approx_pct": 2.1},
    {"symbol": "BAJAJFINSV", "company_name": "Bajaj Finserv Ltd",           "sector": "Financial Services",    "weight_approx_pct": 0.9},
    {"symbol": "BAJFINANCE", "company_name": "Bajaj Finance Ltd",           "sector": "Financial Services",    "weight_approx_pct": 2.1},
    {"symbol": "BHARTIARTL", "company_name": "Bharti Airtel Ltd",           "sector": "Telecommunications",   "weight_approx_pct": 3.2},
    {"symbol": "BPCL",       "company_name": "Bharat Petroleum Corp Ltd",   "sector": "Energy / Oil & Gas",    "weight_approx_pct": 0.7},
    {"symbol": "BRITANNIA",  "company_name": "Britannia Industries Ltd",    "sector": "Consumer Goods / FMCG", "weight_approx_pct": 0.7},
    {"symbol": "CIPLA",      "company_name": "Cipla Ltd",                   "sector": "Pharmaceuticals",       "weight_approx_pct": 0.9},
    {"symbol": "COALINDIA",  "company_name": "Coal India Ltd",              "sector": "Mining",                "weight_approx_pct": 1.0},
    {"symbol": "DIVISLAB",   "company_name": "Divi's Laboratories Ltd",     "sector": "Pharmaceuticals",       "weight_approx_pct": 0.7},
    {"symbol": "DRREDDY",    "company_name": "Dr. Reddy's Laboratories",    "sector": "Pharmaceuticals",       "weight_approx_pct": 0.9},
    {"symbol": "EICHERMOT",  "company_name": "Eicher Motors Ltd",           "sector": "Automobile",            "weight_approx_pct": 0.9},
    {"symbol": "GRASIM",     "company_name": "Grasim Industries Ltd",       "sector": "Cement / Diversified",  "weight_approx_pct": 1.0},
    {"symbol": "HCLTECH",    "company_name": "HCL Technologies Ltd",        "sector": "Information Technology","weight_approx_pct": 2.2},
    {"symbol": "HDFCBANK",   "company_name": "HDFC Bank Ltd",               "sector": "Banking",               "weight_approx_pct": 12.5},
    {"symbol": "HDFCLIFE",   "company_name": "HDFC Life Insurance Co Ltd",  "sector": "Insurance",             "weight_approx_pct": 0.8},
    {"symbol": "HEROMOTOCO", "company_name": "Hero MotoCorp Ltd",           "sector": "Automobile",            "weight_approx_pct": 0.8},
    {"symbol": "HINDUNILVR", "company_name": "Hindustan Unilever Ltd",      "sector": "FMCG",                  "weight_approx_pct": 2.0},
    {"symbol": "ICICIBANK",  "company_name": "ICICI Bank Ltd",              "sector": "Banking",               "weight_approx_pct": 7.5},
    {"symbol": "INDUSINDBK", "company_name": "IndusInd Bank Ltd",           "sector": "Banking",               "weight_approx_pct": 0.9},
    {"symbol": "INFY",       "company_name": "Infosys Ltd",                 "sector": "Information Technology","weight_approx_pct": 5.8},
    {"symbol": "ITC",        "company_name": "ITC Ltd",                     "sector": "FMCG / Conglomerate",   "weight_approx_pct": 2.8},
    {"symbol": "JSWSTEEL",   "company_name": "JSW Steel Ltd",               "sector": "Metals & Mining",       "weight_approx_pct": 1.0},
    {"symbol": "KOTAKBANK",  "company_name": "Kotak Mahindra Bank Ltd",     "sector": "Banking",               "weight_approx_pct": 3.2},
    {"symbol": "LT",         "company_name": "Larsen & Toubro Ltd",         "sector": "Infrastructure / EPC",  "weight_approx_pct": 3.5},
    {"symbol": "M&M",        "company_name": "Mahindra & Mahindra Ltd",     "sector": "Automobile",            "weight_approx_pct": 2.0},
    {"symbol": "MARUTI",     "company_name": "Maruti Suzuki India Ltd",     "sector": "Automobile",            "weight_approx_pct": 1.8},
    {"symbol": "NESTLEIND",  "company_name": "Nestle India Ltd",            "sector": "FMCG",                  "weight_approx_pct": 0.7},
    {"symbol": "NTPC",       "company_name": "NTPC Ltd",                    "sector": "Power / Utilities",     "weight_approx_pct": 1.5},
    {"symbol": "ONGC",       "company_name": "Oil & Natural Gas Corp Ltd",  "sector": "Energy / Oil & Gas",    "weight_approx_pct": 1.2},
    {"symbol": "POWERGRID",  "company_name": "Power Grid Corp of India Ltd","sector": "Power / Utilities",     "weight_approx_pct": 1.1},
    {"symbol": "RELIANCE",   "company_name": "Reliance Industries Ltd",     "sector": "Energy / Retail / Tech","weight_approx_pct": 9.2},
    {"symbol": "SBILIFE",    "company_name": "SBI Life Insurance Co Ltd",   "sector": "Insurance",             "weight_approx_pct": 0.9},
    {"symbol": "SBIN",       "company_name": "State Bank of India",         "sector": "Banking (PSU)",         "weight_approx_pct": 3.0},
    {"symbol": "SHRIRAMFIN", "company_name": "Shriram Finance Ltd",         "sector": "NBFC",                  "weight_approx_pct": 0.8},
    {"symbol": "SUNPHARMA",  "company_name": "Sun Pharmaceutical Industries","sector": "Pharmaceuticals",      "weight_approx_pct": 1.9},
    {"symbol": "TATACONSUM", "company_name": "Tata Consumer Products Ltd",  "sector": "FMCG",                  "weight_approx_pct": 0.9},
    {"symbol": "TATAMOTORS", "company_name": "Tata Motors Ltd",             "sector": "Automobile",            "weight_approx_pct": 1.4},
    {"symbol": "TATASTEEL",  "company_name": "Tata Steel Ltd",              "sector": "Metals & Steel",        "weight_approx_pct": 0.9},
    {"symbol": "TCS",        "company_name": "Tata Consultancy Services Ltd","sector": "Information Technology","weight_approx_pct": 4.5},
    {"symbol": "TECHM",      "company_name": "Tech Mahindra Ltd",           "sector": "Information Technology","weight_approx_pct": 0.9},
    {"symbol": "TITAN",      "company_name": "Titan Company Ltd",           "sector": "Consumer Goods / Retail","weight_approx_pct": 1.5},
    {"symbol": "TRENT",      "company_name": "Trent Ltd",                   "sector": "Retail",                "weight_approx_pct": 1.2},
    {"symbol": "ULTRACEMCO", "company_name": "UltraTech Cement Ltd",        "sector": "Cement",                "weight_approx_pct": 1.8},
    {"symbol": "WIPRO",      "company_name": "Wipro Ltd",                   "sector": "Information Technology","weight_approx_pct": 0.9},
    {"symbol": "BAJAJ-AUTO", "company_name": "Bajaj Auto Ltd",              "sector": "Automobile",            "weight_approx_pct": 1.4},
    {"symbol": "BAJAJAUTO",  "company_name": "Bajaj Auto Ltd",              "sector": "Automobile",            "weight_approx_pct": 1.4},  # alias
]

# ---------------------------------------------------------------------------
# NIFTY BANK Constituents (12 stocks)
# ---------------------------------------------------------------------------
NIFTY_BANK_CONSTITUENTS: List[Dict[str, Any]] = [
    {"symbol": "HDFCBANK",   "company_name": "HDFC Bank Ltd",           "sector": "Banking", "weight_approx_pct": 28.0},
    {"symbol": "ICICIBANK",  "company_name": "ICICI Bank Ltd",          "sector": "Banking", "weight_approx_pct": 22.0},
    {"symbol": "AXISBANK",   "company_name": "Axis Bank Ltd",           "sector": "Banking", "weight_approx_pct": 10.0},
    {"symbol": "KOTAKBANK",  "company_name": "Kotak Mahindra Bank Ltd", "sector": "Banking", "weight_approx_pct": 12.0},
    {"symbol": "SBIN",       "company_name": "State Bank of India",     "sector": "Banking", "weight_approx_pct": 10.0},
    {"symbol": "INDUSINDBK", "company_name": "IndusInd Bank Ltd",       "sector": "Banking", "weight_approx_pct": 5.0},
    {"symbol": "BANDHANBNK", "company_name": "Bandhan Bank Ltd",        "sector": "Banking", "weight_approx_pct": 2.0},
    {"symbol": "FEDERALBNK", "company_name": "The Federal Bank Ltd",    "sector": "Banking", "weight_approx_pct": 2.5},
    {"symbol": "IDFCFIRSTB", "company_name": "IDFC First Bank Ltd",     "sector": "Banking", "weight_approx_pct": 2.0},
    {"symbol": "PNB",        "company_name": "Punjab National Bank",    "sector": "Banking", "weight_approx_pct": 2.0},
    {"symbol": "AUBANK",     "company_name": "AU Small Finance Bank",   "sector": "Banking", "weight_approx_pct": 1.5},
    {"symbol": "CANBK",      "company_name": "Canara Bank",             "sector": "Banking", "weight_approx_pct": 2.0},
]

# Deduplicated NIFTY 50 symbol list
NIFTY50_SYMBOLS = list({c["symbol"] for c in NIFTY50_CONSTITUENTS if c["symbol"] != "BAJAJAUTO"})
NIFTY_BANK_SYMBOLS = [c["symbol"] for c in NIFTY_BANK_CONSTITUENTS]


def get_nifty50_constituents() -> List[Dict[str, Any]]:
    """
    Return the NIFTY 50 constituent metadata list.
    Prices are NOT included — use get_nifty50_live_quotes() for live data.
    """
    seen = set()
    unique = []
    for c in NIFTY50_CONSTITUENTS:
        if c["symbol"] not in seen and c["symbol"] != "BAJAJAUTO":
            seen.add(c["symbol"])
            unique.append(c)
    return unique


def get_nifty50_symbols() -> List[str]:
    """Return deduplicated list of NIFTY 50 stock symbols."""
    return list(NIFTY50_SYMBOLS)


def get_nifty_bank_symbols() -> List[str]:
    """Return NIFTY BANK constituent stock symbols."""
    return list(NIFTY_BANK_SYMBOLS)


def get_nifty50_live_quotes(market_data_manager) -> List[Dict[str, Any]]:
    """
    Fetch live quotes for all NIFTY 50 constituent stocks.

    Returns:
        List of normalized quote dicts from the active market data provider.
        Missing quotes (provider returned None) are excluded.
        Empty list returned if no quotes available.

    NEVER returns hardcoded or invented prices.

    Args:
        market_data_manager: The active MarketDataManager instance
    """
    symbols = get_nifty50_symbols()
    quotes = []
    constituent_meta = {c["symbol"]: c for c in get_nifty50_constituents()}

    for symbol in symbols:
        quote = market_data_manager.get_quote(symbol)
        if quote and isinstance(quote.get("last_price"), (int, float)) and quote["last_price"] > 0:
            meta = constituent_meta.get(symbol, {})
            quote["nifty50_weight_approx_pct"] = meta.get("weight_approx_pct")
            quote["index_member"] = "NIFTY 50"
            quotes.append(quote)
        else:
            logger.debug(f"NIFTY50 constituent '{symbol}': no live quote available from provider")

    logger.info(f"NIFTY50 constituents: {len(quotes)}/{len(symbols)} quotes available from provider")
    return quotes


def get_nifty_bank_live_quotes(market_data_manager) -> List[Dict[str, Any]]:
    """
    Fetch live quotes for all NIFTY BANK constituent stocks.
    Returns only stocks for which the provider has data.
    NEVER returns hardcoded prices.
    """
    symbols = get_nifty_bank_symbols()
    quotes = []
    for symbol in symbols:
        quote = market_data_manager.get_quote(symbol)
        if quote and isinstance(quote.get("last_price"), (int, float)) and quote["last_price"] > 0:
            quote["index_member"] = "NIFTY BANK"
            quotes.append(quote)
    logger.info(f"NIFTY BANK constituents: {len(quotes)}/{len(symbols)} quotes available")
    return quotes
