"""
Phase 9 Test Suite: AI Trade Plan Generation Engine
TradePilot AI

Tests:
1. Trade plan generation with dynamic entry zone, multi-tier targets (Target 1, Target 2, Target 3), and stop loss.
2. Risk/Reward ratio calculation and validation across targets.
3. Position sizing computation based on virtual account balance and risk % per trade.
4. Pre-flight checklists: 5 explicit Buy conditions and 5 explicit Do-Not-Buy / Invalidation conditions.
5. Indian market (RELIANCE / INR / ₹) and US market (AAPL / USD / $) support.
6. Custom Trade Plan Generation via POST /api/v1/ai/generate-trade-plan.
7. Standard Trade Plan lookup via GET /api/v1/ai/trade-plan/{symbol}.
8. Probabilistic safety rules: zero guaranteed profit claims and presence of mandatory disclaimer.
"""
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.schemas.ai import GenerateTradePlanRequest, AITradePlan
from app.services.trade_plan_generator import generate_trade_plan
from app.services.market_data.market_data_manager import get_market_data_manager

client = TestClient(app)


@pytest.fixture(scope="module", autouse=True)
def init_market_manager():
    mgr = get_market_data_manager()
    mgr.initialize()
    # Populate test quotes in the manager's cache so tests run deterministically even when external network is throttled
    now_iso = "2026-09-08T14:30:00Z"
    mgr._cached_quotes["AAPL"] = {
        "symbol": "AAPL",
        "exchange": "NASDAQ",
        "last_price": 224.50,
        "open": 222.10,
        "high": 225.80,
        "low": 221.90,
        "previous_close": 222.00,
        "change": 2.50,
        "change_percent": 1.13,
        "volume": 45000000,
        "timestamp": now_iso,
        "data_status": "LIVE_DELAYED",
        "data_source": "TEST_FEED",
        "is_live": True,
    }
    mgr._cached_quotes["TCS"] = {
        "symbol": "TCS",
        "exchange": "NSE",
        "last_price": 4150.00,
        "open": 4120.00,
        "high": 4175.00,
        "low": 4110.00,
        "previous_close": 4120.00,
        "change": 30.00,
        "change_percent": 0.73,
        "volume": 1200000,
        "timestamp": now_iso,
        "data_status": "LIVE_DELAYED",
        "data_source": "TEST_FEED",
        "is_live": True,
    }
    mgr._cached_quotes["INFY"] = {
        "symbol": "INFY",
        "exchange": "NSE",
        "last_price": 1825.00,
        "open": 1810.00,
        "high": 1835.00,
        "low": 1805.00,
        "previous_close": 1810.00,
        "change": 15.00,
        "change_percent": 0.83,
        "volume": 2500000,
        "timestamp": now_iso,
        "data_status": "LIVE_DELAYED",
        "data_source": "TEST_FEED",
        "is_live": True,
    }


def test_generate_trade_plan_indian_stock():
    """Test generating a trade plan for an Indian equity (RELIANCE)."""
    plan = generate_trade_plan(
        symbol="RELIANCE",
        account_balance=200000.0,
        risk_per_trade_pct=1.5,
        timeframe="1h",
    )

    assert plan.symbol == "RELIANCE"
    assert plan.market == "IN"
    assert plan.currency == "INR"
    assert plan.currency_symbol == "₹"
    assert plan.current_price is not None and plan.current_price > 0
    assert "₹" in plan.entry_zone
    assert plan.stop_loss > 0
    assert plan.target_1 > 0
    assert plan.target_2 > 0
    assert plan.target_3 is not None and plan.target_3 > 0

    # If BUY, targets must be higher than stop loss and entry
    if plan.direction == "BUY":
        assert plan.target_1 > plan.stop_loss
        assert plan.target_2 > plan.target_1
        assert plan.target_3 > plan.target_2
    else:
        assert plan.target_1 < plan.stop_loss
        assert plan.target_2 < plan.target_1
        assert plan.target_3 < plan.target_2

    # Position sizing check
    assert plan.max_capital_risk == 3000.0  # 1.5% of 200,000 = 3000.0
    assert plan.suggested_quantity is not None and plan.suggested_quantity >= 1.0

    # Risk score between 1 and 10
    assert 1 <= plan.risk_score <= 10

    # Risk/Reward ratio
    assert plan.risk_reward_ratio > 0

    # Probabilistic guarantees
    assert plan.disclaimer == "AI predictions are probabilistic and do not guarantee future returns."
    plan_dict_str = str(plan.model_dump())
    assert "Guaranteed Profit" not in plan_dict_str
    assert "100% Accuracy" not in plan_dict_str


