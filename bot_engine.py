import os
import time
from datetime import datetime, timezone
from supabase import create_client, Client

SUPABASE_URL = os.getenv("SUPABASE_URL", "YOUR_SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_KEY", "YOUR_SUPABASE_SERVICE_ROLE_KEY")
ACCOUNT_NO = os.getenv("ACCOUNT_NO", "10001234")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

def fetch_account():
    res = (
        supabase.table("bot_accounts")
        .select("*")
        .eq("account_number", ACCOUNT_NO)
        .single()
        .execute()
    )
    return res.data

def push_telemetry(balance, floating_pnl, profit_today, open_positions):
    supabase.table("bot_accounts").update({
        "balance": balance,
        "floating_pnl": floating_pnl,
        "profit_today": profit_today,
        "open_positions": open_positions,
        "last_heartbeat": datetime.now(timezone.utc).isoformat()
    }).eq("account_number", ACCOUNT_NO).execute()

def evaluate_strategy(symbol):
    # Letakkan logik entry sebenar di sini (contoh: breakout / EMA / struktur harga).
    # Kembalikan "BUY", "SELL", atau None.
    return None

def send_order(symbol, side, lot):
    print(f"[ORDER] {side} {lot} lot pada {symbol}")
    # Sambungkan ke API broker / MetaApi di sini.

def main():
    print(f"Bot berjalan untuk akaun {ACCOUNT_NO}...")
    while True:
        try:
            acc = fetch_account()
            if acc:
                started = bool(acc["is_started"])
                hold = bool(acc["is_hold"])
                symbol = acc["symbol"]
                lot = float(acc["lot_size"])
                max_pos = int(acc["max_open_trades"])

                # Nilai contoh sebelum disambung ke data akaun sebenar
                bal = float(acc["balance"])
                flt = float(acc["floating_pnl"])
                pft = float(acc["profit_today"])
                pos = int(acc["open_positions"])

                push_telemetry(bal, flt, pft, pos)

                if not started:
                    print(f"[{datetime.now().strftime('%H:%M:%S')}] START: OFF")
                elif hold:
                    print(f"[{datetime.now().strftime('%H:%M:%S')}] HOLD: ON (Posisi sedia ada sahaja)")
                else:
                    print(f"[{datetime.now().strftime('%H:%M:%S')}] AKTIF | {symbol} | Lot: {lot}")
                    if pos < max_pos:
                        sig = evaluate_strategy(symbol)
                        if sig in ("BUY", "SELL"):
                            send_order(symbol, sig, lot)
        except Exception as err:
            print(f"[ERROR] {err}")

        time.sleep(5)

if __name__ == "__main__":
    main()
