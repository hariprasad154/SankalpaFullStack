"""Post logs, applications, and runtime state to backend."""
import os

import httpx

BACKEND_URL = (
    os.getenv("BACKEND_URL")
    or os.getenv("BACKEND_URL_SANKALPA")
    or os.getenv("BACKEND_BASE_URL")
    or "http://localhost:8000"
).rstrip("/")
BACKEND_URL_SANKALPA = BACKEND_URL
WORKER_API_KEY = os.getenv("WORKER_API_KEY", "worker-dev-key")


def _username() -> str:
    return os.getenv("SANKALPA_USERNAME") or os.getenv("SANKALPA_USER_ID") or "default"


def _headers() -> dict:
    return {"X-Worker-Key": WORKER_API_KEY}


def set_current_job(job_title: str) -> None:
    patch_runtime(current_job=(job_title or "")[:500], last_error="")


def patch_runtime(**fields) -> None:
    try:
        body = {"username": _username(), **fields}
        with httpx.Client(timeout=15) as client:
            client.post(
                f"{BACKEND_URL}/api/internal/runtime-state",
                json=body,
                headers=_headers(),
            )
    except Exception:  # noqa: BLE001
        pass


def post_log(message: str) -> None:
    try:
        with httpx.Client(timeout=15) as client:
            client.post(
                f"{BACKEND_URL}/api/internal/log",
                json={"username": _username(), "message": message},
                headers=_headers(),
            )
    except Exception:  # noqa: BLE001
        pass


def post_application(
    job_title: str,
    company: str,
    status: str,
    error: str = "",
) -> None:
    sheet_status = status
    if str(status).upper() in ("APPLIED", "SUCCESS"):
        sheet_status = "SUCCESS"
    elif str(status).upper() in ("FAILED", "APPLYUNCERTAIN", "FAIL"):
        sheet_status = "FAILED"
    try:
        with httpx.Client(timeout=15) as client:
            client.post(
                f"{BACKEND_URL}/api/internal/application",
                json={
                    "username": _username(),
                    "job_title": job_title,
                    "company": company,
                    "status": sheet_status,
                    "error": (error or "")[:500],
                },
                headers=_headers(),
            )
    except Exception:  # noqa: BLE001
        pass
