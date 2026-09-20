"""
Phase 10 Test Suite: AI Multi-Agent Architecture
TradePilot AI

Tests:
1. 4 Specialized Agents:
   - Scout Agent: Technical patterns, RSI, volume, multi-timeframe confluence.
   - Risk Agent: ATR volatility, exposure limits, and VETO power.
   - Trade Agent: Order execution viability and tiered profit targets.
   - Macro Agent: Broad market sentiment and benchmark alignment.
2. Risk Agent VETO authority:
   - When volatility is extreme (ATR % > 4.5%), Risk Agent vetoes trade -> overall recommendation is REJECT.
3. Multi-Agent Consensus aggregation:
   - Weighted vote scoring and tiering (STRONG_BUY, BUY, HOLD, SELL, STRONG_SELL, WAIT_FOR_CONFIRMATION, REJECT).
4. Multi-market support:
   - Indian stocks (RELIANCE / INR / ₹).
   - US stocks (AAPL / USD / $).
5. REST Endpoints:
   - GET /api/v1/ai/agents/consensus/{symbol}
   - POST /api/v1/ai/agents/consensus (custom balance/risk parameters)
6. Probabilistic safety rules:
   - Zero guaranteed profit claims, presence of mandatory disclaimer.
"""
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.services.multi_agent_engine import (
    ScoutAgent,
    RiskAgent,
    TradeAgent,
    MacroAgent,
    get_multi_agent_consensus_engine,
)
from app.services.market_data.market_data_manager import get_market_data_manager

client = TestClient(app)


@pytest.fixture(scope="module", autouse=True)
def init_market_manager():
    mgr = get_market_data_manager()
    mgr.initialize()
    now_iso = "2026-09-12T06:00:00Z"
    mgr._cached_quotes["RELIANCE"] = {
        "symbol": "RELIANCE",
        "exchange": "NSE",
        "last_price": 2950.00,
        "open": 2930.00,
        "high": 2970.00,
        "low": 2920.00,
        "previous_close": 2930.00,
        "change": 20.00,
        "change_percent": 0.68,
        "volume": 3500000,
        "timestamp": now_iso,
        "data_status": "LIVE_DELAYED",
        "data_source": "TEST_FEED",
        "is_live": True,
    }
    mgr._cached_quotes["AAPL"] = {
        "symbol": "AAPL",
        "exchange": "NASDAQ",
        "last_price": 225.00,
        "open": 222.00,
        "high": 226.50,
        "low": 221.50,
        "previous_close": 222.00,
        "change": 3.00,
        "change_percent": 1.35,
        "volume": 42000000,
        "timestamp": now_iso,
        "data_status": "LIVE_DELAYED",
        "data_source": "TEST_FEED",
        "is_live": True,
    }


def test_individual_agents_evaluation():
    """Verify each specialized agent produces a valid AgentVote with role, conviction, and metrics."""
    scout = ScoutAgent()
    risk = RiskAgent()
    trade = TradeAgent()
    macro = MacroAgent()

    # Mock technical inputs
    bars = [{"close": 2950.0, "volume": 100000, "open": 2930.0, "high": 2970.0, "low": 2920.0}]
    tech = {"rsi": 58.0, "volume_surge_ratio": 1.4, "macd_cross": "BULLISH_CROSS", "atr14": 45.0}
    ml_pred = {"bullish_probability": 0.72, "bearish_probability": 0.28, "direction": "UP"}

    class MockMTF:
        confluence_score = 82.0
        overall_trend = "BULLISH"

    # Scout
    scout_vote = scout.evaluate("RELIANCE", bars, tech, ml_pred, MockMTF())
    assert scout_vote.agent_name == "Scout Agent"
    assert scout_vote.decision == "BUY"
    assert scout_vote.conviction_pct >= 65.0
    assert len(scout_vote.reasons) >= 1

    # Risk
    risk_vote = risk.evaluate("RELIANCE", 2950.0, tech, scout_vote, 100000.0, 1.0)
    assert risk_vote.agent_name == "Risk Agent"
    assert risk_vote.decision == "BUY"
    assert risk_vote.metrics["is_vetoed"] is False

    # Trade
    trade_vote = trade.evaluate("RELIANCE", 2950.0, scout_vote, risk_vote, 100000.0, 1.0)
    assert trade_vote.agent_name == "Trade Agent"
    assert trade_vote.decision == "BUY"
    assert trade_vote.conviction_pct > 50.0

    # Macro
    macro_vote = macro.evaluate("IN")
    assert macro_vote.agent_name == "Macro Agent"
    assert macro_vote.decision in ["BUY", "HOLD", "SELL"]
    assert macro_vote.conviction_pct > 0


