"""
Market Data Manager — TradePilot

Central orchestrator for all market data operations:
  - Coordinates live providers (NSE yfinance, BSE yfinance, Broker APIs)
  - Validates every incoming tick (freshness, price > 0, symbol integrity)
  - Caches real market quotes and detects stale feeds
  - Distributes real-time updates to WebSocket clients
  - Tracks feed health metrics
  - Manages NIFTY 50 and NIFTY BANK constituent subscriptions

DATA INTEGRITY GUARANTEE:
  - NEVER produces or falls back to mock/fake/random prices
  - When feed is down: returns stale cache (marked STALE) or None
  - UI responsibility: show "FEED DISCONNECTED" when price is None
  - Caller responsibility: show "DATA STALE" when data_status == "STALE"
"""
import os
import time
import logging
import asyncio
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional, Tuple

from app.services.market_data.base_provider import MarketDataProvider
from app.services.market_data.provider_factory import (
    create_primary_provider,
    create_bse_provider,
    create_international_provider,
    validate_provider_is_not_paper,
)
from app.services.market_data.instrument_manager import get_instrument_manager
from app.services.market_data.market_status_service import get_market_status_service
from app.services.market_data.websocket_manager import get_websocket_manager
from app.services.market_data.feed_health import get_feed_health_monitor
from app.services.market_data.nifty50_constituents import (
    get_nifty50_symbols,
    get_nifty_bank_symbols,
    NIFTY50_SYMBOLS,
    NIFTY_BANK_SYMBOLS,
)
from app.services.market_data.international_provider import INTERNATIONAL_INSTRUMENT_CATALOG
from app.services.market_data.crypto_provider import (
    get_crypto_provider,
    CryptoMarketDataProvider,
    CRYPTO_INSTRUMENT_CATALOG,
)
from app.services.market_data.data_quality_engine import (
    get_data_quality_engine,
    DataQualityEngine,
)

logger = logging.getLogger(__name__)

# Core indices always tracked
CORE_INDICES = ["NIFTY 50", "NIFTY BANK", "SENSEX", "INDIA VIX"]

# Core commodities & precious metals
CORE_COMMODITIES = ["GOLD", "SILVER", "GOLDBEES", "SILVERBEES"]

# Core NSE equities tracked by default (NIFTY 50 constituents + extras)
CORE_EQUITIES = list(NIFTY50_SYMBOLS)

# Core US & International Symbols
CORE_US_SYMBOLS = [item["symbol"] for item in INTERNATIONAL_INSTRUMENT_CATALOG]

# Core 24/7 Crypto Symbols
CORE_CRYPTO_SYMBOLS = [item["symbol"] for item in CRYPTO_INSTRUMENT_CATALOG] + [item["pair"] for item in CRYPTO_INSTRUMENT_CATALOG] + ["BITCOIN", "ETHEREUM", "SOLANA"]

# Staleness threshold from environment (default: 5 minutes)
QUOTE_STALE_SECONDS = int(os.getenv("QUOTE_STALE_SECONDS", "300"))
FEED_DISCONNECT_SECONDS = int(os.getenv("FEED_DISCONNECT_SECONDS", "300"))


