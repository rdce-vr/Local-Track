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
        ORDER BY fuel_type
    """)
    rows = cur.fetchall()
    conn.close()

    prices = [
        {
            "fuel_type": r[0],
            "price": r[1],
            "fetched_at": datetime.strptime(r[2], "%Y-%m-%d %H:%M:%S"),
        }
        for r in rows
    ]

    return render_template("index.html", prices=prices)

if __name__ == "__main__":
    init_db()
    app.run(host="0.0.0.0", port=5000)
