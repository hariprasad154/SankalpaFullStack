"""
Mark3.txt — recommended jobs + tabs → JSON + logs.

mark2.txt: Profile tab is excluded by default (different DOM / lazy load / often not
clickable). Override with NAUKRI_FLOW_TABS=comma,separated,labels if needed.
"""
import os
import time
import uuid
from datetime import datetime

from dotenv import load_dotenv
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

load_dotenv()

_NAUKRI_HOME_URL = os.getenv("NAUKRI_HOME_URL", "https://www.naukri.com/mnjuser/homepage")
_RECOMMENDED_URL = os.getenv(
    "NAUKRI_RECOMMENDED_URL",
    "https://www.naukri.com/mnjuser/recommendedjobs",
)
_FLOW_MAX_JOBS = int(os.getenv("FLOW_MAX_JOBS", "10"))

# mark2.txt: skip "Profile" unless user sets NAUKRI_FLOW_TABS explicitly.
_TABS_RAW = os.getenv("NAUKRI_FLOW_TABS", "").strip()
if _TABS_RAW:
    _TABS = [t.strip() for t in _TABS_RAW.split(",") if t.strip()]
else:
    _TABS = [
        "Applies",
        "Top Candidate",
        "Preferences",
        "You might like",
    ]


def _read_jobs():
    from ingest_loop import read_json

    data = read_json("jobs.json")
    return data if isinstance(data, list) else []


def _write_jobs(data) -> None:
    from ingest_loop import write_json

    write_json("jobs.json", data)


def _flow_log(msg: str) -> None:
    from ingest_loop import log

    log(msg)


def open_recommended_page(driver) -> None:
    print("Opening recommended jobs page")
    _flow_log("Flow: opening recommended jobs page")
    driver.get(_RECOMMENDED_URL)
    time.sleep(6)


def extract_jobs(driver, tab: str):
    jobs = []
    elements = driver.find_elements(By.CSS_SELECTOR, "a.title")
    limit = min(10000, max(1, _FLOW_MAX_JOBS))
    for el in elements[:limit]:
        role = (el.text or "").strip()
        if not role:
            continue
        href = el.get_attribute("href") or ""
        jobs.append(
            {
                "company": "Naukri",
                "role": role,
                "status": "Captured",
                "source": tab,
                "link": href,
                "time": str(datetime.now()),
            }
        )
    return jobs


def click_tab(driver, tab_name: str) -> bool:
    wait = WebDriverWait(driver, 20)
    try:
        print(f"Clicking tab: {tab_name}")
        tab_el = wait.until(
            EC.element_to_be_clickable(
                (By.XPATH, f"//*[contains(text(),'{tab_name}')]"),
            ),
        )
        driver.execute_script("arguments[0].click();", tab_el)
        time.sleep(4)
        return True
    except Exception:  # noqa: BLE001
        print(f"Failed tab: {tab_name}")
        _flow_log(f"Tab failed: {tab_name}")
        return False


def process_all_tabs(driver):
    existing = _read_jobs()
    all_jobs = []

    for tab in _TABS:
        if not click_tab(driver, tab):
            continue

        jobs = extract_jobs(driver, tab)

        for job in jobs:
            duplicate = any(
                j.get("role") == job["role"] and j.get("company") == job["company"]
                for j in existing
            )

            if duplicate:
                job["status"] = "Skipped"
            else:
                job["id"] = str(uuid.uuid4())
                job["applied_date"] = None
                existing.append(job)

            _flow_log(f"{job['status']} - {job['role']} ({tab})")
            all_jobs.append(job)

    _write_jobs(existing)
    return all_jobs


def run_flow(driver) -> list:
    print("Starting recommended flow")
    _flow_log("Flow: run_flow start")

    try:
        open_recommended_page(driver)
        jobs = process_all_tabs(driver)
        print("Total jobs:", len(jobs))
        _flow_log(f"Flow: processed {len(jobs)} job rows across tabs")
        return jobs
    except Exception as e:  # noqa: BLE001
        print("FLOW ERROR:", e)
        _flow_log(f"Flow error: {e!s}")
        raise


def run_mark3_flow() -> None:
    from naukri import _credentials_ok, login_naukri, start_driver

    driver = None
    try:
        _flow_log("Flow: starting Chrome")
        driver = start_driver()

        if _credentials_ok():
            login_naukri(driver)
        else:
            _flow_log("Flow: NAUKRI credentials not set; continuing without form login")

        driver.get(_NAUKRI_HOME_URL)
        time.sleep(5)

        run_flow(driver)

    except Exception as e:  # noqa: BLE001
        print("FLOW ERROR:", e)
        _flow_log(f"Flow error: {e!s}")
        raise
    finally:
        if driver is not None:
            driver.quit()
        _flow_log("Flow: browser closed")
