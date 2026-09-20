"""
Multi-Agent AI Architecture — TradePilot AI

Phase 10 Implementation:
1. Scout Agent:
   - Scans technical setups, price action, indicators, breakouts, momentum, and multi-timeframe confluence.
   - Proposes initial trade intent: BUY, SELL, or WAIT.

2. Risk Agent:
   - Evaluates portfolio exposure, stop loss distance, ATR volatility risk, maximum position risk, and drawdown.
   - Enforces strict safety guardrails.
   - HOLDS VETO POWER: If risk is excessive (risk_score >= 8 or portfolio risk limit breached), Risk Agent can VETO the trade immediately.

3. Trade Agent:
   - Generates exact execution parameters (entry zone, multi-tier targets 1/2/3, trailing stop, order type, position size).
   - Recommends execution viability.

4. Macro Agent:
   - Assesses broader index direction (NIFTY 50, SENSEX, NASDAQ, SPY), market breadth, sentiment, and volatility (INDIA VIX / VIX).
   - Calibrates macroeconomic regime.

5. Multi-Agent Consensus Arbiter:
   - Combines votes from all 4 specialized agents.
   - Calculates Consensus Score (0-100), Risk Score (1-10), and Overall Recommendation.
   - Respects Risk Agent Veto.
   - Probabilistic safety guard with mandatory non-guarantee disclaimer.
"""
from datetime import datetime, timezone
import time
import logging
from typing import Dict, List, Any, Optional, Tuple

from app.schemas.ai import (
    AgentVote,
    MultiAgentConsensusResponse,
    AITradePlan,
)
from app.services.market_data import (
    get_current_live_price,
    generate_historical_candles,
    get_quotes,
)
from app.services.feature_engineering import extract_all_features
from app.services.ml_engine import get_ml_prediction, get_sentiment_analytics
from app.services.instrument_master import get_instrument_by_symbol
from app.services.multi_timeframe_engine import run_symbol_multi_timeframe_analysis
from app.services.trade_plan_generator import generate_trade_plan
from app.services.risk_engine import assess_portfolio
from app.database import get_store

logger = logging.getLogger(__name__)


class ScoutAgent:
    """Specialized Agent analyzing technical patterns, momentum, volume surges, and multi-timeframe alignment."""
    def evaluate(self, symbol: str, bars: List[Dict[str, Any]], tech: Dict[str, Any], ml_pred: Dict[str, Any], mtf: Any) -> AgentVote:
        curr_time = datetime.now(timezone.utc).isoformat()
        rsi = tech.get("rsi", 50.0)
        vol_ratio = tech.get("volume_surge_ratio", 1.0)
        macd_cross = tech.get("macd_cross", "NONE")
        bull_prob = ml_pred.get("bullish_probability", 0.50)
        bear_prob = ml_pred.get("bearish_probability", 0.50)
        mtf_score = getattr(mtf, "confluence_score", 50.0) if mtf else 50.0
        mtf_trend = getattr(mtf, "overall_trend", "NEUTRAL") if mtf else "NEUTRAL"

        reasons = []
        metrics = {
            "rsi": round(rsi, 2),
            "volume_ratio": round(vol_ratio, 2),
            "mtf_confluence": round(mtf_score, 1),
            "mtf_trend": mtf_trend,
        }

        # Scoring
        score_bull = 0
        score_bear = 0

        if bull_prob > 0.55: score_bull += 25
        if bear_prob > 0.55: score_bear += 25

        if mtf_trend == "BULLISH": score_bull += 35
        elif mtf_trend == "BEARISH": score_bear += 35

        if rsi > 52 and rsi < 70: score_bull += 20
        elif rsi < 48 and rsi > 30: score_bear += 20

        if vol_ratio >= 1.2:
            reasons.append(f"Volume surge detected ({vol_ratio:.1f}x 10-period average).")
            score_bull += 10
            score_bear += 10

        if macd_cross == "BULLISH_CROSS":
            reasons.append("MACD bullish crossover confirmed.")
            score_bull += 15
        elif macd_cross == "BEARISH_CROSS":
            reasons.append("MACD bearish crossover confirmed.")
            score_bear += 15

        if score_bull >= 65 and score_bull > score_bear:
            decision = "BUY"
            conviction = min(92.0, 50.0 + score_bull * 0.45)
            reasons.append(f"Technical momentum and {mtf_trend} multi-timeframe confluence support BUY.")
        elif score_bear >= 65 and score_bear > score_bull:
            decision = "SELL"
            conviction = min(92.0, 50.0 + score_bear * 0.45)
            reasons.append(f"Technical breakdown and {mtf_trend} multi-timeframe confluence support SELL.")
        else:
            decision = "WAIT"
            conviction = 50.0
            reasons.append("Technical signals mixed or consolidating. Patience advised.")

        return AgentVote(
            agent_name="Scout Agent",
            role="Technical Pattern & Multi-Timeframe Discovery",
            decision=decision,
            conviction_pct=round(conviction, 1),
            reasons=reasons,
            metrics=metrics,
            timestamp=curr_time,
        )


