import sqlite3
import requests
import re

API_URL = "https://api.web.mypertamina.id/price"
PLUANG_API = "https://api-pluang.pluang.com/api/v3/asset/gold/pricing"
TARGET_PROVINCE = "Prov. Jawa Tengah"
DB_PATH = "/app/data/prices.db"

def db():
    return sqlite3.connect(DB_PATH, timeout=30)

def normalize_price(raw):
    """
    'Rp. 13.500' / 'Rp 10.000' -> 13500
    '-' -> None
    """
    if not raw or raw.strip() == "-":
        return None
    digits = re.sub(r"[^\d]", "", raw)
    return int(digits) if digits else None

def last_price(conn, fuel):
    cur = conn.cursor()
    cur.execute(
        """
        SELECT price
        FROM fuel_prices
        WHERE fuel_type = ?
        ORDER BY fetched_at DESC
        LIMIT 1
        """,
        (fuel,),
    )
    row = cur.fetchone()
    return row[0] if row else None

def save_if_changed(conn, fuel, price):
    if last_price(conn, fuel) == price:
        return False
    conn.execute(
        """
        INSERT INTO fuel_prices (fuel_type, price, source)
        VALUES (?, ?, ?)
        """,
        (fuel, price, "mypertamina-api"),
    )
    conn.commit()
    return True

def run_fetch():
    r = requests.get(API_URL, timeout=30)
    r.raise_for_status()
    payload = r.json()

    provinces = payload.get("data", {}).get("data", [])
    if not provinces:
        raise RuntimeError("No province data returned")

    jawa_tengah = next(
        (p for p in provinces if p.get("province") == TARGET_PROVINCE),
        None,
    )
    if not jawa_tengah:
        raise RuntimeError(f"{TARGET_PROVINCE} not found")

    prices = {}
    for item in jawa_tengah.get("list_price", []):
        fuel = item.get("product")
        price = normalize_price(item.get("price"))
        if price is not None:
            prices[fuel] = price

    if not prices:
        raise RuntimeError("No valid prices for Jawa Tengah")

    print("[DEBUG] Jawa Tengah prices:", prices)

    conn = db()
    for fuel, price in prices.items():
        if save_if_changed(conn, fuel, price):
            print(f"[UPDATE] {fuel} → Rp{price}")
    conn.close()

#Gold Fetcher
def fetch_gold_price():
    r = requests.get(PLUANG_API, timeout=15)
    r.raise_for_status()
    data = r.json()["data"]["current"]

    return {
        "mid": data["midPrice"],
        "buy": data["buy"],
        "sell": data["sell"],
        "updated_at": data["updated_at"],
    }

def save_gold_price(gold):
    conn = sqlite3.connect(DB_PATH, timeout=30)
    cur = conn.cursor()
    cur.execute("""
        INSERT OR IGNORE INTO gold_prices (mid_price, buy_price, sell_price)
        VALUES (?, ?, ?)
    """, (gold["mid"], gold["buy"], gold["sell"]))
    conn.commit()
    conn.close()

def run_gold_fetch():
    print("[DEBUG] Starting gold fetch...")

    try:
        gold = fetch_gold_price()
        print("[DEBUG] Gold API data:", gold)

        conn = sqlite3.connect(DB_PATH, timeout=30)
        cur = conn.cursor()
        cur.execute("""
            INSERT OR IGNORE INTO gold_prices (mid_price, buy_price, sell_price)
            VALUES (?, ?, ?)
        """, (gold["mid"], gold["buy"], gold["sell"]))
        conn.commit()

        if cur.rowcount == 0:
            print("[INFO] Gold price unchanged, not inserted.")
        else:
            print(f"[INFO] Gold price inserted: mid={gold['mid']}, buy={gold['buy']}, sell={gold['sell']}")

        conn.close()

    except Exception as e:
        print("[ERROR] Gold fetch failed:", e)
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    run_fetch()
