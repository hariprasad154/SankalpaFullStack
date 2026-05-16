from datetime import datetime

from pydantic import BaseModel


class DashboardStats(BaseModel):
    applied_today: int
    applied_week: int
    applied_month: int
    success_count: int
    failed_count: int
    total: int


class ApplicationItem(BaseModel):
    id: int
    company: str
    role: str
    status: str
    applied_at: datetime | None
    ai_used: bool
    failure_reason: str


class LogItem(BaseModel):
    time: str
    timestamp: str | None = None
    level: str
    message: str
