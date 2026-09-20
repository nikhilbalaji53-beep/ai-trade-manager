import time
from datetime import datetime, timezone
from typing import Dict, List, Any, Tuple, Optional

from app.services.instrument_master import get_instrument_by_symbol, get_all_instruments


class DataValidationAndNormalizationPipeline:
    """
    7-Step Data Validation & Normalization Pipeline:
    1. Symbol Validation
    2. Timestamp Validation
    3. Duplicate Check
    4. Missing Data Check
    5. Price Sanity Check (Circuit Breakers)
    6. Normalize Format
    7. Store Raw Feed
    """

    def __init__(self):
        self._recent_order_signatures: Dict[str, float] = {}
        self._raw_feed_buffer: List[Dict[str, Any]] = []

    def step1_symbol_validation(self, symbol: str) -> Tuple[bool, Optional[Dict[str, Any]], str]:
        inst = get_instrument_by_symbol(symbol)
        if not inst:
            return False, None, f"Symbol '{symbol}' not found in Instrument Master Catalog (NSE, BSE, NASDAQ, NYSE)."
        return True, inst, "Symbol valid"

    def step2_timestamp_validation(self, ts_str: Optional[str], max_drift_seconds: float = 5.0) -> Tuple[bool, str]:
        if not ts_str:
            return True, "No timestamp provided; current system time assigned."
        try:
            # Check for freshness
            dt = datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
            drift = abs(datetime.now(timezone.utc).timestamp() - dt.timestamp())
            if drift > max_drift_seconds:
                return False, f"Stale feed detected: timestamp drift is {drift:.2f}s (threshold: {max_drift_seconds}s)."
            return True, "Timestamp fresh"
        except Exception:
            return True, "Timestamp parsing bypassed; current time assigned."

    def step3_duplicate_check(self, symbol: str, side: str, quantity: float, price: float, window_seconds: float = 3.0) -> Tuple[bool, str]:
        sig = f"{symbol.upper()}_{side}_{quantity}_{round(price, 1)}"
        now = time.time()

        if sig in self._recent_order_signatures:
            last_time = self._recent_order_signatures[sig]
            if now - last_time < window_seconds:
                return False, f"Duplicate order signature detected within {window_seconds}s window. Submission blocked."

        self._recent_order_signatures[sig] = now
        if len(self._recent_order_signatures) > 200:
            self._recent_order_signatures = {k: v for k, v in self._recent_order_signatures.items() if now - v < 60}

        return True, "Order signature unique"

    def step4_missing_data_check(self, tick: Dict[str, Any]) -> Tuple[bool, str]:
        required = ["symbol", "price"]
        for req in required:
            if req not in tick or tick[req] is None:
                return False, f"Missing required market field: '{req}'."
        return True, "Required fields intact"

    def step5_price_sanity_check(self, symbol: str, price: float, base_price: Optional[float] = None, circuit_limit_pct: float = 20.0) -> Tuple[bool, str]:
        if price <= 0:
            return False, "Price must be strictly positive."

        if base_price and base_price > 0:
            upper_circuit = round(base_price * (1.0 + circuit_limit_pct / 100.0), 2)
            lower_circuit = round(base_price * (1.0 - circuit_limit_pct / 100.0), 2)

            if price > upper_circuit:
                return False, f"Price ₹{price:.2f} breaches Upper Circuit Limit of ₹{upper_circuit:.2f} (+{circuit_limit_pct}%)."
            if price < lower_circuit:
                return False, f"Price ₹{price:.2f} breaches Lower Circuit Limit of ₹{lower_circuit:.2f} (-{circuit_limit_pct}%)."

        return True, "Price within valid parameters"

    def step6_normalize_format(self, raw_tick: Dict[str, Any], inst: Dict[str, Any]) -> Dict[str, Any]:
        price = float(raw_tick.get("price", raw_tick.get("ltp", raw_tick.get("last_price", 0.0))))
        open_p = float(raw_tick.get("open", price))
        high_p = float(raw_tick.get("high", price))
        low_p = float(raw_tick.get("low", price))
        prev_close = float(raw_tick.get("previous_close", price))
        volume = int(raw_tick.get("volume", 0))

        change = round(price - prev_close, 2)
        change_pct = round((change / prev_close) * 100.0, 2) if prev_close > 0 else 0.0

        return {
            "symbol": inst["symbol"],
            "exchange": inst.get("exchange", "NSE"),
            "instrument_token": inst.get("instrument_token", 0),
            "isin": inst.get("isin", ""),
            "segment": inst.get("segment", "EQ"),
            "company_name": inst.get("company_name", inst["symbol"]),
            "sector": inst.get("sector", "General"),
            "market": inst.get("market", "IN"),
            "currency_symbol": inst.get("currency_symbol", "₹"),
            "ltp": price,
            "open": open_p,
            "high": high_p,
            "low": low_p,
            "previous_close": prev_close,
            "change": change,
            "change_percent": change_pct,
            "volume": volume,
            "turnover_crores": round((price * volume) / 10_000_000.0, 2),
            "timestamp": raw_tick.get("timestamp", datetime.now(timezone.utc).isoformat()),
        }

    def step7_store_raw_feed(self, normalized_tick: Dict[str, Any]):
        self._raw_feed_buffer.append(normalized_tick)
        if len(self._raw_feed_buffer) > 500:
            self._raw_feed_buffer.pop(0)

    def process_incoming_tick(self, raw_tick: Dict[str, Any]) -> Tuple[bool, Optional[Dict[str, Any]], str]:
        # 1. Missing Data Check
        ok4, msg4 = self.step4_missing_data_check(raw_tick)
        if not ok4:
            return False, None, msg4

        # 2. Symbol Validation
        ok1, inst, msg1 = self.step1_symbol_validation(raw_tick["symbol"])
        if not ok1 or not inst:
            return False, None, msg1

        # 3. Timestamp Validation
        ok2, msg2 = self.step2_timestamp_validation(raw_tick.get("timestamp"))
        if not ok2:
            return False, None, msg2

        # 4. Price Sanity Check
        price = float(raw_tick["price"])
        ref_price = float(raw_tick.get("previous_close", price))
        ok5, msg5 = self.step5_price_sanity_check(inst["symbol"], price, ref_price)
        if not ok5:
            return False, None, msg5

        # 5. Normalize
        normalized = self.step6_normalize_format(raw_tick, inst)

        # 6. Store Raw Feed
        self.step7_store_raw_feed(normalized)

        return True, normalized, "Normalized successfully"

    def validate_price_sanity(self, symbol: str, price: float, base_price: float, circuit_limit_pct: float = 10.0) -> Tuple[bool, str]:
        return self.step5_price_sanity_check(symbol, price, base_price, circuit_limit_pct)

    def validate_duplicate_order(self, symbol: str, side: str, quantity: float, price: float, window_seconds: float = 3.0) -> Tuple[bool, str]:
        return self.step3_duplicate_check(symbol, side, quantity, price, window_seconds)


_pipeline = DataValidationAndNormalizationPipeline()


def get_validator() -> DataValidationAndNormalizationPipeline:
    return _pipeline
