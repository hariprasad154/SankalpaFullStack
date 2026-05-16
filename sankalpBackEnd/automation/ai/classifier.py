"""Classify screening questions by type."""
QUESTION_TYPES = {
    "salary": ["ctc", "salary", "expected", "compensation", "lpa"],
    "notice": ["notice", "joining", "lwd", "last working"],
    "relocation": ["relocate", "location", "shift", "wfo", "hybrid", "office"],
    "experience": ["years of experience", "worked on", "experience in", "how long"],
    "skills": ["java", "spring", "docker", "kafka", "aws", "kubernetes", "skill"],
    "project": ["project", "architecture", "responsibility", "describe your"],
    "yesno": ["immediate", "join us", "willing", "yes or no", "can you join"],
}


def classify_question(question: str) -> str:
    q = (question or "").lower()
    if not q.strip():
        return "unknown"
    for qtype, keywords in QUESTION_TYPES.items():
        if any(kw in q for kw in keywords):
            return qtype
    return "unknown"
