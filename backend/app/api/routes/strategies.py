from fastapi import APIRouter

router = APIRouter(prefix="/strategies", tags=["strategies"])


@router.get("")
def strategies():
    return [
        {"name": "Momentum Scout", "style": "Trend following", "confidence": 78, "symbols": ["NVDA", "AAPL"], "status": "READY"},
        {"name": "Balanced Swing", "style": "Multi-factor", "confidence": 68, "symbols": ["MSFT", "AMD"], "status": "READY"},
        {"name": "Defensive Income", "style": "Risk managed", "confidence": 54, "symbols": ["SPY", "MSFT"], "status": "READY"},
    ]


@router.get("/{name}/analysis")
def strategy_analysis(name: str):
    return {"name": name, "score": 78, "recommendation": "Consider a long NVDA entry", "support": 134.50, "target_low": 146.00, "target_high": 149.00, "factors": {"trend": "Strong", "momentum": "Strong", "sentiment": "Neutral", "volatility": "Elevated"}}
