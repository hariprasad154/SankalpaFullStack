"""Question → answer cache (Sheet Cache tab via backend, local JSON fallback)."""
import hashlib

from core.storage import read_json, write_json


def _cache_key(question: str) -> str:
    normalized = " ".join((question or "").lower().split())
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()[:32]


def _backend_cache_get(question: str) -> str:
    import os

    backend = os.getenv("BACKEND_URL_SANKALPA", "").strip()
    if not backend:
        return ""
    try:
        import httpx

        from sheets_client import WORKER_API_KEY

        with httpx.Client(timeout=15) as client:
            resp = client.get(
                f"{backend.rstrip('/')}/api/internal/cache",
                params={"question": (question or "")[:500]},
                headers={"X-Worker-Key": WORKER_API_KEY},
            )
            if resp.status_code == 200:
                return (resp.json().get("answer") or "").strip()
    except Exception:  # noqa: BLE001
        pass
    return ""


def _backend_cache_set(question: str, answer: str) -> None:
    import os

    backend = os.getenv("BACKEND_URL_SANKALPA", "").strip()
    if not backend or not (question or "").strip() or not (answer or "").strip():
        return
    try:
        import httpx

        from sheets_client import WORKER_API_KEY

        with httpx.Client(timeout=15) as client:
            client.post(
                f"{backend.rstrip('/')}/api/internal/cache",
                params={"question": (question or "")[:500], "answer": (answer or "")[:2000]},
                headers={"X-Worker-Key": WORKER_API_KEY},
            )
    except Exception:  # noqa: BLE001
        pass


def get_cached_answer(question: str, user_id: str | None = None) -> str:
    ans = _backend_cache_get(question)
    if ans:
        return ans

    data = read_json("cache.json", user_id)
    if not isinstance(data, dict):
        return ""
    entry = data.get(_cache_key(question))
    if isinstance(entry, dict):
        return (entry.get("answer") or "").strip()
    if isinstance(entry, str):
        return entry.strip()
    return ""


def set_cached_answer(question: str, answer: str, user_id: str | None = None) -> None:
    _backend_cache_set(question, answer)

    data = read_json("cache.json", user_id)
    if not isinstance(data, dict):
        data = {}
    data[_cache_key(question)] = {
        "question": (question or "")[:500],
        "answer": (answer or "").strip(),
    }
    write_json("cache.json", data, user_id)
