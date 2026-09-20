from typing import Dict, Any


def calculate_indian_charges(
    side: str,
    quantity: float,
    entry_price: float,
    exit_price: float,
    trade_type: str = "INTRADAY",
    exchange: str = "NSE",
) -> Dict[str, Any]:
    """
    Calculates exact statutory charges for Indian Stock Market (NSE / BSE).
    
    1. Brokerage: Flat ₹20 per executed order or 0.03% (whichever is lower for intraday)
    2. STT (Securities Transaction Tax):
       - Intraday: 0.025% on Sell side only
       - Delivery: 0.1% on Buy and Sell side
    3. Exchange Transaction Charges: 0.00297% (NSE) or 0.00375% (BSE)
    4. SEBI Turnover Charges: ₹10 per Crore (0.0001%)
    5. Stamp Duty: 0.003% on Buy side only (for Intraday) / 0.015% (for Delivery)
    6. GST: 18% on (Brokerage + Exchange Charges + SEBI Charges)
    """
    buy_value = quantity * (entry_price if side == "BUY" else exit_price)
    sell_value = quantity * (exit_price if side == "BUY" else entry_price)
    turnover = buy_value + sell_value

    # 1. Brokerage (Entry + Exit orders)
    entry_brokerage = min(20.0, buy_value * 0.0003) if trade_type == "INTRADAY" else 0.0
    exit_brokerage = min(20.0, sell_value * 0.0003) if trade_type == "INTRADAY" else 0.0
    total_brokerage = round(entry_brokerage + exit_brokerage, 2)

    # 2. STT
    if trade_type == "INTRADAY":
        stt = round(sell_value * 0.00025, 2)
    else:
        stt = round((buy_value + sell_value) * 0.001, 2)

    # 3. Exchange Transaction Charges (NSE: 0.00297%)
    exchange_rate = 0.0000297 if exchange.upper() == "NSE" else 0.0000375
    exchange_charges = round(turnover * exchange_rate, 2)

    # 4. SEBI Turnover Charges (₹10 / Crore = 0.0001%)
    sebi_charges = round(turnover * 0.000001, 2)

    # 5. Stamp Duty (0.003% on Buy side for intraday)
    stamp_duty = round(buy_value * 0.00003, 2) if trade_type == "INTRADAY" else round(buy_value * 0.00015, 2)

    # 6. GST (18% on Brokerage + Exchange charges + SEBI charges)
    gst_base = total_brokerage + exchange_charges + sebi_charges
    gst = round(gst_base * 0.18, 2)

    # Total Statutory Taxes & Charges
    total_charges = round(total_brokerage + stt + exchange_charges + sebi_charges + stamp_duty + gst, 2)

    # Gross vs Net Realized P&L
    direction = 1.0 if side == "BUY" else -1.0
    gross_pnl = round((exit_price - entry_price) * quantity * direction, 2)
    net_pnl = round(gross_pnl - total_charges, 2)
    pnl_percent = round((net_pnl / buy_value) * 100.0, 2) if buy_value > 0 else 0.0

    return {
        "gross_pnl": gross_pnl,
        "brokerage": total_brokerage,
        "stt": stt,
        "exchange_charges": exchange_charges,
        "sebi_charges": sebi_charges,
        "stamp_duty": stamp_duty,
        "gst": gst,
        "total_charges": total_charges,
        "net_pnl": net_pnl,
        "pnl_percent": pnl_percent,
        "turnover": round(turnover, 2),
    }
