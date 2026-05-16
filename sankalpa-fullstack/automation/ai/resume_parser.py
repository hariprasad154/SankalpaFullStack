"""Extract text from uploaded resume PDF."""
import os

from core.storage import resume_path

_parsed_cache: dict[str, str] = {}


def read_resume(path: str | None = None, user_id: str | None = None) -> str:
    """Read resume PDF and return plain text (cached in memory per path)."""
    uid = user_id or os.getenv("SANKALPA_USER_ID", "default")
    uploads_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "uploads"))
    worker_env = os.path.join(uploads_root, str(uid), "worker_env.json")
    if os.path.isfile(worker_env):
        try:
            import json

            with open(worker_env, encoding="utf-8") as f:
                data = json.load(f)
            text = (data.get("resume_text") or "").strip()
            if text:
                return text
        except Exception:  # noqa: BLE001
            pass

    pdf_path = path or resume_path(user_id)
    if not os.path.isfile(pdf_path):
        return ""

    if pdf_path in _parsed_cache:
        return _parsed_cache[pdf_path]

    try:
        from pypdf import PdfReader
    except ImportError:
        try:
            from PyPDF2 import PdfReader  # type: ignore
        except ImportError:
            return ""

    try:
        reader = PdfReader(pdf_path)
        parts = []
        for page in reader.pages:
            text = page.extract_text() or ""
            if text.strip():
                parts.append(text)
        text = "\n".join(parts).strip()
    except Exception:  # noqa: BLE001
        text = ""

    _parsed_cache[pdf_path] = text
    return text
