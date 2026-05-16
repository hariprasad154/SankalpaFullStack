"""
Selenium worker — run locally or on VPS (NOT Render).

Polls backend for users with auto_apply_enabled in Google Sheet.
"""
import os
import subprocess
import sys
import time

import httpx

BACKEND_URL_SANKALPA = os.getenv("BACKEND_URL_SANKALPA", "http://localhost:8000").rstrip("/")
WORKER_API_KEY = os.getenv("WORKER_API_KEY", "worker-dev-key")
MAX_RETRIES = int(os.getenv("WORKER_MAX_RETRIES", "2"))
_AUTOMATION_DIR = os.path.dirname(os.path.abspath(__file__))


def fetch_active_users() -> list:
    headers = {"X-Worker-Key": WORKER_API_KEY}
    with httpx.Client(timeout=60, follow_redirects=True) as client:
        resp = client.get(f"{BACKEND_URL_SANKALPA}/api/internal/active-users", headers=headers)
        resp.raise_for_status()
        return resp.json()


def run_batch_for_user(username: str) -> int:
    from sheets_client import patch_runtime, post_log

    patch_runtime(running=True, last_error="")
    post_log("Worker: starting batch apply")

    env = os.environ.copy()
    env["SANKALPA_USERNAME"] = username
    env["SANKALPA_USER_ID"] = username
    env["AUTOMATION_MODE"] = "batch"
    env["BACKEND_URL_SANKALPA"] = BACKEND_URL_SANKALPA
    env["WORKER_API_KEY"] = WORKER_API_KEY

    code = 1
    for attempt in range(MAX_RETRIES + 1):
        if attempt > 0:
            post_log(f"Worker: retry {attempt}/{MAX_RETRIES}")
            patch_runtime(last_log=f"Retrying batch ({attempt}/{MAX_RETRIES})")
            time.sleep(5)

        code = subprocess.run(
            [sys.executable, "main.py", "batch"],
            cwd=_AUTOMATION_DIR,
            env=env,
        ).returncode

        if code == 0:
            break

    patch_runtime(running=False, current_job="")
    if code != 0:
        patch_runtime(last_error=f"Worker exited with code {code}")
    post_log(f"Worker: batch finished (exit {code})")
    return code


def run_once() -> None:
    users = fetch_active_users()
    if not users:
        print("No users with auto_apply_enabled=true in Google Sheet.")
        return
    for row in users:
        name = row.get("username", "")
        if not name:
            continue
        print(f"Batch apply for: {name}")
        code = run_batch_for_user(name)
        print(f"  exit code: {code}")


if __name__ == "__main__":
    run_once()
