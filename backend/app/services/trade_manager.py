import uuid
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional

from app.database import PortfolioStore
from app.models.db_models import PositionModel, OrderModel, TradeRecordModel
from app.services.market_data import get_price, get_current_live_price
from app.services.pnl_engine import position_pnl, position_summary
from app.services.trailing_stop import (
    calculate_trailing_stop,
    evaluate_profit_protection_step,
    evaluate_ai_trade_manager,
    evaluate_profit_manager,
    evaluate_loss_manager,
)
from app.services.risk_engine import validate_order
from app.services.indian_brokerage import calculate_indian_charges
from app.services.broker_connector import get_broker_connector


class TradeManager:
    def __init__(self, store: PortfolioStore) -> None:
        self.store = store

    def open_trade(
        self,
        symbol: str,
        side: str,
        quantity: float,
        order_type: str = "MARKET",
        price: Optional[float] = None,
        stop_loss: Optional[float] = None,
        take_profit: Optional[float] = None,
        trailing_stop_pct: Optional[float] = None,
        max_loss: Optional[float] = None,
        broker: str = "ZERODHA_KITE",
        strategy: str = "User Trade Config",
    ) -> Dict[str, Any]:
        symbol = symbol.upper().replace(".NS", "").replace(".BO", "")
        current_market_price = get_current_live_price(symbol)

        # CRITICAL: MARKET orders require a live market price.
        # If the feed is down (get_current_live_price returns None) and no explicit
        # price is given, reject the order rather than use a fake/stale price.
        if order_type == "LIMIT" and price and price > 0:
            exec_price = price
        elif current_market_price and current_market_price > 0:
            exec_price = current_market_price
        else:
            raise ValueError(
                f"MARKET order for {symbol} rejected: live market price is unavailable "
                f"(feed disconnected or symbol not found). Connect a live market data "
                f"provider before placing MARKET orders."
            )

        # Calculate notional in INR
        notional = round(exec_price * quantity, 2)

        # Snapshot for pre-trade risk validation
        cash, positions_map, _, _ = self.store.snapshot()
        pos_summaries = [position_summary(p) for p in positions_map.values()]
        equity = round(cash + sum(p["market_value"] for p in pos_summaries if p["side"] == "BUY") - sum(p["market_value"] for p in pos_summaries if p["side"] == "SELL"), 2)

        # Calculate Default Stop & Target if not specified
        stop = stop_loss or calculate_trailing_stop(side, exec_price, self.store.risk_settings.default_stop_loss_pct)
        target = take_profit or round(exec_price * (1.10 if side == "BUY" else 0.90), 2)
        target_2 = round(exec_price * (1.18 if side == "BUY" else 0.82), 2)

        # 1. Pre-Trade Risk Check
        passed, msg = validate_order(
            cash=cash,
            equity=equity,
            positions=pos_summaries,
            symbol=symbol,
            side=side,
            notional=notional,
            stop_loss=stop,
            risk_settings=self.store.risk_settings,
        )
        if not passed:
            self.store.log_audit("ORDER_REJECTED", "WARNING", f"Risk Engine REJECTED {symbol} order: {msg}", {"symbol": symbol, "notional": notional})
            raise ValueError(msg)

        # 2. Max Loss Guardrail Check
        if max_loss and max_loss > 0 and stop:
            potential_loss = abs(exec_price - stop) * quantity
            if potential_loss > max_loss:
                reason = f"Potential loss of ₹{potential_loss:,.2f} exceeds configured Max Loss limit of ₹{max_loss:,.2f}."
                self.store.log_audit("ORDER_REJECTED", "WARNING", f"Max Loss Breached: {reason}", {"symbol": symbol})
                raise ValueError(reason)

        # 4. Route via Indian Broker API
        broker_conn = get_broker_connector(broker)
        broker_res = broker_conn.place_order(
            symbol=symbol,
            side=side,
            quantity=quantity,
            order_type=order_type,
            price=exec_price,
            trigger_price=stop,
            exchange="NSE",
        )

        with self.store._lock:
            if symbol in self.store.positions:
                existing = self.store.positions[symbol]
                if existing.side == side:
                    total_qty = existing.quantity + quantity
                    avg_entry = round(((existing.entry_price * existing.quantity) + (exec_price * quantity)) / total_qty, 2)
                    existing.quantity = total_qty
                    existing.entry_price = avg_entry
                    existing.stop_loss = stop
                    existing.take_profit = target
                    existing.updated_at = datetime.now(timezone.utc).isoformat()
                    position = existing
                else:
                    raise ValueError(f"Opposing position already open in {symbol}. Close existing {existing.side} position first.")
            else:
                position = PositionModel(
                    symbol=symbol,
                    side=side,
                    quantity=quantity,
                    entry_price=exec_price,
                    current_price=exec_price,
                    market_value=notional,
                    unrealized_pnl=0.0,
                    pnl_percent=0.0,
                    stop_loss=stop,
                    trailing_stop=stop,
                    take_profit=target,
                    take_profit_2=target_2,
                    risk_level="Low",
                    highest_price=exec_price,
                    lowest_price=exec_price,
                    break_even_activated=False,
                )
                self.store.positions[symbol] = position

            if side == "BUY":
                self.store.cash -= notional
            else:
                self.store.cash += notional

            # Record Order
            order = OrderModel(
                id=broker_res["order_id"],
                symbol=symbol,
                side=side,
                order_type=order_type,
                quantity=quantity,
                price=exec_price,
                stop_loss=stop,
                take_profit=target,
                trailing_stop_pct=trailing_stop_pct or self.store.risk_settings.trailing_stop_distance_pct,
                status="FILLED",
                filled_price=exec_price,
                commission=20.0,
                notes=f"Broker: {broker} | Strategy: {strategy}",
            )
            self.store.orders.insert(0, order)

        # Audit & In-App Alert
        self.store.log_audit(
            "ORDER_EXECUTED",
            "SUCCESS",
            f"Filled {side} {quantity} {symbol} @ ₹{exec_price:,.2f} on NSE via {broker}",
            {"order_id": order.id, "symbol": symbol, "notional": notional, "stop_loss": stop, "take_profit": target},
        )
        self.store.add_alert(
            "Order Executed",
            f"Filled {side} {quantity} shares of {symbol} at ₹{exec_price:,.2f} with Stop-Loss ₹{stop:,.2f} and Target ₹{target:,.2f}.",
            symbol=symbol,
            severity="green",
        )

        return position_summary(position)

    def close_trade(self, symbol: str, quantity: Optional[float] = None, reason: str = "MANUAL") -> Dict[str, Any]:
        symbol = symbol.upper().replace(".NS", "").replace(".BO", "")
        with self.store._lock:
            position = self.store.positions.get(symbol)
            if position is None:
                raise ValueError(f"No open position exists for {symbol}")

            close_quantity = quantity or position.quantity
            if close_quantity > position.quantity:
                raise ValueError("Close quantity exceeds open position size.")

            exit_price = get_current_live_price(symbol)

            # CRITICAL: Closing a position requires a real exit price.
            # If the feed is down, reject rather than close at a fake price.
            if exit_price is None or exit_price <= 0:
                raise ValueError(
                    f"Cannot close {symbol}: live market price unavailable "
                    f"(feed disconnected). Reconnect the market data provider "
                    f"before closing positions."
                )

            # Exact Indian statutory taxes calculation
            charges = calculate_indian_charges(
                side=position.side,
                quantity=close_quantity,
                entry_price=position.entry_price,
                exit_price=exit_price,
                trade_type="INTRADAY",
                exchange="NSE",
            )
            realized_gross = charges["gross_pnl"]
            realized_net = charges["net_pnl"]
            pnl_pct = charges["pnl_percent"]
            notional = round(exit_price * close_quantity, 2)

            if position.side == "BUY":
                self.store.cash += (notional - charges["total_charges"])
            else:
                self.store.cash -= (notional + charges["total_charges"])

            trade_id = f"TRD-{uuid.uuid4().hex[:6].upper()}"
            trade = TradeRecordModel(
                id=trade_id,
                symbol=symbol,
                side=position.side,
                quantity=close_quantity,
                entry_price=position.entry_price,
                exit_price=exit_price,
                realized_pnl=realized_net,
                pnl_percent=pnl_pct,
                duration="Intraday",
                strategy="AI Execution",
                exit_reason=reason,
                status="CLOSED",
                opened_at=position.opened_at,
                closed_at=datetime.now(timezone.utc).isoformat(),
            )
            self.store.trades.insert(0, trade)

            if close_quantity >= position.quantity:
                del self.store.positions[symbol]
            else:
                position.quantity -= close_quantity
                position.market_value = round(position.quantity * exit_price, 2)

        self.store.log_audit(
            "POSITION_CLOSED",
            "INFO" if realized_net >= 0 else "WARNING",
            f"Closed {close_quantity} {symbol} @ ₹{exit_price:,.2f} [Gross: ₹{realized_gross:+,.2f} | Taxes: ₹{charges['total_charges']:,.2f} | Net: ₹{realized_net:+,.2f}] ({reason})",
            {"trade_id": trade_id, "net_pnl": realized_net, "charges": charges, "reason": reason},
        )
        self.store.add_alert(
            "Position Closed",
            f"{symbol} closed @ ₹{exit_price:,.2f}. Net Realized P&L: ₹{realized_net:+,.2f} ({pnl_pct:+,.2f}%). Exit Reason: {reason}.",
            symbol=symbol,
            severity="green" if realized_net >= 0 else "coral",
        )

        return {
            "symbol": symbol,
            "quantity": close_quantity,
            "exit_price": exit_price,
            "gross_pnl": realized_gross,
            "charges": charges,
            "realized_pnl": realized_net,
            "pnl_percent": pnl_pct,
            "status": "CLOSED",
            "reason": reason,
        }

    def close_all_positions(self, reason: str = "PANIC_CLOSE") -> List[Dict[str, Any]]:
        symbols = list(self.store.positions.keys())
        results = []
        for symbol in symbols:
            try:
                res = self.close_trade(symbol, reason=reason)
                results.append(res)
            except Exception as e:
                results.append({"symbol": symbol, "error": str(e)})
        
        self.store.log_audit(
            "PANIC_SQUARE_OFF",
            "ERROR",
            f"Emergency Killswitch: Square off all {len(results)} open positions executed.",
            {"closed_symbols": symbols},
        )
        return results

    def update_position_levels(self, symbol: str, stop_loss: Optional[float], take_profit: Optional[float], trailing_stop: Optional[float]) -> Dict[str, Any]:
        symbol = symbol.upper().replace(".NS", "").replace(".BO", "")
        with self.store._lock:
            pos = self.store.positions.get(symbol)
            if not pos:
                raise ValueError(f"Position for {symbol} not found")
            if stop_loss:
                pos.stop_loss = stop_loss
            if take_profit:
                pos.take_profit = take_profit
            if trailing_stop:
                pos.trailing_stop = trailing_stop
            pos.updated_at = datetime.now(timezone.utc).isoformat()
            return position_summary(pos)

    def evaluate_live_positions(self):
        """
        AI Trade Manager Continuous Monitoring Engine:
        Price -> Trend -> Momentum -> Volume -> Volatility -> P&L -> Risk -> Decision (HOLD / TRAIL / PARTIAL EXIT / EXIT)
        """
        closed_trades_to_process = []
        with self.store._lock:
            for symbol, pos in list(self.store.positions.items()):
                curr_p = get_current_live_price(symbol)

                # CRITICAL: If live price is unavailable, DO NOT update the position.
                # The position stays frozen at its last-known price.
                # DO NOT use stale prices to trigger stop-loss or take-profit decisions.
                if curr_p is None or curr_p <= 0:
                    import logging
                    logging.getLogger(__name__).warning(
                        f"evaluate_live_positions: no live price for '{symbol}'. "
                        f"Skipping position update. P&L frozen at last known values."
                    )
                    pos.data_status = "DATA_STALE"
                    continue

                pos.current_price = curr_p
                pos.data_status = "LIVE"
                pos.market_value = round(pos.quantity * curr_p, 2)
                pos.unrealized_pnl = position_pnl(pos.side, pos.quantity, pos.entry_price, curr_p)
                pos.pnl_percent = round(
                    ((curr_p - pos.entry_price) / pos.entry_price) * 100.0
                    if pos.side == "BUY"
                    else ((pos.entry_price - curr_p) / pos.entry_price) * 100.0,
                    2,
                )

                # Continuous AI Trade Manager & Dual Branch Evaluation
                eval_res = evaluate_ai_trade_manager(
                    side=pos.side,
                    entry_price=pos.entry_price,
                    current_price=curr_p,
                    stop_loss=pos.stop_loss,
                    trailing_stop=pos.trailing_stop or pos.stop_loss,
                    take_profit=pos.take_profit,
                    highest_price=pos.highest_price,
                    lowest_price=pos.lowest_price,
                    quantity=pos.quantity,
                )

                decision = eval_res["decision"]
                new_stop = eval_res["new_stop"]
                pos.highest_price = eval_res["new_high"]
                pos.lowest_price = eval_res["new_low"]

                if eval_res["branch"] == "PROFIT_MANAGER" and new_stop > (pos.trailing_stop or pos.stop_loss):
                    pos.trailing_stop = new_stop
                    self.store.log_audit(
                        "TRAILING_STOP_RATCHET", "SUCCESS",
                        f"{symbol} Trailing Stop ratcheted to ₹{new_stop:,.2f} as price reached ₹{curr_p:,.2f}",
                        {"symbol": symbol, "trailing_stop": new_stop},
                    )

                # Risk level
                stop_dist = abs(curr_p - (pos.trailing_stop or pos.stop_loss)) / curr_p if curr_p > 0 else 0.05
                pos.risk_level = "High" if stop_dist < 0.015 else "Moderate" if stop_dist < 0.035 else "Low"

                if decision in ["TARGET_EXIT", "EXIT"]:
                    closed_trades_to_process.append((symbol, "TAKE_PROFIT" if decision == "TARGET_EXIT" else "STOP_LOSS_HIT"))

        for sym, reason in closed_trades_to_process:
            try:
                self.close_trade(sym, reason=reason)
            except Exception:
                pass

    def portfolio(self) -> Dict[str, Any]:
        self.evaluate_live_positions()
        cash, positions, trades, orders = self.store.snapshot()
        summaries = [position_summary(p) for p in positions.values()]

        realized_pnl = round(sum(t.realized_pnl for t in trades), 2)
        unrealized_pnl = round(sum(item["unrealized_pnl"] for item in summaries), 2)
        total_pnl = round(realized_pnl + unrealized_pnl, 2)

        long_value = sum(item["market_value"] for item in summaries if item["side"] == "BUY")
        short_value = sum(item["market_value"] for item in summaries if item["side"] == "SELL")
        equity = round(cash + long_value - short_value, 2)

        wins = sum(1 for t in trades if t.realized_pnl > 0)
        win_rate = round((wins / len(trades)) * 100.0, 1) if trades else 0.0

        gross_win = sum(t.realized_pnl for t in trades if t.realized_pnl > 0)
        gross_loss = abs(sum(t.realized_pnl for t in trades if t.realized_pnl <= 0))
        profit_factor = round(gross_win / max(1.0, gross_loss), 2)

        margin_used = round(long_value + short_value, 2)
        margin_available = round(max(0.0, cash), 2)

        return {
            "equity": equity,
            "cash": round(cash, 2),
            "starting_capital": self.store.starting_capital,
            "total_pnl": total_pnl,
            "daily_pnl": total_pnl,
            "realized_pnl": realized_pnl,
            "unrealized_pnl": unrealized_pnl,
            "win_rate": win_rate,
            "profit_factor": profit_factor,
            "total_trades_count": len(trades),
            "open_positions_count": len(summaries),
            "margin_used": margin_used,
            "margin_available": margin_available,
            "positions": summaries,
        }
