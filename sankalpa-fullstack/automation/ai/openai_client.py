"""OpenAI chat completion for HR screening answers."""
import json
import urllib.error
import urllib.request

from core import config
from models.user_config import UserConfig


def build_prompt(question: str, resume_context: str, cfg: UserConfig) -> str:
    return (
        "You are an expert HR job application assistant.\n\n"
        f"Candidate profile:\n{resume_context[:4000]}\n\n"
        "Configuration:\n"
        f"- Experience: {cfg.apply_years} years\n"
        f"- Expected Salary: {cfg.expected_salary}\n"
        f"- Notice Period: {cfg.notice_period}\n\n"
        f"Question:\n{question[:1500]}\n\n"
        "Rules:\n"
        "- Keep answer short\n"
        "- Improve recruiter response chance\n"
        "- Avoid negative wording\n"
        "- Use resume context\n"
        "- If unsure, provide safe professional answer\n"
        "- Return only answer"
    )


def call_openai(question: str, resume_context: str, cfg: UserConfig) -> str:
    api_key = config.OPENAI_API_KEY
    if not api_key:
        return ""

    body = json.dumps(
        {
            "model": config.OPENAI_MODEL,
            "messages": [{"role": "user", "content": build_prompt(question, resume_context, cfg)}],
            "max_tokens": 120,
            "temperature": 0.2,
        }
    ).encode("utf-8")

    req = urllib.request.Request(
        "https://api.openai.com/v1/chat/completions",
        data=body,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=45) as resp:
            payload = json.loads(resp.read().decode("utf-8"))
        choices = payload.get("choices") or []
        if choices:
            content = choices[0].get("message", {}).get("content", "")
            return (content or "").strip()
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError, KeyError):
        pass
    return ""
