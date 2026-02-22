import signal
import sys
from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.events import EVENT_JOB_ERROR, EVENT_JOB_EXECUTED
from fetcher import run_fetch, run_gold_fetch
from app import init_db

SCHEDULER_TZ = "Asia/Jakarta"

def job_listener(event):
    if event.exception:
        print(f"[ERROR] Job {event.job_id} failed: {event.exception}")
        import traceback
        traceback.print_exception(event.exception)
    else:
        print(f"[INFO] Job {event.job_id} completed successfully")

def shutdown(scheduler):
    if scheduler.running:
        print("[INFO] Shutting down scheduler...")
        scheduler.shutdown()
    sys.exit(0)

def main():
    scheduler = BlockingScheduler(timezone=SCHEDULER_TZ)
    scheduler.add_listener(job_listener, EVENT_JOB_EXECUTED | EVENT_JOB_ERROR)

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
        hour=0,
        minute=5,
        id="daily_gold_price_fetch",
        replace_existing=True,
    )

    signal.signal(signal.SIGINT, lambda s, f: shutdown(scheduler))
    signal.signal(signal.SIGTERM, lambda s, f: shutdown(scheduler))

    print(f"[INFO] Scheduler started with {len(scheduler.get_jobs())} jobs")
    scheduler.start()

if __name__ == "__main__":
    main()
