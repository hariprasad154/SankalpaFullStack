"""Find resume lines relevant to a screening question."""
from core import config


def search_resume_context(question: str, resume_text: str) -> str:
    if not config.AI_ENABLE_RESUME_CONTEXT:
        return (resume_text or "")[:2000]

    q = (question or "").lower()
    text = (resume_text or "").strip()
    if not text:
        return ""

    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
    if not lines:
        return text[:2000]

    tokens = [t for t in q.replace("?", " ").split() if len(t) > 2]
    scored: list[tuple[int, str]] = []
    for line in lines:
        low = line.lower()
        score = sum(1 for t in tokens if t in low)
        if score > 0:
            scored.append((score, line))

    if scored:
        scored.sort(key=lambda x: x[0], reverse=True)
        top = [ln for _, ln in scored[:5]]
        return "\n".join(top)

    return "\n".join(lines[:8])[:2000]
