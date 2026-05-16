"""Worker runtime helpers — sync live state to backend API."""
import os


def _username() -> str:
    return os.getenv("SANKALPA_USERNAME") or os.getenv("SANKALPA_USER_ID") or "default"


def update_runtime(username: str | None = None, **fields) -> None:
    try:
        from sheets_client import patch_runtime

        if username:
            os.environ["SANKALPA_USERNAME"] = username
        patch_runtime(**fields)
    except Exception:  # noqa: BLE001
        pass


def increment_applied(username: str | None = None) -> None:
    update_runtime(username=username, last_log="Applied successfully")


def increment_failed(username: str | None = None, error: str = "") -> None:
    try:
        import httpx

        from sheets_client import BACKEND_URL, WORKER_API_KEY, patch_runtime, _headers

        uname = username or _username()
        with httpx.Client(timeout=15) as client:
            resp = client.post(
                f"{BACKEND_URL}/api/internal/runtime-increment-failed",
                json={"username": uname, "error": (error or "")[:500]},
                headers=_headers(),
            )
            if resp.status_code != 200:
                patch_runtime(last_error=(error or "")[:500])
    except Exception:  # noqa: BLE001
        patch_runtime(last_error=(error or "")[:500])
