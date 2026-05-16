"""Answer cache — local JSON + Google Sheets Cache tab via backend."""
from ai.cache import get_cached_answer, set_cached_answer


def get_cache(question: str, user_id: str | None = None) -> str:
    return get_cached_answer(question, user_id)


def save_cache(question: str, answer: str, user_id: str | None = None) -> None:
    set_cached_answer(question, answer, user_id)
