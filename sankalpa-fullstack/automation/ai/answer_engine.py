"""AI screening answer engine — cache → classify → resume → OpenAI → optimize."""
import os

from ai.cache_manager import get_cache, save_cache
from ai.classifier import classify_question
from ai.history_tracker import record_question_history
from ai.hr_optimizer import optimize_answer
from ai.openai_client import call_openai
from ai.resume_parser import read_resume
from ai.resume_search import search_resume_context
from ai.validators import validate_answer
from core import config
from core.logger import log_info
from models.user_config import UserConfig, load_user_config


def build_qa_rules(cfg: UserConfig | None = None) -> list[tuple[tuple[str, ...], str]]:
    """Fast keyword rules (Qa.txt style) — checked before cache."""
    u = cfg or load_user_config()
    fixed_ctc = os.getenv("NAUKRI_QA_FIXED_CTC", "750000")
    var_ctc = os.getenv("NAUKRI_QA_VARIABLE_CTC", "50000")
    offer_ctc = os.getenv("NAUKRI_QA_OFFER_CTC", "1250000")
    secondary_exp = os.getenv("NAUKRI_QA_SECONDARY_SKILL_YEARS", "2.5 to 3")
    proficiency = os.getenv("NAUKRI_QA_PROFICIENCY", "8")
    domain_ans = os.getenv("NAUKRI_QA_DOMAIN", "Yes")
    city = os.getenv("NAUKRI_QA_CURRENT_CITY", "Chennai")
    grad_year = os.getenv("NAUKRI_QA_GRAD_YEAR", "2022")
    cgpa = os.getenv("NAUKRI_QA_CGPA", "8.5")
    job_change = os.getenv(
        "NAUKRI_QA_JOB_CHANGE",
        "Seeking better growth opportunities and work on large-scale distributed systems.",
    )
    why_join = os.getenv(
        "NAUKRI_QA_WHY_JOIN",
        "Strong product culture and opportunity to contribute Java/Spring Boot skills.",
    )
    project_ans = os.getenv(
        "NAUKRI_QA_PROJECT",
        "Microservices with Spring Boot and Kafka; DB optimization and Helm deployments.",
    )
    certs = os.getenv("NAUKRI_QA_CERTS", "AWS Certified Developer")

    return [
        (("last drawn salary", "currently unemployed"), u.current_salary),
        (("current annual ctc", "your current annual ctc", "current ctc"), u.current_salary),
        (("fixed component", "fixed part of ctc"), fixed_ctc),
        (("variable component", "variable part"), var_ctc),
        (("expected ctc", "expected annual", "expected salary"), u.expected_salary),
        (("negotiable", "expected salary negotiable", "salary negotiable"), "Yes"),
        (("official notice period", "notice period (in days)", "notice period in days"), u.notice_period),
        (("currently serving your notice", "currently serving notice", "serving your notice"), "Yes"),
        (("last working day", "lwd", "mention lwd", "serving notice period"), u.lwd_reply),
        (("join us immediately", "within 15 days", "join immediately"), "Yes"),
        (("buy-out", "notice period negotiable"), "Yes"),
        (("other job offers", "job offers in hand", "offers in hand"), "Yes"),
        (("offered ctc", "offer in hand", "if you have an offer"), offer_ctc),
        (("total years of professional experience", "total years of experience"), u.apply_years),
        (("relevant experience", "years of experience do you have"), u.apply_years),
        (("spring boot", "secondary skill"), secondary_exp),
        (("proficiency", "scale of 1 to 10", "scale of 1-10", "rate your proficiency"), proficiency),
        (("kubernetes", "amazon web services", "worked on aws", "worked on kubernetes"), "Yes"),
        (("managed a team", "team size"), "0"),
        (("fintech", "healthcare", "domain experience"), domain_ans),
        (("current city", "city of residence"), city),
        (("willing to relocate", "relocate to"), "Yes"),
        (("wfo", "office 5 days", "5 days a week", "from the office"), "Yes"),
        (("hybrid work", "hybrid model"), "Yes"),
        (("rotational shift", "night shift"), "No"),
        (("valid passport",), "Yes"),
        (("b1/b2", "h1b visa", "h1-b"), "No"),
        (("highest qualification",), "B.Tech"),
        (("year of graduation",), grad_year),
        (("percentage", "cgpa in your"), cgpa),
        (("full-time course", "part-time", "distance"), "Full-time"),
        (("gaps in your education", "gaps in your career"), "No"),
        (("interviewed by this company", "last 6 months"), "No"),
        (("looking for a job change", "why are you looking"), job_change),
        (("why do you want to join", "why join"), why_join),
        (("most recent project", "briefly describe your"), project_ans),
        (("certifications", "certification"), certs),
        (("laptop", "stable internet", "internet connection"), "Yes"),
        (
            (
                "key skill",
                "primary skill",
                "technology stack",
                "tech stack",
                "technologies",
                "skillset",
                "skill",
            ),
            u.skills_reply,
        ),
    ]


def keyword_answer(question_lower: str, cfg: UserConfig | None = None) -> str:
    for keywords, answer in build_qa_rules(cfg):
        if not answer:
            continue
        if any(kw in question_lower for kw in keywords):
            return answer
    return ""


def generate_answer(
    question: str,
    resume_text: str | None = None,
    cfg: UserConfig | None = None,
    user_id: str | None = None,
    company: str = "",
    job_title: str = "",
) -> str:
    """Full AI flow: keywords → cache → classify → resume → OpenAI → optimize → validate."""
    q = (question or "").strip()
    if not q:
        return validate_answer("")

    u = cfg or load_user_config(user_id)
    uid = user_id or os.getenv("SANKALPA_USERNAME") or os.getenv("SANKALPA_USER_ID")
    q_lower = q.lower()

    kw = keyword_answer(q_lower, u)
    if kw:
        return validate_answer(optimize_answer(q, kw, classify_question(q)))

    if config.AI_ENABLE_CACHE:
        cached = get_cache(q, uid)
        if cached:
            log_info("AI: cache hit", uid)
            return validate_answer(cached)

    q_type = classify_question(q)
    resume = (resume_text or read_resume(user_id=uid)).strip()
    resume_ctx = search_resume_context(q, resume)

    raw = ""
    if config.OPENAI_API_KEY:
        log_info(f"AI: generating answer ({q_type})", uid)
        raw = call_openai(q, resume_ctx, u)

    if not raw:
        raw = u.generic_reply or "Yes"

    optimized = optimize_answer(q, raw, q_type)
    final = validate_answer(optimized)

    if config.AI_ENABLE_CACHE and final:
        save_cache(q, final, uid)

    record_question_history(q, final, company=company, job_title=job_title, user_id=uid)
    return final


def get_answer(
    question: str,
    user_id: str | None = None,
    cfg: UserConfig | None = None,
) -> str:
    """Backward-compatible alias used by popup_handler."""
    return generate_answer(question=question, cfg=cfg, user_id=user_id)
