"""
AI Market Analysis, Probabilistic P&L Prediction & Trade Plan Schemas — TradePilot AI

CRITICAL SAFETY DIRECTIVE:
  - All predictions are purely probabilistic.
  - Zero claims of "Guaranteed Profit", "100% Accuracy", or "Risk Free".
  - Always output Profit Probability, Loss Probability, Expected P&L Range, Risk Score, and Confidence.
  - Every prediction must include the mandatory disclaimer:
    "AI predictions are probabilistic and do not guarantee future returns."
"""
from typing import List, Optional, Dict, Any
from enum import Enum
from pydantic import BaseModel, Field


class ConfidenceLevel(str, Enum):
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


class TradeAction(str, Enum):
    BUY = "BUY"
    WAIT = "WAIT"
    HOLD = "HOLD"
    SELL = "SELL"
    EXIT = "EXIT"
    NO_TRADE = "NO TRADE"


class PnLRange(BaseModel):
    min: float
    max: float


class PnLPredictionRequest(BaseModel):
    symbol: str = Field(..., min_length=1, max_length=20)
    direction: str = Field(default="BUY", pattern="^(BUY|SELL)$")
    entry_price: Optional[float] = Field(default=None, gt=0)
    quantity: float = Field(default=1.0, gt=0)
    stop_loss: Optional[float] = Field(default=None, gt=0)
    target: Optional[float] = Field(default=None, gt=0)
    trailing_stop_pct: Optional[float] = Field(default=None, ge=0.1, le=25.0)
    risk_limit: Optional[float] = Field(default=None, gt=0)


class PnLPredictionResponse(BaseModel):
    symbol: str
    direction: str
    current_price: float
    entry_price: float
    quantity: float
    profit_probability: float = Field(..., ge=0.0, le=1.0)
    loss_probability: float = Field(..., ge=0.0, le=1.0)
    expected_profit: float
    expected_loss: float
    expected_pnl: float
    expected_pnl_range: PnLRange
    risk_reward_ratio: float
    confidence: ConfidenceLevel
    confidence_score: float = Field(..., ge=0.0, le=100.0)
    risk_score: int = Field(..., ge=0, le=100)
    recommended_action: TradeAction
    reasons: List[str]
    disclaimer: str = "AI predictions are probabilistic and do not guarantee future returns."
    timestamp: str
    model_version: str = "tradepilot-probabilistic-v2.5"


class GenerateTradePlanRequest(BaseModel):
    symbol: str = Field(..., min_length=1, max_length=20)
    direction: Optional[str] = Field(default=None, pattern="^(BUY|SELL)?$")
    account_balance: Optional[float] = Field(default=100000.0, gt=0)
    risk_per_trade_pct: Optional[float] = Field(default=1.0, gt=0.0, le=10.0)
    timeframe: Optional[str] = Field(default="1h")


class AITradePlan(BaseModel):
    symbol: str
    direction: str
    entry_zone: str
    stop_loss: float
    target_1: float
    target_2: float
    target_3: Optional[float] = None
    trailing_stop_pct: float
    risk_reward_ratio: float
    profit_probability: float
    loss_probability: float
    confidence: ConfidenceLevel
    trade_score: int  # 0 - 100
    risk_score: int = Field(default=5, ge=1, le=10)
    decision: TradeAction
    market: str = "IN"
    currency: str = "INR"
    currency_symbol: str = "₹"
    current_price: Optional[float] = None
    order_type: str = "LIMIT"
    trigger_condition: Optional[str] = None
    suggested_quantity: Optional[float] = None
    max_capital_risk: Optional[float] = None
    reasons: List[str]
    buy_conditions: List[str]
    do_not_buy_conditions: List[str]
    disclaimer: str = "AI predictions are probabilistic and do not guarantee future returns."
    timestamp: str


class TimeframeAnalysis(BaseModel):
    timeframe: str
    horizon_label: str
    trend: str  # BULLISH, BEARISH, NEUTRAL
    momentum: str  # STRONG_BULL, WEAK_BULL, NEUTRAL, WEAK_BEAR, STRONG_BEAR
    rsi14: Optional[float] = None
    macd_crossover: Optional[str] = None
    ema_alignment: Optional[str] = None
    key_levels: Dict[str, Optional[float]] = {}
    bars_count: int = 0


class MultiTimeframeAnalysisResponse(BaseModel):
    symbol: str
    current_price: float
    currency_symbol: str = "₹"
    confluence_score: float = Field(..., ge=0.0, le=100.0)
    confluence_tier: str  # STRONG_CONFLUENCE, MODERATE_CONFLUENCE, WEAK_CONFLUENCE, NO_CONFLUENCE
    overall_trend: str  # BULLISH, BEARISH, CONSOLIDATION
    recommended_action: str  # STRONG_BUY, BUY, HOLD, SELL, STRONG_SELL, WAIT_FOR_CONFIRMATION
    timeframes: Dict[str, TimeframeAnalysis]
    risk_score: int = Field(..., ge=1, le=10)
    confidence_pct: float = Field(..., ge=0.0, le=100.0)
    reasons: List[str]
    disclaimer: str = "AI predictions are probabilistic and do not guarantee future returns."
    timestamp: str


class AITradeAnalysisResponse(BaseModel):
    symbol: str
    current_price: float
    currency_symbol: str = "₹"
    data_status: str  # LIVE, LIVE_DELAYED, STALE, DISCONNECTED
    trade_plan: AITradePlan
    prediction: PnLPredictionResponse
    multi_timeframe: Optional[MultiTimeframeAnalysisResponse] = None
    disclaimer: str = "AI predictions are probabilistic and do not guarantee future returns."
    timestamp: str


class AgentVote(BaseModel):
    agent_name: str  # Scout, Risk, Trade, Macro
    role: str
    decision: str  # BUY, SELL, HOLD, WAIT, REJECT
    conviction_pct: float = Field(..., ge=0.0, le=100.0)
    reasons: List[str] = []
    metrics: Dict[str, Any] = {}
    timestamp: str


class MultiAgentConsensusResponse(BaseModel):
    symbol: str
    market: str  # IN / US
    currency_symbol: str = "₹"
    current_price: float
    overall_recommendation: str  # STRONG_BUY, BUY, HOLD, SELL, STRONG_SELL, WAIT_FOR_CONFIRMATION, REJECT
    consensus_score: float = Field(..., ge=0.0, le=100.0)
    risk_score: int = Field(..., ge=1, le=10)
    confidence_pct: float = Field(..., ge=0.0, le=100.0)
    is_vetoed: bool = False
    veto_reason: Optional[str] = None
    agent_votes: Dict[str, AgentVote]
    suggested_trade_plan: Optional[AITradePlan] = None
    disclaimer: str = "AI predictions are probabilistic and do not guarantee future returns."
    timestamp: str

