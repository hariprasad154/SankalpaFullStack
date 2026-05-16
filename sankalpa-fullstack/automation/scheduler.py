"""
APScheduler — auto apply every 6 hours (0 */6 * * *).

Run on worker machine alongside backend URL:
  BACKEND_URL_SANKALPA=http://localhost:8000 python scheduler.py
"""
import os

from apscheduler.schedulers.blocking import BlockingScheduler

from worker import run_once

HOURS = int(os.getenv("AUTO_APPLY_INTERVAL_HOURS", "6"))


def main() -> None:
    scheduler = BlockingScheduler()
    scheduler.add_job(run_once, "interval", hours=HOURS, id="sankalpa_auto_apply")
    print(f"Scheduler: batch apply every {HOURS} hour(s). Ctrl+C to stop.")
    scheduler.start()


if __name__ == "__main__":
    main()
