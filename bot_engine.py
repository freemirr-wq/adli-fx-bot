import os
import time
from datetime import datetime, timezone
from supabase import create_client, Client

SUPABASE_URL = os.getenv("SUPABASE_URL", "https://hvvpuhyxnuugslflmtou.supabase.co")
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


def get_recent_candles(symbol: str):
    """
    Placeholder data candle untuk ujian awal.
    Nanti kita sambungkan ke API harga sebenar / MetaApi.
    """
    sample_closes = [
        2650.0, 2652.5, 2654.0, 2653.2, 2655.8, 2657.1, 2656.4, 2658.9,
        2660.2, 2659.5, 2661.8, 2663.0, 2662.1, 2664.5, 2666.0, 2665.2,
        2667.8, 2669.4, 2668.7, 2671.0, 2673.2, 2672.5, 2675.0, 2677.4,
        2679.8
    ]
    return [{"close": c} for c in sample_closes]


def calc_ema(values: list[float], period: int) -> float:
    k = 2 / (period + 1)
    ema_val = values[0]
    for price in values[1:]:
        ema_val = price * k + ema_val * (1 - k)
    return ema_val


def evaluate_strategy(candles: list[dict]):
    """
    Strategi EMA 9 & EMA 21 crossover.
    Kembalikan ("BUY", sl_points, tp_points), ("SELL", sl_points, tp_points), atau (None, None, None).
    """
    if len(candles) < 25:
        return None, None, None

    closes = [float(c["close"]) for c in candles]
    fast_prev = calc_ema(closes[:-1], 9)
    slow_prev = calc_ema(closes[:-1], 21)
    fast_curr = calc_ema(closes, 9)
    slow_curr = calc_ema(closes, 21)

    sl_points = 150.0
    tp_points = 225.0  # Nisbah R:R 1:1.5

    if fast_prev <= slow_prev and fast_curr > slow_curr:
        return "BUY", sl_points, tp_points

    if fast_prev >= slow_prev and fast_curr < slow_curr:
        return "SELL", sl_points, tp_points

    return None, None, None


def send_order(symbol: str, side: str, lot: float, sl_points: float, tp_points: float):
    print(f"[SIGNAL -> ORDER] {side} {lot} lot | {symbol} | SL: {sl_points} pts | TP: {tp_points} pts")
    # Di sini nanti kita masukkan panggilan sebenar ke MetaApi / broker API


def main():
    print(f"Bot Engine bermula untuk akaun {ACCOUNT_NO}...")
    while True:
        try:
            acc = fetch_account()
            if acc:
                started = bool(acc["is_started"])
                hold = bool(acc["is_hold"])
                symbol = acc["symbol"]
                lot = float(acc["lot_size"])
                max_pos = int(acc["max_open_trades"])

                bal = float(acc["balance"])
                flt = float(acc["floating_pnl"])
                pft = float(acc["profit_today"])
                pos = int(acc["open_positions"])

                push_telemetry(bal, flt, pft, pos)

                if not started:
                    print(f"[{datetime.now().strftime('%H:%M:%S')}] START: OFF")
                elif hold:
                    print(f"[{datetime.now().strftime('%H:%M:%S')}] HOLD: ON (Tiada entry baru)")
                else:
                    print(f"[{datetime.now().strftime('%H:%M:%S')}] AKTIF | {symbol} | Lot: {lot} | Pos: {pos}/{max_pos}")
                    if pos < max_pos:
                        candles = get_recent_candles(symbol)
                        side, sl_pts, tp_pts = evaluate_strategy(candles)
                        if side in ("BUY", "SELL"):
                            send_order(symbol, side, lot, sl_pts, tp_pts)
                    else:
                        print("Posisi terbuka sudah mencapai had maksimum.")
        except Exception as err:
            print(f"[ERROR] {err}")

        time.sleep(5)


if __name__ == "__main__":
    main()