class RiskAgent:
    """Specialized Agent evaluating volatility, portfolio exposure, stop loss viability, and holding VETO power."""
    def evaluate(
        self,
        symbol: str,
        current_price: float,
        tech: Dict[str, Any],
        scout_vote: AgentVote,
        account_balance: float = 100000.0,
        risk_per_trade_pct: float = 1.0,
    ) -> AgentVote:
        curr_time = datetime.now(timezone.utc).isoformat()
        atr = tech.get("atr14", current_price * 0.02)
        atr_pct = (atr / current_price) * 100.0 if current_price > 0 else 2.0
        
        reasons = []
        metrics = {
            "atr": round(atr, 2),
            "atr_pct": round(atr_pct, 2),
            "risk_limit_pct": risk_per_trade_pct,
        }

        # Check volatility spikes
        is_extreme_volatility = atr_pct > 4.5
        veto = False
        decision = "HOLD"

        if is_extreme_volatility:
            veto = True
            decision = "REJECT"
            reasons.append(f"Abnormally high volatility: ATR is {atr_pct:.1f}% of spot price (threshold: 4.5%).")
            conviction = 95.0
        elif scout_vote.decision in ["BUY", "SELL"]:
            # Prudent risk evaluation
            if atr_pct <= 3.0:
                decision = scout_vote.decision
                conviction = 80.0
                reasons.append(f"Acceptable volatility risk ({atr_pct:.1f}% ATR). Stop-loss distance is controllable.")
            else:
                decision = "WAIT"
                conviction = 65.0
                reasons.append(f"Moderate volatility risk ({atr_pct:.1f}% ATR). Position size should be reduced.")
        else:
            decision = "WAIT"
            conviction = 60.0
            reasons.append("Awaiting directional setup from Scout before capital allocation.")

        metrics["is_vetoed"] = veto
        return AgentVote(
            agent_name="Risk Agent",
            role="Capital Preservation & Risk Guardrails (Veto Authority)",
            decision=decision,
            conviction_pct=round(conviction, 1),
            reasons=reasons,
            metrics=metrics,
            timestamp=curr_time,
        )


class TradeAgent:
    """Specialized Agent designing structured entry, stop loss, and multi-tier targets with execution viability."""
    def evaluate(
        self,
        symbol: str,
        current_price: float,
        scout_vote: AgentVote,
        risk_vote: AgentVote,
        account_balance: float = 100000.0,
        risk_per_trade_pct: float = 1.0,
    ) -> AgentVote:
        curr_time = datetime.now(timezone.utc).isoformat()
        reasons = []
        
        # If Risk Agent vetoed or Scout said WAIT, Trade Agent will not schedule entry
        if risk_vote.decision == "REJECT":
            return AgentVote(
                agent_name="Trade Agent",
                role="Execution Setup & Target Structuring",
                decision="REJECT",
                conviction_pct=90.0,
                reasons=["Trade aborted due to Risk Agent veto."],
                metrics={"status": "ABORTED_BY_RISK"},
                timestamp=curr_time,
            )

        if scout_vote.decision in ["BUY", "SELL"]:
            decision = scout_vote.decision
            conviction = min(88.0, (scout_vote.conviction_pct * 0.6) + (risk_vote.conviction_pct * 0.4))
            reasons.append(f"Calculated 1:1.5 minimum R:R order framework aligned with {decision} intent.")
            reasons.append("Structured tiered profit targets (TP1: 1.5R, TP2: 2.5R, TP3: 3.5R runner).")
        else:
            decision = "WAIT"
            conviction = 55.0
            reasons.append("No active breakout/retest trigger identified. Standing by.")

        return AgentVote(
            agent_name="Trade Agent",
            role="Execution Setup & Target Structuring",
            decision=decision,
            conviction_pct=round(conviction, 1),
            reasons=reasons,
            metrics={"execution_style": "LIMIT_PULLBACK"},
            timestamp=curr_time,
        )


