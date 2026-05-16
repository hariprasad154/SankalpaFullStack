"""JSON file storage under sankalpa-fullstack/data/ (and per-user paths)."""
import json
import os

from core.config import DATA_DIR, UPLOADS_DIR


def data_dir_for_user(user_id: str | None = None) -> str:
    if not user_id or user_id in ("default", ""):
        return DATA_DIR
    return os.path.join(UPLOADS_DIR, user_id, "data")


def _path(name: str, user_id: str | None = None) -> str:
    base = data_dir_for_user(user_id)
    os.makedirs(base, exist_ok=True)
    return os.path.join(base, name)


def read_json(name: str, user_id: str | None = None):
    path = _path(name, user_id)
    init = "[]" if name.endswith((".json",)) and name in (
        "jobs.json",
        "logs.json",
        "missed_questions.json",
        "question_history.json",
    ) else "{}"
    if name == "cache.json":
        init = "{}"
    if not os.path.exists(path):
        with open(path, "w", encoding="utf-8") as f:
            f.write(init)
        return json.loads(init)
    with open(path, encoding="utf-8") as f:
        raw = f.read()
    if not raw.strip():
        with open(path, "w", encoding="utf-8") as f:
            f.write(init)
        return json.loads(init)
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        with open(path, "w", encoding="utf-8") as f:
            f.write(init)
        return json.loads(init)


def write_json(name: str, data, user_id: str | None = None) -> None:
    path = _path(name, user_id)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def resume_path(user_id: str | None = None) -> str:
    uid = user_id or "default"
    folder = os.path.join(UPLOADS_DIR, uid)
    os.makedirs(folder, exist_ok=True)
    return os.path.join(folder, "resume.pdf")
