"""Environment-backed configuration for Naukri automation."""
import os

from pathlib import Path

from dotenv import load_dotenv

_REPO_ROOT = Path(__file__).resolve().parents[2]  # sankalpBackEnd/
load_dotenv(_REPO_ROOT / ".env")
load_dotenv(_REPO_ROOT / "backend" / ".env")
load_dotenv(_REPO_ROOT / "automation" / ".env")

# Paths
AUTOMATION_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.abspath(os.path.join(AUTOMATION_DIR, "..", "data"))
UPLOADS_DIR = os.path.abspath(os.path.join(AUTOMATION_DIR, "uploads"))

# Naukri URLs
NAUKRI_URL = os.getenv("NAUKRI_URL", "https://www.naukri.com")
NAUKRI_HOME_URL = os.getenv("NAUKRI_HOME_URL", "https://www.naukri.com/mnjuser/homepage")
RECOMMENDED_URL = os.getenv(
    "NAUKRI_RECOMMENDED_URL",
    "https://www.naukri.com/mnjuser/recommendedjobs",
)

# Credentials
NAUKRI_EMAIL = os.getenv("NAUKRI_EMAIL", "")
NAUKRI_PASSWORD = os.getenv("NAUKRI_PASSWORD", "")
NAUKRI_HOLD_SECONDS = int(os.getenv("NAUKRI_HOLD_SECONDS", "60"))
NAUKRI_LOGIN_WAIT = int(os.getenv("NAUKRI_LOGIN_WAIT", "20"))

# Batch apply
BATCH_SIZE = int(os.getenv("BATCH_APPLY_SIZE", os.getenv("MAX_BATCH_SIZE", "5")))
PAGE_READY_TIMEOUT = int(os.getenv("NAUKRI_BATCH_PAGE_TIMEOUT", "30"))
APPLY_BTN_WAIT = int(os.getenv("NAUKRI_APPLY_BUTTON_WAIT", "35"))
MAX_APPLY_JOBS = int(os.getenv("NAUKRI_MAX_APPLY_JOBS", os.getenv("MAX_APPLY_PER_DAY", "0")))

# Screening answers
APPLY_YEARS = os.getenv("NAUKRI_APPLY_YEARS", "3")
EXPECTED_SALARY = os.getenv("NAUKRI_EXPECTED_SALARY", "1400000")
CURRENT_SALARY = os.getenv("NAUKRI_CURRENT_SALARY", "807000")
NOTICE = os.getenv("NAUKRI_NOTICE", "15 days")
LWD_REPLY = os.getenv("NAUKRI_LWD_REPLY", "15 days")
SKILLS_REPLY = os.getenv("NAUKRI_SKILLS_REPLY", "Java, Spring Boot, Microservices")
GENERIC_POPUP_REPLY = os.getenv("NAUKRI_GENERIC_POPUP_REPLY", "Yes")
FALLBACK_REPLIES = os.getenv("NAUKRI_FALLBACK_REPLIES", "Yes,0,N/A")
RADIO_DEFAULT_ORDER = os.getenv("NAUKRI_RADIO_DEFAULT_ORDER", "Yes,YES,yes,y,Y")

MODAL_MAX_ROUNDS = int(os.getenv("NAUKRI_MODAL_MAX_ROUNDS", "6"))
MODAL_MAX_SECONDS = float(os.getenv("NAUKRI_MODAL_MAX_SECONDS", "45"))
SAVE_NUDGE_ATTEMPTS = int(os.getenv("NAUKRI_SAVE_NUDGE_ATTEMPTS", "10"))
MAX_BATCHES_PER_TAB = int(os.getenv("NAUKRI_MAX_BATCHES_PER_TAB", "60"))
EMPTY_PICK_TAB_ROUNDS = int(os.getenv("NAUKRI_EMPTY_PICK_TAB_ROUNDS", "3"))
RANDOM_UNKNOWN_CHECKBOX = (os.getenv("NAUKRI_RANDOM_UNKNOWN_CHECKBOX", "1") or "1").strip().lower()

POPUP_EMAIL = (os.getenv("NAUKRI_POPUP_EMAIL", "") or NAUKRI_EMAIL).strip()
POPUP_PHONE = os.getenv("NAUKRI_POPUP_PHONE", "").strip()
POPUP_DATE_DDMM = os.getenv("NAUKRI_POPUP_DATE_DDMM", "").strip()

DEFAULT_FEED_TABS = "Applies,Profile,Top Candidate,Preferences,You might like"
_tabs_csv = (os.getenv("NAUKRI_BATCH_TABS") or os.getenv("NAUKRI_FLOW_TABS") or DEFAULT_FEED_TABS).strip()
BATCH_TABS = [t.strip() for t in _tabs_csv.split(",") if t.strip()]

CHECKBOX_CSS = os.getenv(
    "NAUKRI_CHECKBOX_CSS",
    "i.naukicon-ot-checkbox,i[class*='naukicon-ot-checkbox'],i[class*='ot-checkbox']",
)

DEDUPE_MIN_CHARS = int(os.getenv("NAUKRI_DEDUPE_MIN_CHARS", "30"))
DESC_MAX_STORE = int(os.getenv("NAUKRI_JOB_DESC_MAX_CHARS", "2500"))
TOGGLE_CARD_HINT_MIN = int(os.getenv("NAUKRI_TOGGLE_CARD_MIN_CHARS", "45"))
DEDUPE_SCOPE = (os.getenv("NAUKRI_DEDUPE_SCOPE", "per_tab") or "per_tab").strip().lower()
APPLY_CLICK_FAIL_TAB_BREAK = int(os.getenv("NAUKRI_APPLY_CLICK_FAIL_TAB_BREAK", "2"))
MODAL_FAIL_TAB_BREAK = int(os.getenv("NAUKRI_MODAL_FAIL_TAB_BREAK", "2"))

# AI
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "").strip()
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4.1-mini")
AI_ENABLE_CACHE = os.getenv("AI_ENABLE_CACHE", "1").strip() in ("1", "true", "yes")
AI_ENABLE_OPTIMIZER = os.getenv("AI_ENABLE_OPTIMIZER", "1").strip() in ("1", "true", "yes")
AI_ENABLE_RESUME_CONTEXT = os.getenv("AI_ENABLE_RESUME_CONTEXT", "1").strip() in ("1", "true", "yes")

# Apply limits
MAX_APPLY_PER_RUN = int(os.getenv("MAX_APPLY_PER_RUN", os.getenv("MAX_APPLY_PER_DAY", "50")))
MAX_APPLY_JOBS = int(os.getenv("NAUKRI_MAX_APPLY_JOBS", str(MAX_APPLY_PER_RUN)))

DEFAULT_USER_ID = os.getenv("SANKALPA_USER_ID", "default")
HEADLESS_MODE = os.getenv("HEADLESS_MODE", os.getenv("HEADLESS", "0")).strip() in ("1", "true", "yes")

# Ingest
INTERVAL_SECONDS = int(os.getenv("INTERVAL_SECONDS", "30"))
KEYWORDS = os.getenv("KEYWORDS", "")
AUTOMATION_MODE = os.getenv("AUTOMATION_MODE", "ingest").strip().lower()
