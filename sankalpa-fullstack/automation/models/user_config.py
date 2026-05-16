"""Per-user Naukri / screening configuration."""
import json
import os
from dataclasses import asdict, dataclass, field

from core import config
from core.storage import UPLOADS_DIR, read_json, write_json


@dataclass
class UserConfig:
    email: str = ""
    password: str = ""
    expected_salary: str = ""
    current_salary: str = ""
    notice_period: str = ""
    apply_years: str = ""
    lwd_reply: str = ""
    skills_reply: str = ""
    generic_reply: str = ""
    skills: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "UserConfig":
        skills = data.get("skills")
        if isinstance(skills, str):
            skills = [s.strip() for s in skills.split(",") if s.strip()]
        if not isinstance(skills, list):
            skills = []
        return cls(
            email=str(data.get("email", "")),
            password=str(data.get("password", "")),
            expected_salary=str(data.get("expected_salary", "")),
            current_salary=str(data.get("current_salary", "")),
            notice_period=str(data.get("notice_period", "")),
            apply_years=str(data.get("apply_years", "")),
            lwd_reply=str(data.get("lwd_reply", "")),
            skills_reply=str(data.get("skills_reply", "")),
            generic_reply=str(data.get("generic_reply", "")),
            skills=skills,
        )


def _config_path(user_id: str) -> str:
    folder = os.path.join(UPLOADS_DIR, user_id or "default")
    os.makedirs(folder, exist_ok=True)
    return os.path.join(folder, "config.json")


def _worker_env_path(uid: str) -> str:
    return os.path.join(UPLOADS_DIR, uid, "worker_env.json")


def load_user_config(user_id: str | None = None) -> UserConfig:
    uid = user_id or os.getenv("SANKALPA_USERNAME") or os.getenv("SANKALPA_USER_ID") or config.DEFAULT_USER_ID
    worker_path = _worker_env_path(str(uid))
    if os.path.isfile(worker_path):
        with open(worker_path, encoding="utf-8") as f:
            data = json.load(f)
        return UserConfig.from_dict(
            {
                "email": data.get("naukri_email", ""),
                "password": data.get("naukri_password", ""),
                "expected_salary": data.get("expected_salary", ""),
                "current_salary": data.get("current_salary", ""),
                "notice_period": data.get("notice_period", ""),
                "apply_years": data.get("apply_years", "3"),
                "lwd_reply": data.get("lwd_reply", ""),
                "skills_reply": data.get("skills_reply", ""),
                "generic_reply": data.get("generic_reply", "Yes"),
            }
        )
    path = _config_path(uid)
    if os.path.isfile(path):
        with open(path, encoding="utf-8") as f:
            return UserConfig.from_dict(json.load(f))

    stored = read_json("profile.json", uid if uid != "default" else None)
    if isinstance(stored, dict) and stored.get("email"):
        return UserConfig.from_dict(stored)

    # No .env fallback for credentials — user must register and use Google Sheets / worker_env
    return UserConfig(
        email="",
        password="",
        expected_salary="",
        current_salary="",
        notice_period="15 days",
        apply_years="3",
        lwd_reply="15 days",
        skills_reply="",
        generic_reply="Yes",
        skills=[],
    )


def save_user_config(cfg: UserConfig, user_id: str | None = None) -> None:
    uid = user_id or config.DEFAULT_USER_ID
    path = _config_path(uid)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(cfg.to_dict(), f, indent=2)
    write_json("profile.json", cfg.to_dict(), uid if uid != "default" else None)
