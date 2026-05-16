from pydantic import BaseModel, EmailStr


class UserConfigRequest(BaseModel):
    naukri_email: str = ""
    naukri_password: str = ""
    current_ctc: str = ""
    expected_ctc: str = ""
    notice_period: str = ""
    apply_years: str = "3"
    lwd_reply: str = ""
    skills: str = ""
    skills_reply: str = ""
    preferred_locations: str = ""
    generic_reply: str = "Yes"


class UserConfigResponse(BaseModel):
    naukri_email: str = ""
    current_ctc: str = ""
    expected_ctc: str = ""
    notice_period: str = ""
    apply_years: str = ""
    lwd_reply: str = ""
    skills: str = ""
    skills_reply: str = ""
    preferred_locations: str = ""
    generic_reply: str = ""
    has_resume: bool = False


class AutomationSettingsRequest(BaseModel):
    auto_apply_enabled: bool = False
    schedule_times: str = "09:00,14:00,19:00"
    max_applies_per_day: int = 100
