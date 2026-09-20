from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional


class MarketDataProvider(ABC):
    """
    Abstract Base Class for all real-time market data providers.
    Providers can be:
    - BrokerProvider (Zerodha Kite, Upstox, Angel One, Dhan, Shoonya)
    - NSEMarketDataProvider (Indian Equities & Indices: NIFTY 50, NIFTY BANK, etc.)
    - BSEMarketDataProvider (SENSEX & BSE Equities)
    - InternationalMarketDataProvider (US Equities & Indices: NASDAQ, NYSE, S&P 500, etc.)
    """

    def __init__(self, provider_name: str):
        self.provider_name = provider_name
        self.is_connected = False
        self.subscribed_symbols: List[str] = []

    @abstractmethod
    def connect(self) -> bool:
        """Establish connection to the market data provider API or WebSocket."""
        pass

    @abstractmethod
    def disconnect(self):
        """Disconnect from market data provider."""
        pass

    @abstractmethod
    def subscribe(self, symbols: List[str]):
        """Subscribe to real-time tick updates for given symbols."""
        pass

    @abstractmethod
    def unsubscribe(self, symbols: List[str]):
        """Unsubscribe from given symbols."""
        pass

    @abstractmethod
    def get_quote(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Fetch normalized real-time quote for a single symbol."""
        pass

    @abstractmethod
    def get_quotes(self, symbols: List[str]) -> List[Dict[str, Any]]:
        """Fetch normalized real-time quotes for multiple symbols."""
        pass

    @abstractmethod
    def get_instruments(self) -> List[Dict[str, Any]]:
        """Fetch all dynamic instrument metadata from the provider."""
        pass

    @abstractmethod
    def get_historical_candles(self, symbol: str, timeframe: str = "1h", count: int = 100) -> List[Dict[str, Any]]:
        """Fetch real historical OHLCV candle bars."""
        pass

    def get_historical_data(self, symbol: str, timeframe: str = "1h", count: int = 100) -> List[Dict[str, Any]]:
        """Alias for get_historical_candles."""
        return self.get_historical_candles(symbol, timeframe, count)

    def getQuote(self, symbol: str) -> Optional[Dict[str, Any]]:
        """CamelCase alias matching specification."""
        return self.get_quote(symbol)

    def getQuotes(self, symbols: List[str]) -> List[Dict[str, Any]]:
        """CamelCase alias matching specification."""
        return self.get_quotes(symbols)

    def getHistoricalData(self, symbol: str, timeframe: str = "1h", count: int = 100) -> List[Dict[str, Any]]:
        """CamelCase alias matching specification."""
        return self.get_historical_data(symbol, timeframe, count)

    def getInstruments(self) -> List[Dict[str, Any]]:
        """CamelCase alias matching specification."""
        return self.get_instruments()

    def getMarketStatus(self) -> Dict[str, Any]:
        """CamelCase alias matching specification."""
        return self.get_market_status()

    @abstractmethod
    def get_market_status(self) -> Dict[str, Any]:
        """Fetch market session status from provider."""
        pass
