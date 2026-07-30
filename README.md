# Local-Track

A personal fuel and gold price tracker for Indonesia. Runs as a small Flask web app backed by SQLite, with a background scheduler that periodically fetches prices and sends notifications when they change.

Live instance (personal): `flpr.rdce-vr.my.id`

## Features

- **Fuel prices** — tracks Pertamina fuel prices (Pertalite, Pertamax family, Biosolar, Dexlite, Pertamina Dex, etc.), grouped into Gasoline and Diesel categories, with the latest price and delta vs. the previous recorded price for each fuel type.
- **Gold prices** — tracks intraday and daily gold buy/sell/mid prices from the Pluang API, with a 30-day history sparkline and a delta indicator (up/down/unchanged) vs. the previous available close.
- **Notifications** — sends alerts via Telegram and/or Discord webhook when prices change.
- **Scheduler** — a separate background process (`scheduler.py`) handles periodic fetching so the web process stays responsive.
- **Dockerized** — ships as a single image, run as two services (`web` and `scheduler`) via `docker-compose.yml`.

## Tech stack

- Python / Flask
- SQLite (file-based, no external DB needed)
- HTML/CSS/JS templates (server-rendered, no frontend framework)
- Docker / Docker Compose

## Project structure

```
.
├── app.py                # Flask web app (routes: "/" fuel dashboard, "/gold" gold dashboard)
├── fetcher.py             # Fuel price fetching logic
├── fetcher_gold.py         # Gold price fetching logic (Pluang API) + SQLite storage
├── scheduler.py            # Background job runner for periodic fetches
├── notifier.py              # Telegram / Discord notification logic
├── templates/               # Jinja2 HTML templates
├── static/                  # CSS/JS/static assets
├── service-worker.js         # PWA service worker
├── Dockerfile
├── docker-compose.yml
└── .env.example
```

## Setup

### 1. Configure environment variables

Copy the example env file and fill in your notification credentials:

```bash
cp .env.example .env
```

```env
TELEGRAM_BOT_TOKEN=
TELEGRAM_CHAT_ID=
DISCORD_WEBHOOK_URL=
```

Any of these can be left blank if you don't want that notification channel.

### 2. Build the image

```bash
docker build -t fueltracker:local .
```

### 3. Run with Docker Compose

```bash
docker-compose up -d
```

This starts two containers:

| Service     | Purpose                                  | Port   |
|-------------|-------------------------------------------|--------|
| `web`       | Flask app serving the dashboards           | `5000` |
| `scheduler` | Periodic fetch jobs (fuel + gold + notify) | —      |

Both share a persistent `./data` volume, which holds the SQLite database (`prices.db`).

### 4. Access the dashboard

- Fuel dashboard: `http://<host>:5000/`
- Gold dashboard: `http://<host>:5000/gold`

## Data sources

- **Fuel prices**: MyPertamina public pricing data.
- **Gold prices**: Pluang gold pricing API (`api-pluang.pluang.com`).

## Notes

- Designed for personal/self-hosted use — typically deployed behind a Cloudflare Tunnel or reverse proxy rather than exposed directly, since it has no built-in authentication.
- The SQLite database is the only persistent state; back up the `./data` directory if you want to preserve price history.

## License

Personal project — no license specified.