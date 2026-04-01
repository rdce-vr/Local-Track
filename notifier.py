import requests

TELEGRAM_TOKEN = "YOUR_TOKEN"
CHAT_ID = "YOUR_CHAT_ID"

def send_telegram(msg):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    requests.post(url, json={
        "chat_id": CHAT_ID,
        "text": msg,
        "parse_mode": "HTML"
    })

DISCORD_WEBHOOK = "https://discord.com/api/webhooks/..."

def send_discord(msg):
    requests.post(DISCORD_WEBHOOK, json={
        "content": msg
    })