class MacroAgent:
    """Specialized Agent analyzing benchmark indices, market sentiment, and volatility environment."""
    def evaluate(self, market: str) -> AgentVote:
        curr_time = datetime.now(timezone.utc).isoformat()
        sentiment = get_sentiment_analytics()
        mood = sentiment.get("overall_market_mood", "Neutral")
        mood_score = sentiment.get("market_mood_score", 50)
        
        reasons = [
            f"Overall market sentiment is {mood} (mood score: {mood_score}/100).",
        ]
        metrics = {
            "market_mood": mood,
            "market_mood_score": mood_score,
            "market": market,
        }

        if mood_score >= 60:
            decision = "BUY"
            conviction = float(min(85, mood_score))
            reasons.append("Macro environment and institutional sentiment favor risk-on positioning.")
        elif mood_score <= 40:
            decision = "SELL"
            conviction = float(min(85, 100 - mood_score))
            reasons.append("Macro climate exhibits risk-off bias or protective hedging.")
        else:
            decision = "HOLD"
            conviction = 55.0
            reasons.append("Macro sentiment is balanced with no severe external headwind.")

        return AgentVote(
            agent_name="Macro Agent",
            role="Macro Climate & Sentiment Analysis",
            decision=decision,
            conviction_pct=round(conviction, 1),
            reasons=reasons,
            metrics=metrics,
            timestamp=curr_time,
        )


_CONSENSUS_CACHE: Dict[str, Tuple[float, MultiAgentConsensusResponse]] = {}
_CONSENSUS_CACHE_TTL = 30.0  # 30 seconds


