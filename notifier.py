import requests

# --- CONFIG ---
TELEGRAM_TOKEN = "8643859090:AAEqg0hO8h8_yy9vZWAAkSKcTe7G_5fIjuQ"
TELEGRAM_CHAT_ID = "-1003907542069"

DISCORD_WEBHOOK = "https://discord.com/api/webhooks/1500888377237573633/X7fJZDAce61Ax5suS5LXbzaGmNJdDiIyQWUFIlikL9Z7g1XbdYXPNO4_3mjRDy-Lg2Ed"


def send_telegram(message):
    if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID:
        return

    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    requests.post(url, json={
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message,
        "parse_mode": "HTML"
    })


def send_discord(message):
    if not DISCORD_WEBHOOK:
        return

    requests.post(DISCORD_WEBHOOK, json={
        "content": message
    })