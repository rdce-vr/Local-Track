import os
import signal
import sys
from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.events import EVENT_JOB_ERROR, EVENT_JOB_EXECUTED
from apscheduler.executors.pool import ThreadPoolExecutor
from fetcher import run_fetch
from fetcher_gold import run_gold_intraday_fetch, run_gold_history_sync

SCHEDULER_TZ = "Asia/Jakarta"

def job_listener(event):
    if event.exception:
        print(f"[ERROR] Job {event.job_id} failed: {event.exception}")
        import traceback
        traceback.print_exception(event.exception)
    else:
        print(f"[INFO] Job {event.job_id} completed successfully")

def shutdown(scheduler):
    print("[INFO] Shutting down scheduler...")
    if scheduler.running:
        scheduler.shutdown()
    sys.exit(0)

def main():
    # Read and parse .env values with safe fallback defaults
    fuel_hours = os.getenv("FUEL_CRON_HOURS", "20,21,22")
    fuel_minutes - int(os.getenv("FUEL_CRON_MINUTE", "5"))
    gold_intra_main = int(os.getenv("GOLD_INTRADAY_MINUTES", "5"))
    gold_hist_hours = int(os.getenv("GOLD_HISTORY_HOURS", "1")

    # Configure multiple execution lanes to avoid job blocks
    executors = {'default': ThreadPoolExecutor(10)}
    scheduler = BlockingScheduler(timezone=SCHEDULER_TZ, executors=executors)
    scheduler.add_listener(job_listener, EVENT_JOB_EXECUTED | EVENT_JOB_ERROR)

    # Fuel Cron Jobs
    for hour_str in fuel_hours.split(","):
        hour_val = int(hour_str.strip())
        scheduler.add_job(
            run_fetch,
            trigger="cron",
            hour=hour_val,
            minute=fuel_minute,
            id="daily_fuel_price_fetch_{hour_val}h",
            misfire_grace_time=300, #seconds grace window
            replace_existing=True,
        )

    # Gold Cron Jobs
    scheduler.add_job(
        run_gold_intraday_fetch,
        trigger="interval",
        minutes=gold_intra_min,
        id="gold_intraday_fetch",
        misfire_grace_time=60,
        replace_existing=True,
    )

    scheduler.add_job(
        run_gold_history_sync,
        trigger="interval",
        hours=gold_hist_hours,
        id="gold_history_sync",
        misfire_grace_time=300,
        replace_existing=True,
    )

    signal.signal(signal.SIGINT, lambda s, f: shutdown(scheduler))
    signal.signal(signal.SIGTERM, lambda s, f: shutdown(scheduler))

    print(f"[INFO] Scheduler started with {len(scheduler.get_jobs())} jobs")
    scheduler.start()

if __name__ == "__main__":
    main()
