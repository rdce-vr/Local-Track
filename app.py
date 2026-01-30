import sqlite3
from datetime import datetime
from flask import Flask, render_template

DB_PATH = "/app/data/prices.db"

app = Flask(__name__)

def get_db():
    return sqlite3.connect(DB_PATH, timeout=30)

def init_db():
    conn = get_db()
    
    #Fuel table
    conn.execute("""
        CREATE TABLE IF NOT EXISTS fuel_prices (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            fuel_type TEXT NOT NULL,
            price INTEGER NOT NULL,
            source TEXT NOT NULL,
            fetched_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.execute("""
        CREATE UNIQUE INDEX IF NOT EXISTS uniq_price_change
        ON fuel_prices (fuel_type, price)
    """)

    #Gold table
    conn.execute("""
        CREATE TABLE IF NOT EXISTS gold_prices (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            mid_price INTEGER NOT NULL,
            buy_price INTEGER NOT NULL,
            sell_price INTEGER NOT NULL,
            fetched_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.execute("""
        CREATE UNIQUE INDEX IF NOT EXISTS uniq_gold_price_change
        ON gold_prices (mid_price, buy_price, sell_price)
    """)
    conn.commit()
    conn.close()

FUEL_GROUPS = {
    "Gasoline": [
        "PERTALITE",
        "PERTAMAX PERTASHOP",
        "PERTAMAX",
        "PERTAMAX GREEN 95",
        "PERTAMAX TURBO",
    ],
    "Diesel": [
        "PERTAMINA BIOSOLAR SUBSIDI",
        "DEXLITE",
        "PERTAMINA DEX",
    ],
}

@app.route("/")
def index():
    conn = get_db()
    cur = conn.cursor()

    #Get latest row per fuel type
    cur.execute("""
        SELECT fuel_type, price, fetched_at
        FROM fuel_prices
        WHERE id IN (
            SELECT MAX(id)
            FROM fuel_prices
            GROUP BY fuel_type
        )
        ORDER BY fuel_type
    """)
    latest_rows = cur.fetchall()

    #Get previous price per fuel type
    cur.execute("""
        SELECT fuel_type, price
        FROM fuel_prices
        WHERE id IN (
            SELECT MAX(id) 
            FROM fuel_prices
            WHERE id NOT IN (
                SELECT MAX(id)
                FROM fuel_prices
                GROUP BY fuel_type
            )
            GROUP BY fuel_type
        )
    """)
    previous_rows = cur.fetchall()

    #Get last update time
    cur.execute("SELECT MAX(fetched_at) FROM fuel_prices")
    last_update_raw = cur.fetchone()[0]

    conn.close()

    previous_map = {fuel.upper(): price for fuel, price in previous_rows}

    #Map fuels for grouping
    fuel_map = {}
    for fuel, price, fetched_at in latest_rows:
        prev_price = previous_map.get(fuel.upper())
        delta = None
        if prev_price is not None:
            delta = price - prev_price
        fuel_map[fuel.upper()] = (fuel, price, fetched_at, prev_price, delta)

    grouped = {}
    for group, fuels in FUEL_GROUPS.items():
        grouped[group] = [fuel_map[f] for f in fuels if f in fuel_map]

    last_update = None
    if last_update_raw:
        last_update = datetime.fromisoformat(last_update_raw)

    return render_template('index.html', grouped=grouped, last_update=last_update)

#Gold Route
@app.route("/gold")
def gold():
    conn = get_db()
    cur = conn.cursor()

    # Latest gold price
    cur.execute("""
        SELECT mid_price, buy_price, sell_price, fetched_at
        FROM gold_prices
        ORDER BY id DESC
        LIMIT 1
    """)
    row = cur.fetchone()

    # Previous gold price (for delta later if needed)
    cur.execute("""
        SELECT mid_price, buy_price, sell_price
        FROM gold_prices
        ORDER BY id DESC
        LIMIT 1 OFFSET 1
    """)
    prev = cur.fetchone()

    conn.close()

    from datetime import datetime
    last_update = None
    if row:
        last_update = datetime.fromisoformat(row[3])

    return render_template(
        "gold.html",
        current=row,
        previous=prev,
        last_update=last_update,
    )

if __name__ == "__main__":
    init_db()
    app.run(host="0.0.0.0", port=5000)
