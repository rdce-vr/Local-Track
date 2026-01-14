import requests
import sqlite3
from bs4 import BeautifulSoup

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
    prev = last_price(conn, fuel)
    if prev == price:
        return False

    conn.execute(
        """
        INSERT INTO fuel_prices (fuel_type, price, source)
        VALUES (?, ?, ?)
        """,
        (fuel, price, source),
    )
    conn.commit()
    return True

# -------- SOURCE 1: PATRA NIAGA (PRIMARY) --------

def fetch_patra_niaga():
    url = "https://pertaminapatraniaga.com/page/harga-terbaru-bbm"
    html = requests.get(url, timeout=TIMEOUT).text
    soup = BeautifulSoup(html, "html.parser")

    table = soup.find("table")
    if not table:
        raise RuntimeError("Patra: price table not found")

    prices = {}
    rows = table.find_all("tr")

    for row in rows:
        cols = [c.get_text(strip=True) for c in row.find_all("td")]
        if not cols:
            continue

        # Expect province name somewhere in row
        if not any("Jawa Tengah" in c for c in cols):
            continue

        for fuel in FUEL_TYPES:
            if fuel in row.get_text():
                raw = cols[-1]
                price = int(
                    raw.replace("Rp", "")
                    .replace(".", "")
                    .replace(",", "")
                )
                prices[fuel] = price

    if not prices:
        raise RuntimeError("Patra: Jawa Tengah prices not parsed")

    return prices, "patra-niaga"

# -------- SOURCE 2: MYPERTAMINA (FALLBACK) --------

def fetch_mypertamina():
    url = "https://mypertamina.id/about/product-price"
    html = requests.get(url, timeout=TIMEOUT).text
    soup = BeautifulSoup(html, "html.parser")

    cards = soup.find_all("div")
    prices = {}

    for c in cards:
        text = c.get_text(" ", strip=True)
        for fuel in FUEL_TYPES:
            if fuel in text and "Rp" in text:
                parts = text.split("Rp")
                if len(parts) < 2:
                    continue
                try:
                    price = int(
                        parts[1]
                        .split()[0]
                        .replace(".", "")
                        .replace(",", "")
                    )
                    prices[fuel] = price
                except ValueError:
                    continue

    if not prices:
        raise RuntimeError("MyPertamina: prices not parsed")

    return prices, "mypertamina"

# -------- MAIN ENTRY --------

def run_fetch():
    conn = db()

    try:
        prices, source = fetch_patra_niaga()
    except Exception as e:
        print(f"[WARN] Patra failed: {e}")
        prices, source = fetch_mypertamina()

    for fuel, price in prices.items():
        changed = save_if_changed(conn, fuel, price, source)
        if changed:
            print(f"[UPDATE] {fuel} → Rp{price} ({source})")

    conn.close()

if __name__ == "__main__":
    run_fetch()
