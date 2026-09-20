from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


# --- Market & Data Layer Schemas ---

class OrderBookLevel(BaseModel):
    price: float
    quantity: float
    orders_count: int


class OrderBookDepth(BaseModel):
    symbol: str
    timestamp: str
    bids: List[OrderBookLevel]
    asks: List[OrderBookLevel]
    spread: float
    spread_pct: float
    imbalance_pct: float  # (bids_vol - asks_vol) / (bids_vol + asks_vol)


class CandleBar(BaseModel):
    timestamp: str
    time: int
    open: float
    high: float
    low: float
    close: float
    volume: float
    vwap: Optional[float] = None
    sma20: Optional[float] = None
    ema21: Optional[float] = None
    upper_bb: Optional[float] = None
    lower_bb: Optional[float] = None


class MarketQuote(BaseModel):
    symbol: str
    name: Optional[str] = ""
    exchange: Optional[str] = "NSE"
    price: Optional[float] = None
    open: Optional[float] = 0.0
    high: Optional[float] = 0.0
    low: Optional[float] = 0.0
    previous_close: Optional[float] = 0.0
    change: Optional[float] = 0.0
    change_percent: Optional[float] = 0.0
    volume: Optional[int] = 0
    avg_volume: Optional[int] = 0
    market_cap: Optional[str] = "N/A"
    pe_ratio: Optional[float] = 0.0
    day_52w_high: Optional[float] = 0.0
    day_52w_low: Optional[float] = 0.0
    vwap: Optional[float] = 0.0
    rsi: Optional[float] = 50.0
    trend: Optional[str] = "NEUTRAL"  # BULLISH, BEARISH, NEUTRAL
    bias: Optional[str] = "NEUTRAL"
    regime_flipped: Optional[bool] = False
    auto_refresh_trigger: Optional[str] = None
    sentiment_score: Optional[float] = 0.0
    sparkline: List[float] = Field(default_factory=list)
    data_source: Optional[str] = "LIVE"
    is_live: Optional[bool] = True
    timestamp: Optional[str] = None


class CorporateAction(BaseModel):
    symbol: str
    action_type: str  # DIVIDEND, SPLIT, EARNINGS
    description: str
    ex_date: str
    record_date: Optional[str] = None
    details: Dict[str, Any] = Field(default_factory=dict)


class MacroIndicator(BaseModel):
    name: str
    category: str
    value: float
    unit: str
    previous_value: float
    change: float
    trend: str
    impact: str  # HIGH, MEDIUM, LOW
    release_date: str


# --- Feature Engineering & Technicals ---

class TechnicalIndicators(BaseModel):
    symbol: str
    current_price: float
    sma20: float
    sma50: float
    sma200: float
    ema9: float
    ema21: float
    ema55: float
    vwap: float
    rsi: float
    rsi_signal: str  # OVERBOUGHT, OVERSOLD, NEUTRAL
    macd_line: float
    macd_signal: float
    macd_hist: float
    macd_cross: str  # BULLISH_CROSS, BEARISH_CROSS, NONE
    bb_upper: float
    bb_middle: float
    bb_lower: float
    bb_pct_b: float
    bb_bandwidth: float
    atr14: float
    supertrend: float
    supertrend_direction: str  # BULLISH, BEARISH
    stoch_k: float
    stoch_d: float
    obv: float
    volume_surge_ratio: float
    regime: str  # TRENDING_BULL, TRENDING_BEAR, CONSOLIDATION, BREAKOUT


# --- AI & Analytics Engine Schemas ---

class FeatureImportance(BaseModel):
    feature: str
    importance: float
    category: str


class MLPrediction(BaseModel):
    symbol: str
    current_price: float
    lstm_predicted_target: float
    lstm_expected_return_pct: float
    lstm_forecast_path: List[float]
    rf_direction: str  # BULLISH, BEARISH, NEUTRAL
    rf_bullish_prob: float
    rf_bearish_prob: float
    rf_neutral_prob: float
    ensemble_conviction: int  # 0 - 100
    confidence_interval_low: float
    confidence_interval_high: float
    top_features: List[FeatureImportance]
    rationale: str
    updated_at: str


