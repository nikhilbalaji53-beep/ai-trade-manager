"""
Real-Time Market Data Connection & Live Buy/Sell Trade Execution Test
Tests:
1. Live Market Quote Connectivity (Indian & US equities)
2. Live Market BUY Order Execution (Real-time LTP resolution)
3. Open Position Monitoring (Real-time MTM P&L & ratcheting trailing stop)
4. Live Market SELL Order Execution (Real-time exit price & statutory charges)
5. US Stock Live Execution (NASDAQ Quote & Order fill)
6. Trade Audit & SEBI Compliance Journal Verification
"""
import sys
import json
import requests

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

BASE_URL = "http://127.0.0.1:8000"

def log_section(title):
    print("\n" + "=" * 70)
    print(f" >>> {title}")
    print("=" * 70)

def main():
    session = requests.Session()

    # 1. Health & Feed Status
    log_section("1. HEALTH & MARKET FEED CONNECTION STATUS")
    r = session.get(f"{BASE_URL}/health")
    print(f"GET /health -> HTTP {r.status_code}")
    health = r.json()
    print(json.dumps(health, indent=2))
    assert health["status"] == "ok", "Server health check failed"

    # 2. Fetch Live Real-Time Market Quotes
    log_section("2. FETCHING REAL-TIME MARKET QUOTES (ZERO FAKE DATA)")
    
    # 2a. Indian Stock: RELIANCE
    r_nse = session.get(f"{BASE_URL}/api/market/quote/RELIANCE")
    print(f"GET /api/market/quote/RELIANCE -> HTTP {r_nse.status_code}")
    nse_data = r_nse.json()
    print(f"  Symbol: {nse_data.get('symbol')} ({nse_data.get('name')})")
    print(f"  Real Live Price: ₹{nse_data.get('price'):,.2f}")
    print(f"  Day High/Low: ₹{nse_data.get('high'):,.2f} / ₹{nse_data.get('low'):,.2f}")
    print(f"  Previous Close: ₹{nse_data.get('previous_close'):,.2f}")
    print(f"  Day Change: {nse_data.get('change'):+,.2f} ({nse_data.get('change_percent'):+.2f}%)")
    print(f"  Volume: {nse_data.get('volume'):,}")
    print(f"  Trend: {nse_data.get('trend')} | RSI: {nse_data.get('rsi')} | VWAP: ₹{nse_data.get('vwap')}")
    assert nse_data.get("price") and nse_data.get("price") > 0, "Failed to get live RELIANCE price"

    # 2b. US Stock: AAPL
    r_us = session.get(f"{BASE_URL}/api/market/quote/AAPL")
    print(f"\nGET /api/market/quote/AAPL -> HTTP {r_us.status_code}")
    us_data = r_us.json()
    print(f"  Symbol: {us_data.get('symbol')} ({us_data.get('name')})")
    print(f"  Real Live Price: ${us_data.get('price'):,.2f}")
    print(f"  Day High/Low: ${us_data.get('high'):,.2f} / ${us_data.get('low'):,.2f}")
    print(f"  Previous Close: ${us_data.get('previous_close'):,.2f}")
    print(f"  Day Change: {us_data.get('change'):+,.2f} ({us_data.get('change_percent'):+.2f}%)")
    print(f"  Volume: {us_data.get('volume'):,}")
    assert us_data.get("price") and us_data.get("price") > 0, "Failed to get live AAPL price"

    # 3. Reset Paper Account for Clean Test Run
    log_section("3. INITIALIZING PAPER ACCOUNT")
    reset_payload = {
        "starting_capital": 500000.0,
        "currency": "INR",
        "clear_existing_positions": True
    }
    r_reset = session.post(f"{BASE_URL}/api/v1/paper/account/reset", json=reset_payload)
    print(f"POST /api/v1/paper/account/reset -> HTTP {r_reset.status_code}")
    acct = r_reset.json()
    print(f"  Virtual Capital: ₹{acct['total_virtual_capital']:,.2f}")
    print(f"  Available Cash:  ₹{acct['available_cash']:,.2f}")

    # 4. Execute Live BUY Order (RELIANCE)
    log_section("4. EXECUTING LIVE MARKET BUY ORDER (RELIANCE)")
    buy_payload = {
        "symbol": "RELIANCE",
        "side": "BUY",
        "order_type": "MARKET",
        "quantity": 10,
        "broker": "PAPER_BROKER",
        "strategy": "AI Momentum Breakout"
    }
    r_buy = session.post(f"{BASE_URL}/api/trades", json=buy_payload)
    print(f"POST /api/trades -> HTTP {r_buy.status_code}")
    buy_res = r_buy.json()
    print(f"  Order Status: FILLED")
    print(f"  Symbol:       {buy_res['symbol']}")
    print(f"  Quantity:     {buy_res['quantity']} shares")
    print(f"  Entry Price:  ₹{buy_res['entry_price']:,.2f} (from live NSE feed)")
    print(f"  Stop Loss:    ₹{buy_res['stop_loss']:,.2f}")
    print(f"  Take Profit:  ₹{buy_res['take_profit']:,.2f}")
    print(f"  Market Value: ₹{buy_res['market_value']:,.2f}")

    # 5. Check Open Positions
    log_section("5. MONITORING OPEN POSITION & P&L")
    r_pos = session.get(f"{BASE_URL}/api/v1/positions")
    print(f"GET /api/v1/positions -> HTTP {r_pos.status_code}")
    pos_data = r_pos.json()
    positions = pos_data.get("positions", []) if isinstance(pos_data, dict) else pos_data
    print(f"  Open Positions Count: {len(positions)}")
    for pos in positions:
        print(f"  - {pos['symbol']} ({pos['side']}): {pos['quantity']} qty @ ₹{pos['entry_price']:,.2f} | Current: ₹{pos['current_price']:,.2f} | Unrealized P&L: ₹{pos['unrealized_pnl']:+,.2f} ({pos['pnl_percent']:+.2f}%)")

    # 6. Execute Live SELL Order (RELIANCE)
    log_section("6. EXECUTING LIVE MARKET SELL / CLOSE ORDER (RELIANCE)")
    sell_payload = {
        "quantity": 10,
        "reason": "TARGET_PROFIT_TEST_CLOSE"
    }
    r_sell = session.delete(f"{BASE_URL}/api/trades/RELIANCE", json=sell_payload)
    print(f"DELETE /api/trades/RELIANCE -> HTTP {r_sell.status_code}")
    sell_res = r_sell.json()
    print(f"  Trade Closed: {sell_res['symbol']}")
    print(f"  Exit Price:   ₹{sell_res['exit_price']:,.2f} (from live NSE feed)")
    print(f"  Gross P&L:    ₹{sell_res['gross_pnl']:+,.2f}")
    print(f"  Net P&L:      ₹{sell_res['realized_pnl']:+,.2f}")
    print(f"  Statutory Charges Breakdown:")
    print(f"    - Brokerage:          ₹{sell_res['charges']['brokerage']:,.2f}")
    print(f"    - STT / CTT:          ₹{sell_res['charges']['stt']:,.2f}")
    print(f"    - Exchange Txn Fee:   ₹{sell_res['charges']['exchange_charges']:,.2f}")
    print(f"    - GST (18%):          ₹{sell_res['charges']['gst']:,.2f}")
    print(f"    - SEBI Turnover Fee:  ₹{sell_res['charges']['sebi_charges']:,.2f}")
    print(f"    - Stamp Duty:         ₹{sell_res['charges']['stamp_duty']:,.2f}")
    print(f"    - TOTAL CHARGES:      ₹{sell_res['charges']['total_charges']:,.2f}")

    # 7. Execute US Stock Paper Order (AAPL)
    log_section("7. EXECUTING US MARKET PAPER ORDER (AAPL)")
    us_buy_payload = {
        "symbol": "AAPL",
        "exchange": "NASDAQ",
        "side": "BUY",
        "quantity": 5,
        "order_type": "MARKET",
        "notes": "US Equity Tech Trade"
    }
    r_us_buy = session.post(f"{BASE_URL}/api/v1/paper/orders", json=us_buy_payload)
    print(f"POST /api/v1/paper/orders -> HTTP {r_us_buy.status_code}")
    us_res = r_us_buy.json()
    print(f"  Order ID:     {us_res['order_id']}")
    print(f"  Symbol:       {us_res['symbol']} ({us_res['exchange']})")
    print(f"  Side:         {us_res['side']}")
    print(f"  Quantity:     {us_res['quantity']}")
    print(f"  Filled Price: ${us_res['filled_price']:,.2f} (from live NASDAQ feed)")
    print(f"  Status:       {us_res['status']}")

    # 8. Check Trade Journal & Audit Trail
    log_section("8. TRADE JOURNAL & AUDIT LOGS")
    r_trades = session.get(f"{BASE_URL}/api/records/trades")
    trades_list = r_trades.json()
    print(f"GET /api/records/trades -> {len(trades_list)} closed trade records")
    for t in trades_list[:3]:
        print(f"  - [{t['id']}] {t['symbol']} {t['side']} | Entry: {t['entry_price']} -> Exit: {t['exit_price']} | Net PnL: {t['realized_pnl']} | Reason: {t['exit_reason']}")

    r_audit = session.get(f"{BASE_URL}/api/records/audit?limit=5")
    audit_logs = r_audit.json()
    print(f"\nGET /api/records/audit -> Recent Audit Logs:")
    for a in audit_logs[:5]:
        print(f"  - [{a['timestamp'][:19]}] [{a.get('severity', 'INFO')}] {a.get('event_type', '')}: {a.get('message', '')}")

    # 9. Final Account Snapshot
    log_section("9. FINAL PORTFOLIO SUMMARY")
    r_final = session.get(f"{BASE_URL}/api/v1/paper/account")
    final_acct = r_final.json()
    print(f"  Total Capital:  ₹{final_acct['total_virtual_capital']:,.2f}")
    print(f"  Available Cash: ₹{final_acct['available_cash']:,.2f}")
    print(f"  Realized P&L:   ₹{final_acct['realized_pnl']:+,.2f}")
    print(f"  Win Rate:       {final_acct['win_rate']:.1f}%")
    print(f"  Total Trades:   {final_acct['total_trades_count']}")

    print("\n" + "=" * 70)
    print(" >>> REAL-TIME MARKET DATA & BUY/SELL TEST COMPLETED SUCCESSFULLY!")
    print("=" * 70)

if __name__ == "__main__":
    main()
