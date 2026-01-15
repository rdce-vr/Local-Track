import requests
import sqlite3
import re

DB_PATH = "/app/data/prices.db"
TIMEOUT = 20

FUEL_TYPES = [
    "Pertalite",
    "Biosolar",
    "Pertamax",
    "Pertamax Green",
    "Pertamax Turbo",
    "Dexlite",
    "Pertamina Dex",
]

def db():
    return sqlite3.connect(DB_PATH, timeout=30)

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

def save_if_changed(conn, fuel, price, source):
    if last_price(conn, fuel) == price:
        return False

    conn.execute(
        "INSERT INTO fuel_prices (fuel_type, price, source) VALUES (?, ?, ?)",
        (fuel, price, source),
    )
    conn.commit()
    return True

# -------- PRIMARY: PATRA NIAGA (TEXT PARSING) --------

def fetch_patra_niaga():
    url = "https://pertaminapatraniaga.com/page/harga-terbaru-bbm"
    text = requests.get(url, timeout=TIMEOUT).text

    if "Jawa Tengah" not in text:
        raise RuntimeError("Patra: Jawa Tengah section not found")

    section = text.split("Jawa Tengah", 1)[1][:4000]

    prices = {}
    for fuel in FUEL_TYPES:
        match = re.search(
            rf"{fuel}.*?Rp\s?([\d\.]+)",
            section,
            re.IGNORECASE | re.DOTALL,
        )
        if match:
            prices[fuel] = int(match.group(1).replace(".", ""))

    if not prices:
        raise RuntimeError("Patra: prices not extracted")

    return prices, "patra-niaga"

# -------- FALLBACK: MYPERTAMINA (BEST EFFORT) --------

def fetch_mypertamina():
    url = "https://mypertamina.id/about/product-price"
    text = requests.get(url, timeout=TIMEOUT).text

    prices = {}
    for fuel in FUEL_TYPES:
        match = re.search(
            rf"{fuel}.*?Rp\s?([\d\.]+)",
            text,
            re.IGNORECASE | re.DOTALL,
        )
        if match:
            prices[fuel] = int(match.group(1).replace(".", ""))

    if not prices:
        raise RuntimeError("MyPertamina: prices not extracted")

    return prices, "mypertamina"

# -------- ENTRY --------

def run_fetch():
    conn = db()

    try:
        prices, source = fetch_patra_niaga()
    except Exception as e:
        print(f"[WARN] Patra failed: {e}")
        prices, source = fetch_mypertamina()

    print("[DEBUG] Parsed prices:", prices)

    for fuel, price in prices.items():
        if save_if_changed(conn, fuel, price, source):
            print(f"[UPDATE] {fuel} → Rp{price} ({source})")

    conn.close()

if __name__ == "__main__":
    run_fetch()
