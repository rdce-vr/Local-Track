import sqlite3
from flask import Flask, render_template_string

DB_PATH = "/app/data/prices.db"

HTML = """
<!doctype html>
<html>
<head>
<meta charset="utf-8">
<title>Harga BBM Jawa Tengah</title>
<style>
  body {
    font-family: system-ui, -apple-system, BlinkMacSystemFont;
    margin: 0;
    padding: 12px;
    background: #ffffff;
  }
  h1 {
    font-size: 16px;
    margin: 0 0 10px 0;
  }
  table {
    width: 100%;
    border-collapse: collapse;
    font-size: 14px;
  }
  th, td {
    padding: 8px;
    border-bottom: 1px solid #e0e0e0;
    text-align: left;
  }
  th {
    background: #f5f5f5;
    font-weight: 600;
  }
</style>
</head>
<body>
<h1>Harga BBM – Jawa Tengah</h1>
<table>
  <tr>
    <th>Jenis BBM</th>
    <th>Harga (Rp)</th>
    <th>Update Terakhir</th>
  </tr>
  {% for fuel, price, updated in rows %}
  <tr>
    <td>{{ fuel }}</td>
    <td>{{ "{:,}".format(price).replace(",", ".") }}</td>
    <td>{{ updated }}</td>
  </tr>
  {% endfor %}
</table>
</body>
</html>
"""

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
    return render_template_string(HTML, rows=rows)

if __name__ == "__main__":
    init_db()
    app.run(host="0.0.0.0", port=5000)
