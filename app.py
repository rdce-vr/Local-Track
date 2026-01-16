import sqlite3
from datetime import datetime
from flask import Flask, render_template

DB_PATH = "/app/data/prices.db"

app = Flask(__name__)

def get_db():
    return sqlite3.connect(DB_PATH, timeout=30)

def init_db():
    conn = get_db()
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
    conn.commit()
    conn.close()

FUEL_GROUPS = {
    "Gasoline": [
        "PERTALITE",
        "PERTASHOP",
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
    cur.execute("""
        SELECT fuel_type, price, fetched_at
        FROM fuel_prices
        WHERE id IN (
            SELECT MAX(id)
            FROM fuel_prices
            GROUP BY fuel_type
        )
    """)
    rows = cur.fetchall()
    conn.close()

    fuel_map = {fuel.upper(): (fuel, price, fetched_at) for fuel, price, fetched_at in rows}

    grouped = {}
    for group, fuels in FUEL_GROUPS.items():
        grouped[group] = [fuel_map[f] for f in fuels if f in fuel_map]

    last_update = rows[0][2] if rows else None

    return render_template('index.html', grouped=grouped, last_update=last_update)


if __name__ == "__main__":
    init_db()
    app.run(host="0.0.0.0", port=5000)
