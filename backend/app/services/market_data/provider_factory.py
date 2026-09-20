"""
Market Data Provider Factory — TradePilot

Responsible for selecting and initializing the correct market data provider
based on environment configuration.

Provider Hierarchy:
  BROKER_API       → BrokerMarketDataProvider (real-time, < 1 second)
  NSE_LIVE         → NSEMarketDataProvider via Yahoo Finance (~15-20 min delayed)
  PAPER            → BLOCKED in production (raises RuntimeError)

Production Safety Rule:
  - ENVIRONMENT=production + MARKET_DATA_MODE=paper → RuntimeError on startup
  - ENVIRONMENT=production requires MARKET_DATA_PROVIDER=NSE_LIVE or BROKER_API
"""
import os
import logging
from typing import Optional

from app.services.market_data.base_provider import MarketDataProvider
from app.services.market_data.nse_provider import NSEMarketDataProvider
from app.services.market_data.bse_provider import BSEMarketDataProvider
from app.services.market_data.broker_provider import BrokerMarketDataProvider
from app.services.market_data.international_provider import InternationalMarketDataProvider

logger = logging.getLogger(__name__)


# Paper/mock provider names that are banned in production
PAPER_PROVIDER_KEYWORDS = {"PAPER", "MOCK", "FAKE", "DEMO", "TEST", "RANDOM", "SYNTHETIC"}


def create_primary_provider() -> MarketDataProvider:
    """
    Create and return the configured market data provider.

    Reads:
        ENVIRONMENT              — "production" | "development" | "staging"
        MARKET_DATA_PROVIDER     — "NSE_LIVE" | "BROKER_API" | "BSE_LIVE" | "INTERNATIONAL_LIVE"
        MARKET_DATA_MODE         — "paper" is blocked in production
        BROKER_API_KEY / ZERODHA_KITE_API_KEY / UPSTOX_API_KEY / etc.

    Returns:
        An initialized MarketDataProvider (not yet connected)

    Raises:
        RuntimeError: If production environment attempts to use a paper provider
    """
    environment = os.getenv("ENVIRONMENT", "production").lower()
    provider_choice = os.getenv("MARKET_DATA_PROVIDER", "NSE_LIVE").upper()
    market_mode = os.getenv("MARKET_DATA_MODE", "").upper()

    # ── PRODUCTION GUARD ────────────────────────────────────────────────────
    if environment == "production":
        if market_mode == "PAPER":
            raise RuntimeError(
                "PRODUCTION SAFETY VIOLATION: MARKET_DATA_MODE=paper is set in a "
                "production environment. Paper/mock providers are PROHIBITED in "
                "ENVIRONMENT=production. Set MARKET_DATA_MODE=live and configure "
                "a real market data provider (NSE_LIVE or BROKER_API)."
            )
    # ────────────────────────────────────────────────────────────────────────

    logger.info(
        f"ProviderFactory: ENVIRONMENT={environment} | "
        f"MARKET_DATA_PROVIDER={provider_choice} | "
        f"MARKET_DATA_MODE={market_mode or 'not_set'}"
    )

    if provider_choice == "BROKER_API":
        broker_name = _detect_broker_name()
        logger.info(f"ProviderFactory: Creating BrokerMarketDataProvider for {broker_name}")
        return BrokerMarketDataProvider(broker_name=broker_name)

    elif provider_choice in ("NSE_LIVE", "NSE_YFINANCE", "YFINANCE"):
        logger.info("ProviderFactory: Creating NSEMarketDataProvider (Yahoo Finance, ~15-20 min delay)")
        return NSEMarketDataProvider()

    elif provider_choice in ("BSE_LIVE", "BSE_YFINANCE"):
        logger.info("ProviderFactory: Creating BSEMarketDataProvider (Yahoo Finance, ~15-20 min delay)")
        return BSEMarketDataProvider()

    elif provider_choice in ("INTERNATIONAL_LIVE", "US_LIVE", "NASDAQ_LIVE"):
        logger.info("ProviderFactory: Creating InternationalMarketDataProvider (Yahoo Finance US, ~15 min delay)")
        return InternationalMarketDataProvider()

    else:
        logger.warning(
            f"ProviderFactory: Unknown MARKET_DATA_PROVIDER='{provider_choice}'. "
            f"Defaulting to NSE_YFINANCE. Valid options: NSE_LIVE, BROKER_API, INTERNATIONAL_LIVE"
        )
        return NSEMarketDataProvider()


def create_bse_provider() -> BSEMarketDataProvider:
    """Always create a BSE provider (used alongside primary for SENSEX)."""
    return BSEMarketDataProvider()


def create_international_provider() -> InternationalMarketDataProvider:
    """Create international market data provider for US markets (NASDAQ / NYSE)."""
    return InternationalMarketDataProvider()


def _detect_broker_name() -> str:
    """
    Detect which broker is configured by checking which API key is set.
    Returns the broker identifier string used in .env variable naming.
    """
    # Check in priority order
    broker_checks = [
        ("ZERODHA_KITE", "ZERODHA_KITE_API_KEY"),
        ("UPSTOX",       "UPSTOX_API_KEY"),
        ("ANGEL_ONE",    "ANGEL_ONE_API_KEY"),
        ("DHAN",         "DHAN_CLIENT_ID"),
        ("SHOONYA",      "SHOONYA_API_KEY"),
    ]

    for broker_name, env_key in broker_checks:
        if os.getenv(env_key):
            logger.info(f"ProviderFactory: Detected broker credentials for {broker_name}")
            return broker_name

    # Generic fallback
    if os.getenv("BROKER_API_KEY"):
        logger.info("ProviderFactory: Using generic BROKER_API_KEY")
        return "GENERIC_BROKER"

    logger.warning(
        "ProviderFactory: BROKER_API selected but no broker credentials found. "
        "Falling back to NSE_YFINANCE. Set ZERODHA_KITE_API_KEY / UPSTOX_API_KEY / "
        "ANGEL_ONE_API_KEY / DHAN_CLIENT_ID in .env to enable real-time broker feed."
    )
    return "GENERIC_BROKER"


def validate_provider_is_not_paper(provider: MarketDataProvider, environment: str) -> None:
    """
    Runtime check: verifies the active provider is not a paper/mock provider in production.

    Raises:
        RuntimeError if paper provider detected in production
    """
    if environment.lower() != "production":
        return

    provider_name_upper = provider.provider_name.upper()
    for keyword in PAPER_PROVIDER_KEYWORDS:
        if keyword in provider_name_upper:
            raise RuntimeError(
                f"PRODUCTION SAFETY VIOLATION: Active market data provider "
                f"'{provider.provider_name}' appears to be a paper/mock/demo provider. "
                f"Paper providers are PROHIBITED in ENVIRONMENT=production. "
                f"Set MARKET_DATA_PROVIDER=NSE_LIVE or MARKET_DATA_PROVIDER=BROKER_API "
                f"with valid credentials."
            )
