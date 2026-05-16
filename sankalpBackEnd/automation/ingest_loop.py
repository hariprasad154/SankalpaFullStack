"""
File-based ingestion: updates ../data/jobs.json and logs.json on an interval.
"""
import random
import time
import uuid
from datetime import datetime

from core import config
from core.logger import log_info
from core.storage import read_json, write_json

_INTERVAL = config.INTERVAL_SECONDS
_KEYWORDS = config.KEYWORDS


def log(msg: str) -> None:
    log_info(msg)


def exists(jobs, company: str, role: str) -> bool:
    for j in jobs:
        if j.get("company") == company and j.get("role") == role:
            return True
    return False


COMPANIES = ["TCS", "Infosys", "Wipro", "HCL", "TechM", "Accenture"]
ROLES = ["Java Developer", "Backend Engineer", "Spring Boot Dev", "API Engineer"]


def fetch_jobs():
    """Safe sample batch; replace with real sources when ready."""
    _ = _KEYWORDS  # reserved for future filtering
    batch = []
    for _ in range(random.randint(1, 3)):
        batch.append(
            {
                "company": random.choice(COMPANIES),
                "role": random.choice(ROLES),
                "source": random.choice(["Naukri", "LinkedIn"]),
            }
        )
    return batch


def run_once() -> None:
    jobs = read_json("jobs.json")
    fetched = fetch_jobs()

    for j in fetched:
        if not exists(jobs, j["company"], j["role"]):
            new = {
                "id": str(uuid.uuid4()),
                "company": j["company"],
                "role": j["role"],
                "status": "Applied",
                "source": j["source"],
                "applied_date": str(datetime.now().date()),
            }
            jobs.append(new)
            log(f"Added {j['company']} - {j['role']} ({j['source']})")

    write_json("jobs.json", jobs)


def run_forever() -> None:
    while True:
        run_once()
        time.sleep(_INTERVAL)