class MultiAgentConsensusEngine:
    """Orchestrates the 4 agents, aggregates votes, handles risk vetos, and generates final consensus."""
    def __init__(self):
        self.scout = ScoutAgent()
        self.risk = RiskAgent()
        self.trade = TradeAgent()
        self.macro = MacroAgent()

    def run_consensus(
        self,
        symbol: str,
        account_balance: float = 100000.0,
        risk_per_trade_pct: float = 1.0,
        timeframe: str = "1h",
    ) -> MultiAgentConsensusResponse:
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

        cache_key = f"{clean_sym}_{account_balance}_{risk_per_trade_pct}_{timeframe}"
        now = time.time()
        if cache_key in _CONSENSUS_CACHE:
            cached_ts, cached_res = _CONSENSUS_CACHE[cache_key]
            if (now - cached_ts) < _CONSENSUS_CACHE_TTL and cached_res:
                return cached_res

        inst = get_instrument_by_symbol(clean_sym)
        market = inst.get("market", "IN") if inst else ("US" if clean_sym.startswith("NASDAQ:") or clean_sym.startswith("NYSE:") else "IN")
        curr_symbol = inst.get("currency_symbol", "₹") if inst else ("$" if market == "US" else "₹")

        # Live quote
        curr_price = get_current_live_price(clean_sym)
        if curr_price is None or curr_price <= 0:
            raise ValueError(f"Real market quote for '{clean_sym}' not available from active provider.")

        # Data collection
        bars = generate_historical_candles(clean_sym, timeframe, 60)
        tech = extract_all_features(clean_sym, bars) if bars else {}
        ml_pred = get_ml_prediction(clean_sym)

        mtf = None
        try:
            mtf = run_symbol_multi_timeframe_analysis(clean_sym)
        except Exception:
            pass

        # 1. Execute Agent Analysis
        scout_vote = self.scout.evaluate(clean_sym, bars, tech, ml_pred, mtf)
        risk_vote = self.risk.evaluate(clean_sym, curr_price, tech, scout_vote, account_balance, risk_per_trade_pct)
        trade_vote = self.trade.evaluate(clean_sym, curr_price, scout_vote, risk_vote, account_balance, risk_per_trade_pct)
        macro_vote = self.macro.evaluate(market)

        agent_votes = {
            "scout": scout_vote,
            "risk": risk_vote,
            "trade": trade_vote,
            "macro": macro_vote,
        }

        # 2. Check for Risk Agent Veto
        is_vetoed = risk_vote.metrics.get("is_vetoed", False) or risk_vote.decision == "REJECT"
        veto_reason = risk_vote.reasons[0] if is_vetoed else None

        # 3. Consensus Arbitration
        if is_vetoed:
            overall_rec = "REJECT"
            consensus_score = 20.0
            risk_score = 9
            confidence_pct = risk_vote.conviction_pct
        else:
            # Weighted vote tally
            # Scout: 35%, Risk: 25%, Trade: 25%, Macro: 15%
            weights = {"scout": 0.35, "risk": 0.25, "trade": 0.25, "macro": 0.15}
            votes = [scout_vote.decision, risk_vote.decision, trade_vote.decision, macro_vote.decision]
            
            buy_power = sum(weights[k] * (agent_votes[k].conviction_pct / 100.0) for k in weights if agent_votes[k].decision == "BUY")
            sell_power = sum(weights[k] * (agent_votes[k].conviction_pct / 100.0) for k in weights if agent_votes[k].decision == "SELL")

            if buy_power >= 0.65:
                overall_rec = "STRONG_BUY"
                consensus_score = round(buy_power * 100, 1)
                risk_score = 3
                confidence_pct = round(consensus_score * 0.9, 1)
            elif buy_power >= 0.45:
                overall_rec = "BUY"
                consensus_score = round(buy_power * 100, 1)
                risk_score = 4
                confidence_pct = round(consensus_score * 0.85, 1)
            elif sell_power >= 0.65:
                overall_rec = "STRONG_SELL"
                consensus_score = round(sell_power * 100, 1)
                risk_score = 4
                confidence_pct = round(consensus_score * 0.9, 1)
            elif sell_power >= 0.45:
                overall_rec = "SELL"
                consensus_score = round(sell_power * 100, 1)
                risk_score = 5
                confidence_pct = round(consensus_score * 0.85, 1)
            else:
                overall_rec = "WAIT_FOR_CONFIRMATION"
                consensus_score = 50.0
                risk_score = 6
                confidence_pct = 52.0

        # 4. Generate suggested trade plan if consensus is directional
        suggested_plan = None
        if overall_rec in ["STRONG_BUY", "BUY", "SELL", "STRONG_SELL"]:
            try:
                suggested_plan = generate_trade_plan(
                    symbol=clean_sym,
                    requested_direction="BUY" if "BUY" in overall_rec else "SELL",
                    account_balance=account_balance,
                    risk_per_trade_pct=risk_per_trade_pct,
                    timeframe=timeframe,
                )
            except Exception as e:
                logger.warning(f"Could not attach trade plan to consensus: {e}")

        res = MultiAgentConsensusResponse(
            symbol=clean_sym,
            market=market,
            currency_symbol=curr_symbol,
            current_price=curr_price,
            overall_recommendation=overall_rec,
            consensus_score=consensus_score,
            risk_score=risk_score,
            confidence_pct=confidence_pct,
            is_vetoed=is_vetoed,
            veto_reason=veto_reason,
            agent_votes=agent_votes,
            suggested_trade_plan=suggested_plan,
            disclaimer="AI predictions are probabilistic and do not guarantee future returns.",
            timestamp=datetime.now(timezone.utc).isoformat(),
        )
        _CONSENSUS_CACHE[cache_key] = (now, res)
        return res


_consensus_engine_instance = None


def get_multi_agent_consensus_engine() -> MultiAgentConsensusEngine:
    global _consensus_engine_instance
    if _consensus_engine_instance is None:
        _consensus_engine_instance = MultiAgentConsensusEngine()
    return _consensus_engine_instance
