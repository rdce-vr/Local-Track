import requests
import os

TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")"

def send_telegram(msg):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    requests.post(url, json={
        "chat_id": CHAT_ID,
        "text": msg,
        "parse_mode": "HTML"
    })

DISCORD_WEBHOOK = os.getenv("DISCORD_WEBHOOK_URL")

def send_discord(msg):
    requests.post(DISCORD_WEBHOOK, json={
        "content": msg
    })