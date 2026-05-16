"""Validate and sanitize AI answers before typing into popups."""
FALLBACK = "Can discuss further during interview"
MAX_LEN = 500


def validate_answer(answer: str) -> str:
    text = " ".join((answer or "").split()).strip()
    if not text:
        return FALLBACK
    if len(text) > MAX_LEN:
        text = text[:MAX_LEN].rsplit(" ", 1)[0] or text[:MAX_LEN]
    low = text.lower()
    if low in ("null", "none", "n/a", "undefined"):
        return FALLBACK
    return text
