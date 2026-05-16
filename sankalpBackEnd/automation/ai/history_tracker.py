"""Track answered screening questions for analytics."""
from datetime import datetime

from core.storage import read_json, write_json


def record_question_history(
    question: str,
    answer: str,
    company: str = "",
    job_title: str = "",
    user_id: str | None = None,
) -> None:
    data = read_json("question_history.json", user_id)
    if not isinstance(data, list):
        data = []
    data.append(
        {
            "question": (question or "")[:500],
            "answer": (answer or "")[:500],
            "company": (company or "")[:255],
            "job_title": (job_title or "")[:500],
            "timestamp": datetime.now().isoformat(timespec="seconds"),
        }
    )
    if len(data) > 500:
        data = data[-500:]
    write_json("question_history.json", data, user_id)