class NewsArticle(BaseModel):
    id: str
    headline: str
    source: str
    summary: str
    url: Optional[str] = None
    sentiment_score: float  # -1.0 to +1.0
    sentiment_label: str    # BULLISH, BEARISH, NEUTRAL
    impact_level: str       # HIGH, MEDIUM, LOW
    related_symbols: List[str]
    published_at: str


class SentimentSummary(BaseModel):
    overall_market_mood: str  # Extreme Fear, Fear, Neutral, Greed, Extreme Greed
    market_mood_score: int    # 0 - 100
    bullish_articles_pct: float
    bearish_articles_pct: float
    neutral_articles_pct: float
    trending_topics: List[str]
    symbol_sentiments: Dict[str, float]


class ScannerResult(BaseModel):
    symbol: str
    pattern: str
    category: str  # GAINER, LOSER, BREAKOUT, VOLUME, RSI, MACD, CANDLESTICK, CONFLUENCE
    timeframe: str
    confidence: int
    signal_type: str  # BUY, SELL, WATCH
    change_percent: float
    volume_ratio: float
    current_price: Optional[float] = None
    market: str = "IN"  # IN / US
    currency_symbol: str = "₹"
    risk_score: int = 5
    detail: str


# --- Backtesting Schemas ---

class BacktestRequest(BaseModel):
    strategy_name: str
    symbol: str
    timeframe: str = "1h"
    days_lookback: int = 60
    starting_capital: float = 100000.0
    risk_per_trade_pct: float = 2.0
    slippage_pct: float = 0.05
    commission_per_trade: float = 1.50
    stop_loss_pct: float = 2.5
    take_profit_pct: float = 5.0
    trailing_stop: bool = True


class BacktestTrade(BaseModel):
    id: str
    symbol: str
    side: str
    entry_time: str
    exit_time: str
    entry_price: float
    exit_price: float
    quantity: float
    pnl: float
    pnl_percent: float
    exit_reason: str


class EquityPoint(BaseModel):
    time: str
    equity: float
    drawdown_pct: float
    benchmark_equity: float


class BacktestResponse(BaseModel):
    strategy_name: str
    symbol: str
    total_return_pct: float
    cagr_pct: float
    benchmark_return_pct: float
    sharpe_ratio: float
    sortino_ratio: float
    max_drawdown_pct: float
    win_rate_pct: float
    profit_factor: float
    total_trades: int
    winning_trades: int
    losing_trades: int
    avg_trade_pnl: float
    avg_win: float
    avg_loss: float
    max_consecutive_wins: int
    max_consecutive_losses: int
    equity_curve: List[EquityPoint]
    trades: List[BacktestTrade]


# --- Trade & Order Schemas ---

class TradeRequest(BaseModel):
    symbol: str = Field(min_length=1, max_length=12)
    side: str = Field(pattern="^(BUY|SELL)$")
    order_type: str = Field(default="MARKET", pattern="^(MARKET|LIMIT|STOP_LIMIT)$")
    quantity: float = Field(gt=0)
    price: Optional[float] = None
    stop_loss: Optional[float] = Field(default=None, gt=0)
    take_profit: Optional[float] = Field(default=None, gt=0)
    trailing_stop_pct: Optional[float] = Field(default=None, gt=0)
    max_loss: Optional[float] = Field(default=None, gt=0)
    broker: Optional[str] = "ZERODHA_KITE"
    strategy: Optional[str] = "User Trade Config"


# Alias for backward compatibility
OrderCreateRequest = TradeRequest


class CloseTradeRequest(BaseModel):
    quantity: Optional[float] = Field(default=None, gt=0)
    reason: Optional[str] = "MANUAL"


