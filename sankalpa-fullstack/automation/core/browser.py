"""Chrome WebDriver setup for Naukri automation."""
import os

from core.config import NAUKRI_LOGIN_WAIT


def default_wait_seconds() -> int:
    return NAUKRI_LOGIN_WAIT


def start_driver(headless: bool = False):
    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.chrome.service import Service
    from webdriver_manager.chrome import ChromeDriverManager

    options = Options()
    options.add_argument("--start-maximized")
    if headless or os.getenv("NAUKRI_HEADLESS", "").strip().lower() in ("1", "true", "yes"):
        options.add_argument("--headless=new")
        options.add_argument("--disable-gpu")
        options.add_argument("--no-sandbox")

    return webdriver.Chrome(
        service=Service(ChromeDriverManager().install()),
        options=options,
    )
