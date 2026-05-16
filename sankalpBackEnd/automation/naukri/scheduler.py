"""
APScheduler — auto apply every N hours.

Run: cd automation && python -m naukri.scheduler
Or:  python scheduler.py (root shim)
"""
import os
import sys

_AUTOMATION_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _AUTOMATION_DIR not in sys.path:
    sys.path.insert(0, _AUTOMATION_DIR)

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