class UpdatePositionLevelsRequest(BaseModel):
    stop_loss: Optional[float] = Field(default=None, gt=0)
    take_profit: Optional[float] = Field(default=None, gt=0)
    trailing_stop: Optional[float] = Field(default=None, gt=0)


class PositionResponse(BaseModel):
    symbol: str
    side: str
    quantity: float
    entry_price: float
    current_price: float
    market_value: float
    unrealized_pnl: float
    pnl_percent: float
    stop_loss: float
    trailing_stop: float
    take_profit: float
    take_profit_2: Optional[float] = None
    risk_level: str
    break_even_activated: bool
    opened_at: str


class PortfolioResponse(BaseModel):
    equity: float
    cash: float
    starting_capital: float
    total_pnl: float
    daily_pnl: float
    realized_pnl: float
    unrealized_pnl: float
    win_rate: float
    profit_factor: float
    total_trades_count: int
    open_positions_count: int
    margin_used: float
    margin_available: float
    positions: List[PositionResponse]


class RiskSettingsUpdateRequest(BaseModel):
    max_portfolio_risk_pct: Optional[float] = Field(default=None, ge=10, le=100)
    max_single_position_pct: Optional[float] = Field(default=None, ge=5, le=50)
    max_daily_loss: Optional[float] = Field(default=None, ge=500)
    default_stop_loss_pct: Optional[float] = Field(default=None, ge=0.5, le=15)
    default_take_profit_pct: Optional[float] = Field(default=None, ge=1.0, le=30)
    trailing_stop_enabled: Optional[bool] = None
    auto_break_even_pct: Optional[float] = Field(default=None, ge=0.5, le=5)
    kelly_fraction: Optional[float] = Field(default=None, ge=0.1, le=1.0)


class RiskResponse(BaseModel):
    score: int
    label: str
    exposure: float
    exposure_pct: float
    max_drawdown: float
    max_daily_loss: float
    daily_loss_current: float
    var_95_pct: float  # Value at Risk 95%
    alerts: List[str]
    guardrails: List[Dict[str, Any]]


class AISignal(BaseModel):
    id: str
    symbol: str
    action: str  # BUY, SELL, HOLD
    strategy_name: str
    conviction: int
    entry_price: float
    stop_loss: float
    take_profit_1: float
    take_profit_2: float
    risk_reward_ratio: float
    timeframe: str
    expected_duration: str
    rationale: str
    status: str  # ACTIVE, EXECUTED, EXPIRED
    generated_at: str


# --- Autonomous Trade Manager & Safety Schemas (Phases 12 - 21) ---

class TradeManagerEvaluateRequest(BaseModel):
    symbol: str
    side: str = Field(default="BUY", pattern="^(BUY|SELL)$")
    entry_price: float = Field(gt=0)
    current_price: float = Field(gt=0)
    stop_loss: float = Field(gt=0)
    trailing_stop: Optional[float] = None
    take_profit: float = Field(gt=0)
    take_profit_2: Optional[float] = None
    highest_price: Optional[float] = None
    lowest_price: Optional[float] = None
    quantity: float = 1.0
    max_loss: Optional[float] = None


class TradeManagerEvaluateResponse(BaseModel):
    symbol: str
    branch: str  # PROFIT_MANAGER | LOSS_MANAGER
    decision: str  # HOLD | TRAIL_STOP | PARTIAL_EXIT | TARGET_EXIT | RECOVER_WATCH | EXIT
    pnl_state: str  # PROFIT | LOSS
    new_stop: float
    new_high: float
    new_low: float
    detail: str
    disclaimer: str = "AI predictions and management rules are probabilistic and do not guarantee future returns."


class AlertCreateRequest(BaseModel):
    symbol: str
    alert_type: str = Field(default="PRICE_ABOVE", description="PRICE_ABOVE, PRICE_BELOW, RSI_OVERBOUGHT, RSI_OVERSOLD, BREAKOUT, RISK_DRAWDOWN")
    target_value: float
    notes: Optional[str] = None
    severity: Optional[str] = "yellow"