def test_risk_agent_veto_authority():
    """Verify Risk Agent exercises VETO power when volatility is abnormally high."""
    scout = ScoutAgent()
    risk = RiskAgent()
    trade = TradeAgent()

    scout_vote = scout.evaluate("VOLATILE_STOCK", [], {"rsi": 65.0}, {"bullish_probability": 0.75}, None)
    
    # ATR is 10% of current price (200 / 2000), which exceeds 4.5% threshold
    high_vol_tech = {"atr14": 200.0}
    risk_vote = risk.evaluate("VOLATILE_STOCK", 2000.0, high_vol_tech, scout_vote)

    assert risk_vote.metrics["is_vetoed"] is True
    assert risk_vote.decision == "REJECT"
    assert "Abnormally high volatility" in risk_vote.reasons[0]

    # Trade Agent must abort when Risk Agent vetoes
    trade_vote = trade.evaluate("VOLATILE_STOCK", 2000.0, scout_vote, risk_vote)
    assert trade_vote.decision == "REJECT"
    assert "aborted" in trade_vote.reasons[0].lower()


def test_consensus_engine_indian_stock():
    """Verify consensus deliberation on an Indian instrument (RELIANCE)."""
    engine = get_multi_agent_consensus_engine()
    res = engine.run_consensus("RELIANCE", account_balance=250000.0, risk_per_trade_pct=1.5)

    assert res.symbol == "RELIANCE"
    assert res.market == "IN"
    assert res.currency_symbol == "₹"
    assert res.current_price > 0
    assert res.overall_recommendation in ["STRONG_BUY", "BUY", "HOLD", "SELL", "STRONG_SELL", "WAIT_FOR_CONFIRMATION", "REJECT"]
    assert 0.0 <= res.consensus_score <= 100.0
    assert 1 <= res.risk_score <= 10
    assert 0.0 <= res.confidence_pct <= 100.0

    # Ensure all 4 agents participated
    assert "scout" in res.agent_votes
    assert "risk" in res.agent_votes
    assert "trade" in res.agent_votes
    assert "macro" in res.agent_votes

    # Probabilistic guarantees
    assert res.disclaimer == "AI predictions are probabilistic and do not guarantee future returns."
    res_str = str(res.model_dump())
    assert "Guaranteed Profit" not in res_str
    assert "100% Accuracy" not in res_str


def test_consensus_engine_us_stock():
    """Verify consensus deliberation on a US instrument (AAPL)."""
    engine = get_multi_agent_consensus_engine()
    res = engine.run_consensus("AAPL", account_balance=50000.0, risk_per_trade_pct=2.0)

    assert res.symbol == "AAPL"
    assert res.market == "US"
    assert res.currency_symbol == "$"
    assert res.current_price > 0
    assert len(res.agent_votes) == 4


def test_rest_endpoint_consensus_get():
    """Test GET /api/v1/ai/agents/consensus/{symbol} endpoint."""
    resp = client.get("/api/v1/ai/agents/consensus/RELIANCE")
    assert resp.status_code == 200
    data = resp.json()

    assert data["symbol"] == "RELIANCE"
    assert "overall_recommendation" in data
    assert "consensus_score" in data
    assert "agent_votes" in data
    assert "scout" in data["agent_votes"]
    assert "risk" in data["agent_votes"]
    assert "trade" in data["agent_votes"]
    assert "macro" in data["agent_votes"]
    assert data["disclaimer"] == "AI predictions are probabilistic and do not guarantee future returns."


def test_rest_endpoint_consensus_post():
    """Test POST /api/v1/ai/agents/consensus endpoint with custom parameters."""
    payload = {
        "symbol": "AAPL",
        "account_balance": 75000.0,
        "risk_per_trade_pct": 1.2,
        "timeframe": "1h",
    }
    resp = client.post("/api/v1/ai/agents/consensus", json=payload)
    assert resp.status_code == 200
    data = resp.json()

    assert data["symbol"] == "AAPL"
    assert data["currency_symbol"] == "$"
    assert "overall_recommendation" in data
    assert "consensus_score" in data
    assert len(data["agent_votes"]) == 4
    assert data["disclaimer"] == "AI predictions are probabilistic and do not guarantee future returns."