def test_generate_trade_plan_us_stock():
    """Test generating a trade plan for a US equity (AAPL)."""
    plan = generate_trade_plan(
        symbol="AAPL",
        account_balance=50000.0,
        risk_per_trade_pct=2.0,
        timeframe="1h",
    )

    assert plan.symbol == "AAPL"
    assert plan.market == "US"
    assert plan.currency == "USD"
    assert plan.currency_symbol == "$"
    assert plan.current_price is not None and plan.current_price > 0
    assert "$" in plan.entry_zone
    assert plan.max_capital_risk == 1000.0  # 2% of 50,000 = 1000.0
    assert plan.suggested_quantity is not None and plan.suggested_quantity > 0
    assert plan.target_3 is not None


def test_checklists_and_conditions():
    """Validate 5 Buy conditions and 5 Do-Not-Buy conditions."""
    plan = generate_trade_plan("TCS")

    # 5 explicit buy conditions
    assert len(plan.buy_conditions) == 5
    assert any("entry zone" in c.lower() for c in plan.buy_conditions)
    assert any("stop loss" in c.lower() for c in plan.buy_conditions)
    assert any("volume" in c.lower() for c in plan.buy_conditions)

    # 5 explicit do-not-buy conditions
    assert len(plan.do_not_buy_conditions) == 5
    assert any("stale" in c.lower() or "disconnected" in c.lower() for c in plan.do_not_buy_conditions)
    assert any("invalidation" in c.lower() for c in plan.do_not_buy_conditions)
    assert any("risk" in c.lower() for c in plan.do_not_buy_conditions)


def test_custom_trade_plan_post_endpoint():
    """Test POST /api/v1/ai/generate-trade-plan endpoint."""
    payload = {
        "symbol": "INFY",
        "direction": "BUY",
        "account_balance": 150000.0,
        "risk_per_trade_pct": 1.0,
        "timeframe": "1h",
    }
    resp = client.post("/api/v1/ai/generate-trade-plan", json=payload)
    assert resp.status_code == 200
    data = resp.json()

    assert data["symbol"] == "INFY"
    assert data["direction"] == "BUY"
    assert data["max_capital_risk"] == 1500.0  # 1% of 150000 = 1500.0
    assert data["suggested_quantity"] >= 1.0
    assert data["target_1"] is not None
    assert data["target_2"] is not None
    assert data["target_3"] is not None
    assert data["disclaimer"] == "AI predictions are probabilistic and do not guarantee future returns."


def test_get_trade_plan_endpoint():
    """Test GET /api/v1/ai/trade-plan/{symbol} endpoint."""
    resp = client.get("/api/v1/ai/trade-plan/RELIANCE")
    assert resp.status_code == 200
    data = resp.json()

    assert data["symbol"] == "RELIANCE"
    assert "target_1" in data
    assert "target_2" in data
    assert "target_3" in data
    assert "suggested_quantity" in data
    assert "buy_conditions" in data
    assert "do_not_buy_conditions" in data
    assert len(data["buy_conditions"]) == 5
    assert len(data["do_not_buy_conditions"]) == 5
    assert data["disclaimer"] == "AI predictions are probabilistic and do not guarantee future returns."
