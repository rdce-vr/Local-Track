import sqlite3
import requests
from datetime import datetime, timezone, timedelta
from zoneinfo import ZoneInfo

DB_PATH = "/app/data/prices.db"

API_URL = "https://api-pluang.pluang.com/api/v3/asset/gold/pricing"

TZ = ZoneInfo("Asia/Jakarta")

#DATABASE
def db():
    return sqlite3.connect(DB_PATH, timeout=30)

def init_gold_fetcher():
    conn = db()

    conn.execute(
        """
    CREATE TABLE IF NOT EXISTS gold_intraday (
        timestamp DATETIME PRIMARY KEY,
        buy INTEGER NOT  NULL,
        sell INTEGER NOT NULL,
        mid INTEGER NOT NULL
    )
    """)

    conn.execute(
        """
    CREATE TABLE IF NOT EXISTS gold_daily (
        date DATE PRIMARY KEY,
        buy INTEGER NOT NULL,
        sell INTEGER NOT NULL,
        mid INTEGER NOT NULL,
        source_ts DATETIME NOT NULL
    )
    """)

    conn.commit()
    conn.close()

#HELPERS
def fetch_gold_api(days):
    url = f"{API_URL}?daysLimit={days}"
    
    resp = requests.get(url, timeout=15)
    
    resp.raise_for_status()
    
    data = resp.json()

    if data["statusCode"] != 200:
        raise Exception("Gold API returned non-200 statusCode")
    
    return data["data"]

def parse_iso_to_jakarta(iso):
    dt = datetime.fromisoformat(iso.replace("Z", "+00:00"))
    return dt.astimezone(TZ)

def calc_mid(buy, sell):
    return (buy + sell) // 2

#INTRADAY FETCH
def run_gold_intraday_fetch():
    try:
        data = fetch_gold_api(days=1)

        current = data["current"]

        buy = current["buy"]
        sell = current["sell"]
        mid = calc_mid(buy, sell)

        ts = parse_iso_to_jakarta(current["updated_at"])

        conn = db()

        conn.execute(
            """
        INSERT OR REPLACE INTO gold_intraday
        (timestamp, buy, sell, mid)
        VALUES (?, ?, ?, ?)
        """, (ts, buy, sell, mid))

        #cleanup older than 7 days
        cutoff = datetime.now(TZ) - timedelta(days=7)

        conn.execute(
            """
        DELETE FROM gold_intraday
        WHERE timestamp < ?
        """, (cutoff,))

        conn.commit()
        conn.close()

        print("[INFO] Gold intraday stored")

        print("[DEBUG] Intraday gold",
              {
                  "time": ts.strftime("%Y-%m-%d %H:%M:%S"),
                  "buy": buy,
                  "sell": sell,
                  "mid": mid
              })
        
    except Exception as e:

        print("[ERROR] Gold intraday fetch failed", e)

#DAILY HISTORY SYNC (1 HOUR)
def run_gold_history_sync():
    try:
        data = fetch_gold_api(days=30)

        history = data["history"]

        conn = db()

        inserted = 0

        debug_rows = {}

        for row in history:
            buy = row["buy"]
            sell = row["sell"]
            mid = calc_mid(buy, sell)

            ts = parse_iso_to_jakarta(row["updated_at"])

            date = ts.date()

            conn.execute(
                """
            INSERT OR REPLACE INTO gold_daily
            (date, buy, sell, mid, source_ts)
            VALUES (?, ?, ?, ?, ?)
            """, (date, buy, sell, mid, ts))

            debug_rows[str(date)] = mid

            inserted += 1

        conn.commit()
        conn.close()

        print(f"[INFO] Gold history sync complete ({inserted} rows)")

        print("[DEBUG] Gold daily mids:", debug_rows)

    except Exception as e:

        print("[ERROR] Gold history sync failed", e)

#CURRENT = HISTORY FOR FLASK
def get_gold_current():
    conn = db()
    
    row = conn.execute(
        """
    SELECT mid, buy, sell, timestamp
    FROM gold_intraday
    ORDER BY timestamp DESC
    LIMIT 1
    """).fetchone()

    conn.close()

    return row

def get_gold_history(days=30):
    conn = db()

    rows = conn.execute(
        """
    SELECT date, mid
    FROM gold_daily
    ORDER BY date DESC
    LIMIT ?
    """, (days,)).fetchall()

    conn.close()

    rows.reverse()

    return rows

def get_gold_yesterday_mid():
    yesterday = datetime.now(TZ).date() - timedelta(days=1)

    conn = db()

    row = conn.execute(
        """
    SELECT mid
    FROM gold_daily
    WHERE date = ?
    """, (yesterday,)).fetchone()

    conn.close()

    return row[0] if row else None

#INIT
init_gold_fetcher()