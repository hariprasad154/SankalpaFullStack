"""Tune answers for higher recruiter response rates."""
from ai.classifier import classify_question


_DEFAULTS = {
    "relocation": "Yes",
    "notice": "Yes",
    "salary": "",
    "skills": "Basic working experience",
    "experience": "Yes",
    "project": "",
    "unknown": "Can discuss further during interview",
}


def optimize_answer(question: str, answer: str, q_type: str | None = None) -> str:
    from core import config

    if not config.AI_ENABLE_OPTIMIZER:
        return (answer or "").strip()

    q_type = q_type or classify_question(question)
    text = (answer or "").strip()

    if not text:
        return _DEFAULTS.get(q_type, _DEFAULTS["unknown"])

    low_q = (question or "").lower()
    low_a = text.lower()

    if q_type == "relocation" or "relocate" in low_q:
        return "Yes"
    if q_type == "notice" or "join immediately" in low_q or "within 15 days" in low_q:
        if low_a in ("no", "not", "cannot"):
            return "Yes"
    if q_type == "skills" and any(s in low_q for s in ("docker", "kafka", "kubernetes")):
        if len(text) < 4 or low_a in ("no", "none", "n/a"):
            return "Basic working experience"
    if q_type == "unknown" and len(text) < 3:
        return _DEFAULTS["unknown"]

    if any(w in low_a for w in ("cannot", "won't", "refuse", "never")):
        return "Can discuss further during interview"

    return text[:500]
