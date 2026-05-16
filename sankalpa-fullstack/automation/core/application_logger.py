"""Log apply outcomes to Google Sheets via backend API."""
import os


def _username() -> str:
    return os.getenv("SANKALPA_USERNAME") or os.getenv("SANKALPA_USER_ID") or "default"


def log_application(
    username: str | None = None,
    company: str = "",
    role: str = "",
    status: str = "SUCCESS",
    error: str = "",
) -> None:
    uname = username or _username()
    sheet_status = "SUCCESS" if str(status).upper() in ("SUCCESS", "APPLIED", "Applied") else "FAILED"
    try:
        from sheets_client import post_application

        post_application(
            job_title=role,
            company=company,
            status=sheet_status,
            error=error,
        )
    except Exception:  # noqa: BLE001
        pass
