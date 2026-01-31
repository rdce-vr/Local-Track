from apscheduler.schedulers.blocking import BlockingScheduler
from fetcher import run_fetch, run_gold_fetch

SCHEDULER_TZ = "Asia/Jakarta"

def main():
    scheduler = BlockingScheduler(timezone=SCHEDULER_TZ)

    scheduler.add_job(
        run_fetch,
        trigger="cron",
        hour=3,
        minute=0,
        id="daily_fuel_price_fetch",
        replace_existing=True,
    )

    scheduler.add_job(
        run_gold_fetch, 
        trigger="cron", 
        hours=6,
        minute=0, 
        id="daily_gold_price_fetch", 
        replace_existing=True)

    print("[INFO] Scheduler started (03:00 Asia/Jakarta)")
    scheduler.start()

if __name__ == "__main__":
    main()
