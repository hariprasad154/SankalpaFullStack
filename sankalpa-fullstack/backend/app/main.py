"""Sankalpa API — Google Sheets + live runtime state."""
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import CORS_ORIGINS, GOOGLE_SCRIPT_URL
from app.routes_auth import router as auth_router
from app.routes_automation import router as automation_router
from app.routes_dashboard import router as dashboard_router
from app.routes_internal import router as internal_router
from app.routes_user import router as user_router
from app.services import runtime_state


@asynccontextmanager
async def lifespan(_app: FastAPI):
    runtime_state.recover_stale_runtime()
    yield


app = FastAPI(title="Sankalpa API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(user_router)
app.include_router(automation_router)
app.include_router(dashboard_router)
app.include_router(internal_router)


@app.get("/health")
def health():
    return {
        "status": "ok",
        "storage": "google_sheets" if GOOGLE_SCRIPT_URL else "local_memory_dev",
        "google_script_configured": bool(GOOGLE_SCRIPT_URL),
    }
