"""Naukri login flow."""
import time

from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from core import config
from core.browser import start_driver
from core.logger import log_error, log_info
from naukri.selectors import (
    EMAIL_INPUT_XPATH,
    LOGIN_BTN_CLASS,
    LOGIN_BTN_XPATHS,
    PASSWORD_INPUT_XPATH,
    SUBMIT_BTN_XPATH,
)


def credentials_ok() -> bool:
    from models.user_config import load_user_config

    cfg = load_user_config()
    email = (cfg.email or "").strip()
    password = (cfg.password or "").strip()
    if not email or not password:
        return False
    if email.lower() in ("your_email", "you@example.com"):
        return False
    return True


def login_naukri(driver) -> None:
    wait = WebDriverWait(driver, config.NAUKRI_LOGIN_WAIT)
    driver.get(config.NAUKRI_URL)
    time.sleep(2)

    login_btn = None
    attempts = [
        (By.CLASS_NAME, LOGIN_BTN_CLASS),
        (By.PARTIAL_LINK_TEXT, "Login"),
    ]
    for xp in LOGIN_BTN_XPATHS:
        attempts.append((By.XPATH, xp))
    for by, value in attempts:
        try:
            login_btn = wait.until(EC.element_to_be_clickable((by, value)))
            break
        except Exception:  # noqa: BLE001
            continue

    if login_btn is None:
        raise RuntimeError("Naukri: could not find login entry (update naukri/selectors.py).")

    login_btn.click()
    time.sleep(1)

    from models.user_config import load_user_config

    cfg = load_user_config()
    email_input = wait.until(EC.presence_of_element_located((By.XPATH, EMAIL_INPUT_XPATH)))
    email_input.clear()
    email_input.send_keys(cfg.email)

    password_input = wait.until(EC.presence_of_element_located((By.XPATH, PASSWORD_INPUT_XPATH)))
    password_input.clear()
    password_input.send_keys(cfg.password)

    submit_btn = wait.until(EC.element_to_be_clickable((By.XPATH, SUBMIT_BTN_XPATH)))
    submit_btn.click()
    time.sleep(5)
    log_info("Naukri: login success")
    try:
        from sheets_client import patch_runtime

        patch_runtime(last_log="Naukri login success")
    except Exception:  # noqa: BLE001
        pass


def run_naukri_login() -> None:
    if not credentials_ok():
        print(
            "Naukri credentials missing. Register/login in the app and click Start Apply "
            "(loads config from Google Sheet / worker_env.json)."
        )
        return

    driver = None
    try:
        log_info("Naukri: starting Chrome session")
        driver = start_driver()
        login_naukri(driver)
        print("Logged into Naukri (check browser).")
        log_info("Naukri: login flow finished (session open for inspection)")
        time.sleep(config.NAUKRI_HOLD_SECONDS)
    except Exception as exc:  # noqa: BLE001
        print(f"Naukri automation error: {exc}")
        log_error(f"Naukri error: {exc!s}")
        raise
    finally:
        if driver is not None:
            driver.quit()
        log_info("Naukri: browser closed")
