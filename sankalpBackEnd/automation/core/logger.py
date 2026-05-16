"""Structured logs to data/logs.json (frontend-readable)."""
from datetime import datetime

from core.storage import read_json, write_json


def _append(level: str, message: str, user_id: str | None = None) -> None:
    logs = read_json("logs.json", user_id)
    if not isinstance(logs, list):
        logs = []
    logs.append(
        {
            "time": datetime.now().strftime("%H:%M:%S"),
            "timestamp": datetime.now().isoformat(timespec="seconds"),
            "level": level,
            "message": message,
        }
    )
    write_json("logs.json", logs, user_id)


def log_info(message: str, user_id: str | None = None) -> None:
    _append("info", message, user_id)
    try:
        from sheets_client import post_log

        post_log(message)
    except Exception:  # noqa: BLE001
        pass


def log_warning(message: str, user_id: str | None = None) -> None:
    _append("warning", message, user_id)


def log_error(message: str, user_id: str | None = None) -> None:
    _append("error", message, user_id)
    try:
        from sheets_client import patch_runtime, post_log

        post_log(message)
        patch_runtime(last_error=(message or "")[:500])
    except Exception:  # noqa: BLE001
        pass


def log(message: str, user_id: str | None = None) -> None:
    """Backward-compatible alias used by legacy automation code."""
    log_info(message, user_id)