class MarketDataManager:
    """
    Central Market Data Orchestrator for TradePilot AI.

    Coordinates:
    - Primary provider (NSE yfinance / Broker API)
    - BSE provider (SENSEX)
    - International provider (US Equities & Indices: NASDAQ / NYSE)
    """

    def __init__(self):
        self.environment = os.getenv("ENVIRONMENT", "production")
        self.provider_choice = os.getenv("MARKET_DATA_PROVIDER", "NSE_LIVE")

        # Providers — initialized but not yet connected
        self._primary_provider: Optional[MarketDataProvider] = None
        self._bse_provider: Optional[MarketDataProvider] = None
        self._international_provider: Optional[MarketDataProvider] = None
        self._crypto_provider: Optional[CryptoMarketDataProvider] = None

        self._cached_quotes: Dict[str, Dict[str, Any]] = {}
        self._last_tick_time: Dict[str, float] = {}
        self._candle_cache: Dict[Tuple[str, str, int], Tuple[float, List[Dict[str, Any]]]] = {}
        self._is_running = False
        self._bg_task: Optional[asyncio.Task] = None
        self._feed_health = get_feed_health_monitor()
        self._quality_engine: DataQualityEngine = get_data_quality_engine()
        self._redis_client = None
        self._redis_enabled = False
        self._previous_trends: Dict[str, str] = {}

    @property
    def active_provider(self) -> Optional[MarketDataProvider]:
        return self._primary_provider

    @property
    def international_provider(self) -> Optional[MarketDataProvider]:
        return self._international_provider

    @property
    def crypto_provider(self) -> Optional[CryptoMarketDataProvider]:
        return self._crypto_provider

    @property
    def quality_engine(self) -> DataQualityEngine:
        return self._quality_engine

    def initialize(self) -> None:
        """
        Initialize providers and connect.
        Called once at application startup.
        """
        env = self.environment.lower()
        logger.info(
            f"MarketDataManager: initializing in ENVIRONMENT={env} "
            f"with MARKET_DATA_PROVIDER={self.provider_choice}"
        )

        # Initialize Redis cache if configured
        redis_url = os.getenv("REDIS_URL")
        if redis_url:
            try:
                import redis
                self._redis_client = redis.Redis.from_url(redis_url, decode_responses=True, socket_timeout=1.5)
                self._redis_client.ping()
                self._redis_enabled = True
                logger.info(f"MarketDataManager: connected to Redis cache at {redis_url}")
            except Exception as e:
                logger.info(f"MarketDataManager: Redis offline or unreachable ({e}). Using in-memory fallback cache.")
                self._redis_enabled = False

        # Create providers via factory (handles production guard)
        self._primary_provider = create_primary_provider()
        self._bse_provider = create_bse_provider()
        self._international_provider = create_international_provider()
        self._crypto_provider = get_crypto_provider()

        # Production safety check
        validate_provider_is_not_paper(self._primary_provider, env)

        # Connect
        self._primary_provider.connect()
        self._bse_provider.connect()
        self._international_provider.connect()
        self._crypto_provider.connect()

        self._feed_health.set_provider(self._primary_provider.provider_name)
        self._feed_health.set_subscription_count(
            len(CORE_EQUITIES) + len(CORE_INDICES) + len(CORE_US_SYMBOLS) + len(CORE_CRYPTO_SYMBOLS)
        )

        logger.info(
            f"MarketDataManager: initialized. "
            f"Active primary: '{self._primary_provider.provider_name}' | "
            f"International: '{self._international_provider.provider_name}' | "
            f"Crypto 24/7: '{self._crypto_provider.provider_name}' | "
            f"Environment: {env}"
        )

    def get_market_status(self) -> Dict[str, Any]:
        """Return current market session status."""
        service = get_market_status_service()
        is_conn = self._primary_provider.is_connected if self._primary_provider else False
        status = service.get_session_status(is_feed_connected=is_conn)
        status["active_provider"] = self._primary_provider.provider_name if self._primary_provider else "NOT_INITIALIZED"
        status["data_delay_minutes"] = 15
        return status

    def validate_quote(self, quote: Optional[Dict[str, Any]]) -> Tuple[bool, Optional[Dict[str, Any]], str]:
        """
        Validate an incoming quote from the provider.

        Checks:
          1. Quote is not None
          2. Symbol is present
          3. Price is a positive number
          4. Timestamp is present

        Returns (is_valid, quote, message)
        """
        if not quote:
            return False, None, "Null quote object received"

        symbol = quote.get("symbol")
        if not symbol:
            self._feed_health.record_rejected_tick("UNKNOWN", "Missing symbol")
            return False, None, "Missing symbol in quote"

        price = quote.get("last_price")
        if price is None or not isinstance(price, (int, float)) or price <= 0:
            self._feed_health.record_rejected_tick(symbol, f"Invalid price: {price}")
            return False, None, f"Invalid non-positive market price ({price}) for {symbol}"

        ts = quote.get("timestamp")
        if not ts:
            self._feed_health.record_rejected_tick(symbol, "Missing timestamp")
            return False, None, f"Missing timestamp for {symbol}"

        # Check data_status — if STALE, still valid but track it
        if quote.get("data_status") == "STALE":
            self._feed_health.record_stale_tick(symbol)

        return True, quote, "Valid quote"

    def get_quote(self, symbol: str, force_refresh: bool = False) -> Optional[Dict[str, Any]]:
        """
        Get a normalized quote for a symbol.

        Returns:
            Quote with data_status="LIVE_DELAYED"  — from provider, ~15-20 min delayed
            Quote with data_status="STALE"          — from cache, provider temporarily unavailable
            None                                    — no data at all, show FEED DISCONNECTED

        NEVER returns a hardcoded or invented price.
        """
        if not self._primary_provider:
            return None

        clean_sym = (
            symbol.upper()
            .replace(".NS", "")
            .replace(".BO", "")
            .replace("NSE:", "")
            .replace("BSE:", "")
            .replace("NASDAQ:", "")
            .replace("NYSE:", "")
            .strip()
        )

        if not force_refresh and clean_sym in self._cached_quotes:
            last_t = self._last_tick_time.get(clean_sym, 0)
            if (time.time() - last_t) < 60.0:
                return self._cached_quotes[clean_sym]

        # Route Crypto 24/7 symbols to Crypto provider
        if (
            clean_sym in CORE_CRYPTO_SYMBOLS
            or symbol.startswith("CRYPTO:")
            or clean_sym.endswith("USDT")
            or clean_sym.endswith("-USD")
            or clean_sym in ["BTC", "ETH", "SOL", "BNB", "XRP", "DOGE", "ADA", "AVAX", "LINK", "DOT", "BITCOIN", "ETHEREUM"]
        ) and self._crypto_provider:
            raw_quote = self._crypto_provider.get_quote(clean_sym)
        # Route US / International symbols to International provider
        elif (clean_sym in CORE_US_SYMBOLS or symbol.startswith("NASDAQ:") or symbol.startswith("NYSE:")) and self._international_provider:
            raw_quote = self._international_provider.get_quote(clean_sym)
            if raw_quote:
                raw_quote.setdefault("currency_symbol", "$")
                raw_quote.setdefault("currency", "USD")
                raw_quote.setdefault("country", "United States")
        # Route BSE-specific symbols to BSE provider
        elif clean_sym in ["SENSEX", "BSESENSEX"] and self._bse_provider:
            raw_quote = self._bse_provider.get_quote(clean_sym)
        else:
            raw_quote = self._primary_provider.get_quote(clean_sym)

        # Fallback: return stale cache if provider returned None
        if raw_quote is None:
            if clean_sym in self._cached_quotes:
                cached = self._cached_quotes[clean_sym].copy()
                cached["data_status"] = "STALE"
                cached["is_live"] = False
                cached["data_source"] = f"{cached.get('data_source', 'UNKNOWN')} (STALE)"
                self._feed_health.record_stale_tick(clean_sym)
                return cached
            elif self._redis_enabled and self._redis_client:
                try:
                    import json
                    redis_val = self._redis_client.get(f"quote:{clean_sym}")
                    if redis_val:
                        cached = json.loads(redis_val)
                        cached["data_status"] = "STALE"
                        cached["is_live"] = False
                        self._feed_health.record_stale_tick(clean_sym)
                        return cached
                except Exception:
                    pass
            return None

        # Validate quote
        is_valid, validated_quote, reason = self.validate_quote(raw_quote)
        if not is_valid:
            logger.warning(f"MarketDataManager: rejected quote for '{clean_sym}': {reason}")
            return None

        # Real-time Bullish / Bearish Bias Detection & Auto-Refresh Trigger
        chg_pct = float(validated_quote.get("change_percent") or 0.0)
        movement = validated_quote.get("price_movement", "UNCHANGED")
        if chg_pct > 0.05 or movement == "UP":
            trend = "BULLISH"
        elif chg_pct < -0.05 or movement == "DOWN":
            trend = "BEARISH"
        else:
            trend = "NEUTRAL"

        prev_trend = self._previous_trends.get(clean_sym)
        regime_flipped = (prev_trend is not None and prev_trend != trend and trend in ["BULLISH", "BEARISH"])
        self._previous_trends[clean_sym] = trend

        validated_quote["trend"] = trend
        validated_quote["bias"] = trend
        validated_quote["regime_flipped"] = regime_flipped
        validated_quote["auto_refresh_trigger"] = trend if trend in ["BULLISH", "BEARISH"] else None

        # Track tick health & data quality
        self._feed_health.record_tick(clean_sym)
        self._quality_engine.record_tick(
            symbol=clean_sym,
            provider_name=validated_quote.get("data_source", "NSE_YFINANCE"),
            provider_timestamp=validated_quote.get("timestamp_unix") or time.time(),
        )

        # Update cache (in-memory + redis)
        self._cached_quotes[clean_sym] = validated_quote
        self._last_tick_time[clean_sym] = time.time()

        if self._redis_enabled and self._redis_client:
            try:
                import json
                self._redis_client.setex(f"quote:{clean_sym}", QUOTE_STALE_SECONDS, json.dumps(validated_quote))
                self._redis_client.publish("market:ticks", json.dumps({"symbol": clean_sym, "last_price": validated_quote.get("last_price")}))
            except Exception:
                pass

        return validated_quote

    def get_nifty50(self) -> Optional[Dict[str, Any]]:
        """Get live NIFTY 50 index quote."""
        return self.get_quote("NIFTY 50")

    def get_niftybank(self) -> Optional[Dict[str, Any]]:
        """Get live NIFTY BANK index quote."""
        return self.get_quote("NIFTY BANK")

    def get_sensex(self) -> Optional[Dict[str, Any]]:
        """Get live SENSEX index quote."""
        return self.get_quote("SENSEX")

    def get_nifty50_constituents_live(self) -> List[Dict[str, Any]]:
        """
        Get live quotes for all NIFTY 50 constituent stocks.
        Returns only stocks for which the provider has data.
        Excludes any stock where the provider returns None.
        """
        symbols = get_nifty50_symbols()
        return self.get_quotes(symbols)

    def get_nifty_bank_constituents_live(self) -> List[Dict[str, Any]]:
        """Get live quotes for all NIFTY BANK constituent stocks."""
        symbols = get_nifty_bank_symbols()
        return self.get_quotes(symbols)

    def get_gold(self) -> Optional[Dict[str, Any]]:
        """Get live GOLD quote (NSE GOLDBEES ETF)."""
        return self.get_quote("GOLD")

    def get_silver(self) -> Optional[Dict[str, Any]]:
        """Get live SILVER quote (NSE SILVERBEES ETF)."""
        return self.get_quote("SILVER")

    def get_commodities_live(self) -> List[Dict[str, Any]]:
        """Get live quotes for Gold and Silver commodities."""
        return self.get_quotes(["GOLD", "SILVER"])

    def get_us_indices(self) -> Dict[str, Any]:
        """Get live quotes for major US benchmark indices."""
        indices = {}
        target_indices = ["NASDAQ 100", "S&P 500", "DOW JONES", "US VIX"]
        for idx in target_indices:
            q = self.get_quote(idx)
            if q:
                indices[idx] = q
        return indices

    def get_us_quotes(self, symbols: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """Get live quotes for US equities and ETFs."""
        targets = symbols or [
            "AAPL", "MSFT", "NVDA", "GOOGL", "AMZN", "META", "TSLA",
            "SPY", "QQQ", "DIA", "XLK", "XLF"
        ]
        return self.get_quotes(targets)

    def get_international_instruments(self) -> List[Dict[str, Any]]:
        """Fetch all instruments supported by the international provider."""
        if self._international_provider:
            return self._international_provider.get_instruments()
        return list(INTERNATIONAL_INSTRUMENT_CATALOG)

    def get_crypto_quotes(self) -> List[Dict[str, Any]]:
        """Return all live 24/7 streaming crypto and Bitcoin quotes."""
        if self._crypto_provider:
            return self._crypto_provider.get_all_crypto_quotes()
        return []

    def get_crypto_quote(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Return single live 24/7 crypto quote."""
        if self._crypto_provider:
            return self._crypto_provider.get_quote(symbol)
        return None

    def get_crypto_instruments(self) -> List[Dict[str, Any]]:
        """Return catalog of tracked 24/7 crypto currencies."""
        return list(CRYPTO_INSTRUMENT_CATALOG)

    def get_quotes(self, symbols: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """
        Get live quotes for a list of symbols in parallel.
        If symbols is None, returns quotes for all tracked symbols.
        """
        from concurrent.futures import ThreadPoolExecutor
        target_symbols = symbols or (CORE_INDICES + CORE_COMMODITIES + CORE_EQUITIES)
        
        # Parallel fetch with thread pool
        with ThreadPoolExecutor(max_workers=min(12, len(target_symbols) or 1)) as executor:
            futures = [executor.submit(self.get_quote, s) for s in target_symbols]
            # Collect each result only once to avoid double-invoking f.result()
            raw_results = [f.result() for f in futures]
            results = [r for r in raw_results if r is not None]

        return results

    def get_all_quotes(self) -> List[Dict[str, Any]]:
        """Get quotes for all tracked indices, commodities, and NIFTY 50 equities."""
        return self.get_quotes(CORE_INDICES + CORE_COMMODITIES + CORE_EQUITIES)

    def get_historical_candles(
        self,
        symbol: str,
        timeframe: str = "1h",
        count: int = 100,
    ) -> List[Dict[str, Any]]:
        """
        Fetch real OHLCV candlestick bars from the active provider.
        Returns [] when unavailable — callers must handle empty list.
        """
        if not self._primary_provider:
            return []
        clean_sym = (
            symbol.upper()
            .replace(".NS", "")
            .replace(".BO", "")
            .replace("NSE:", "")
            .replace("BSE:", "")
            .replace("NASDAQ:", "")
            .replace("NYSE:", "")
            .strip()
        )

        cache_key = (clean_sym, timeframe, count)
        now = time.time()
        if hasattr(self, "_candle_cache") and cache_key in self._candle_cache:
            ts, cached_bars = self._candle_cache[cache_key]
            # 120s TTL for historical candles
            if (now - ts) < 120.0 and cached_bars:
                return cached_bars

        # Crypto symbols use 24/7 Crypto provider for history
        if (clean_sym in CORE_CRYPTO_SYMBOLS or clean_sym in ["BTC", "ETH", "SOL", "BNB", "XRP", "DOGE", "ADA", "AVAX", "LINK", "DOT"] or symbol.startswith("CRYPTO:")) and self._crypto_provider:
            bars = self._crypto_provider.get_crypto_candles(clean_sym, timeframe, count)
        # US symbols use International provider for history
        elif (clean_sym in CORE_US_SYMBOLS or symbol.startswith("NASDAQ:") or symbol.startswith("NYSE:")) and self._international_provider:
            bars = self._international_provider.get_historical_candles(clean_sym, timeframe, count)
        # BSE symbols use BSE provider for history
        elif clean_sym in ["SENSEX", "BSESENSEX"] and self._bse_provider:
            bars = self._bse_provider.get_historical_candles(clean_sym, timeframe, count)
        else:
            bars = self._primary_provider.get_historical_candles(clean_sym, timeframe, count)

        if bars:
            if not hasattr(self, "_candle_cache"):
                self._candle_cache = {}
            self._candle_cache[cache_key] = (now, bars)

        return bars

    def get_historical_candles_package(
        self,
        symbol: str,
        timeframe: str = "1h",
        count: int = 100,
    ) -> Dict[str, Any]:
        """
        Fetch dynamic historical candles package enriched with full technical indicators,
        cached with timeframe-based TTL, with zero synthetic data.
        """
        from app.services.market_data.candle_engine import get_historical_candles_package
        return get_historical_candles_package(symbol, timeframe=timeframe, count=count, manager=self)

    def get_feed_health(self) -> Dict[str, Any]:
        """Return feed health metrics."""
        is_conn = self._primary_provider.is_connected if self._primary_provider else False
        return self._feed_health.get_health_metrics(is_provider_connected=is_conn)

    def get_data_quality(self, symbol: Optional[str] = None) -> Dict[str, Any]:
        """
        Evaluate real-time data quality.
        If symbol is provided, returns symbol-level staleness/latency.
        Otherwise returns global feed status and AI recommendation safety.
        """
        if symbol:
            return self._quality_engine.evaluate_symbol_quality(symbol)
        m_status = self.get_market_status()
        is_open = m_status.get("status") == "OPEN"
        return self._quality_engine.evaluate_global_quality(is_market_open=is_open)

    def record_quote_tick(
        self,
        symbol: str,
        provider_name: str,
        provider_timestamp: Optional[float] = None,
        latency_ms: Optional[float] = None,
    ) -> Dict[str, Any]:
        """Explicitly record a tick into the Data Quality Engine."""
        return self._quality_engine.record_tick(
            symbol=symbol,
            provider_name=provider_name,
            provider_timestamp=provider_timestamp,
            latency_ms=latency_ms,
        )

    def get_crypto_quotes(self) -> List[Dict[str, Any]]:
        """Return real-time quotes for all major 24/7 cryptocurrencies."""
        if not self._crypto_provider:
            return []
        if hasattr(self._crypto_provider, "get_all_crypto_quotes"):
            return self._crypto_provider.get_all_crypto_quotes()
        return []

    def get_crypto_quote(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Return real-time quote for a specific cryptocurrency."""
        if not self._crypto_provider:
            return None
        return self._crypto_provider.get_quote(symbol)

    def get_crypto_instruments(self) -> List[Dict[str, Any]]:
        """Return metadata for all supported 24/7 crypto pairs."""
        if not self._crypto_provider:
            return []
        if hasattr(self._crypto_provider, "get_instruments"):
            return self._crypto_provider.get_instruments()
        return []

    async def start_background_stream(self) -> None:
        """
        Background task: continuously fetches and broadcasts live market quotes
        every second without blocking the asyncio event loop.
        Rotates through tracked symbols to provide true 1-second live streaming updates.
        """
        self._is_running = True
        ws_mgr = get_websocket_manager()
        stream_interval = float(os.getenv("STREAM_INTERVAL_SECONDS", "1.0"))

        logger.info(
            f"MarketDataManager: live 1-second background stream started in non-blocking thread pool. "
            f"Interval: {stream_interval}s"
        )

        # High-priority active tickers + rotation of remaining equities
        high_priority = ["NIFTY 50", "NIFTY BANK", "SENSEX", "RELIANCE", "TCS", "INFY", "HDFCBANK", "ICICIBANK", "GOLD", "SILVER", "BTC", "ETH", "AAPL"]
        all_equities = [s for s in CORE_EQUITIES if s not in high_priority]
        rotation_idx = 0

        while self._is_running:
            try:
                # Every second, fetch a high-priority ticker + 2 rotating equities
                hp_sym = high_priority[rotation_idx % len(high_priority)]
                rot_syms = [all_equities[(rotation_idx * 2 + i) % len(all_equities)] for i in range(2)]
                batch = [hp_sym] + rot_syms
                rotation_idx += 1

                quotes = await asyncio.to_thread(self.get_quotes, batch)
                for q in quotes:
                    if q:
                        await ws_mgr.broadcast_quote_update(q)

                # Broadcast market status every 5 seconds
                if rotation_idx % 5 == 0:
                    status = await asyncio.to_thread(self.get_market_status)
                    await ws_mgr.broadcast_market_status(status)

                await asyncio.sleep(stream_interval)

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"MarketDataManager: background stream error — {e}")
                await asyncio.sleep(1.0)

        logger.info("MarketDataManager: background stream stopped.")

    def stop_background_stream(self) -> None:
        self._is_running = False


# Module-level singleton
_manager = MarketDataManager()


def get_market_data_manager() -> MarketDataManager:
    return _manager
