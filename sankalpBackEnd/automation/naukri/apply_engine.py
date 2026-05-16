"""Naukri batch apply engine."""
import os
import random
import time
import uuid
from datetime import datetime

from selenium.common.exceptions import StaleElementReferenceException, TimeoutException
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from core import config
from core.logger import log_info
from core.storage import read_json, write_json
from naukri.popup_handler import handle_apply_modal

_USER_ID = config.DEFAULT_USER_ID


config.RECOMMENDED_URL = os.getenv(
    "NAUKRIconfig.RECOMMENDED_URL",
    "https://www.naukri.com/mnjuser/recommendedjobs",
)
config.BATCH_SIZE = int(os.getenv("BATCH_APPLY_SIZE", "5"))
config.PAGE_READY_TIMEOUT = int(os.getenv("NAUKRI_BATCH_PAGE_TIMEOUT", "30"))
config.APPLY_BTN_WAIT = int(os.getenv("NAUKRI_APPLY_BUTTON_WAIT", "35"))
_cap = os.getenv("NAUKRI_MAX_APPLY_JOBS") or os.getenv("MAX_APPLY_PER_RUN", "50")
config.MAX_APPLY_JOBS = int(_cap) if _cap else 50

config.APPLY_YEARS = os.getenv("NAUKRI_APPLY_YEARS", "3")
config.EXPECTED_SALARY = os.getenv("NAUKRI_EXPECTED_SALARY", "1400000")
config.CURRENT_SALARY = os.getenv("NAUKRI_CURRENT_SALARY", "807000")
config.NOTICE = os.getenv("NAUKRI_NOTICE", "15 days")
config.LWD_REPLY = os.getenv("NAUKRI_LWD_REPLY", "15 days")
config.SKILLS_REPLY = os.getenv("NAUKRI_SKILLS_REPLY", "Java, Spring Boot, Microservices")
config.GENERIC_POPUP_REPLY = os.getenv("NAUKRI_GENERIC_POPUP_REPLY", "Yes")
config.FALLBACK_REPLIES = os.getenv("NAUKRI_FALLBACK_REPLIES", "Yes,0,N/A")
config.RADIO_DEFAULT_ORDER = os.getenv(
    "NAUKRI_RADIO_DEFAULT_ORDER",
    "Yes,YES,yes,y,Y",
)
config.MODAL_MAX_ROUNDS = int(os.getenv("NAUKRIconfig.MODAL_MAX_ROUNDS", "6"))
config.MODAL_MAX_SECONDS = float(os.getenv("NAUKRIconfig.MODAL_MAX_SECONDS", "45"))
config.SAVE_NUDGE_ATTEMPTS = int(os.getenv("NAUKRIconfig.SAVE_NUDGE_ATTEMPTS", "10"))
config.MAX_BATCHES_PER_TAB = int(os.getenv("NAUKRIconfig.MAX_BATCHES_PER_TAB", "60"))
config.EMPTY_PICK_TAB_ROUNDS = int(os.getenv("NAUKRIconfig.EMPTY_PICK_TAB_ROUNDS", "3"))
# When Qa has no match: pick one random modal checkbox (2+ visible) and log to missed_questions.json — set 0 to disable
config.RANDOM_UNKNOWN_CHECKBOX = (os.getenv("NAUKRI_RANDOM_UNKNOWN_CHECKBOX", "1") or "1").strip().lower()

config.POPUP_EMAIL = (os.getenv("NAUKRI_POPUP_EMAIL", "") or os.getenv("NAUKRI_EMAIL", "")).strip()
config.POPUP_PHONE = os.getenv("NAUKRI_POPUP_PHONE", "").strip()
config.POPUP_DATE_DDMM = os.getenv("NAUKRI_POPUP_DATE_DDMM", "").strip()

_DEFAULT_FEED_TABS = "Applies,Profile,Top Candidate,Preferences,You might like"
# Batch apply reads NAUKRIconfig.BATCH_TABS; if empty, use NAUKRI_FLOW_TABS (same list many users set once).
_tabs_csv = (os.getenv("NAUKRIconfig.BATCH_TABS") or os.getenv("NAUKRI_FLOW_TABS") or _DEFAULT_FEED_TABS).strip()
config.BATCH_TABS = [t.strip() for t in _tabs_csv.split(",") if t.strip()]

config.CHECKBOX_CSS = os.getenv(
    "NAUKRIconfig.CHECKBOX_CSS",
    "i.naukicon-ot-checkbox,i[class*='naukicon-ot-checkbox'],i[class*='ot-checkbox']",
)


def _read_jobs():
    from core.storage import read_json

    data = read_json("jobs.json")
    return data if isinstance(data, list) else []


def _write_jobs(data) -> None:
    from core.storage import write_json

    write_json("jobs.json", data)


def _append_missed_question(question_excerpt: str, reason: str) -> None:
    """Append screening question blob when we use a random checkbox (no Qa.txt match)."""
    from core.storage import read_json, write_json

    data = read_json("missed_questions.json")
    if not isinstance(data, list):
        data = []
    data.append(
        {
            "time": datetime.now().isoformat(timespec="seconds"),
            "reason": reason,
            "question_excerpt": (question_excerpt or "")[:2400],
        }
    )
    write_json("missed_questions.json", data)


config.DEDUPE_MIN_CHARS = int(os.getenv("NAUKRIconfig.DEDUPE_MIN_CHARS", "30"))
config.DESC_MAX_STORE = int(os.getenv("NAUKRI_JOB_DESC_MAX_CHARS", "2500"))
# Loose checkbox scan: keep only rows inside job tuples or with at least this much card text (avoids nav filters beating the iframe list).
config.TOGGLE_CARD_HINT_MIN = int(os.getenv("NAUKRI_TOGGLE_CARD_MIN_CHARS", "45"))
# per_tab = dedupe only against jobs.json rows with the same source tab. global = any tab. off = do not skip from file.
config.DEDUPE_SCOPE = (os.getenv("NAUKRI_DEDUPE_SCOPE", "per_tab") or "per_tab").strip().lower()
config.APPLY_CLICK_FAIL_TAB_BREAK = int(os.getenv("NAUKRI_APPLY_CLICK_FAIL_TAB_BREAK", "2"))
config.MODAL_FAIL_TAB_BREAK = int(os.getenv("NAUKRI_MODAL_FAIL_TAB_BREAK", "2"))


def _normalize_job_dedupe_text(s: str) -> str:
    if not s or not isinstance(s, str):
        return ""
    return " ".join(s.split()).strip().lower()


def _job_texts_overlap(a: str, b: str) -> bool:
    """True if either normalized string contains the other (substring dedupe)."""
    x = _normalize_job_dedupe_text(a)
    y = _normalize_job_dedupe_text(b)
    if len(x) < config.DEDUPE_MIN_CHARS or len(y) < config.DEDUPE_MIN_CHARS:
        return False
    if x in y or y in x:
        return True
    n = min(90, len(x), len(y))
    return n >= 40 and x[:n] == y[:n]


def _job_description_recorded(jobs_data, description: str, tab_label: str | None = None) -> bool:
    """Skip apply if jobs.json already has this job (substring / overlap), scoped by NAUKRI_DEDUPE_SCOPE."""
    if config.DEDUPE_SCOPE == "off":
        return False
    cand = _normalize_job_dedupe_text(description)
    if len(cand) < config.DEDUPE_MIN_CHARS:
        return False
    head = cand[:200]
    tab_norm = (tab_label or "").strip().lower()
    for row in jobs_data:
        if not isinstance(row, dict):
            continue
        if config.DEDUPE_SCOPE == "per_tab" and tab_norm:
            src = (row.get("source") or "").strip().lower()
            if src and src != tab_norm:
                continue
        stored = row.get("description") or row.get("job_description") or ""
        if not isinstance(stored, str):
            continue
        s = _normalize_job_dedupe_text(stored)
        if len(s) < config.DEDUPE_MIN_CHARS:
            continue
        if head in s or s in cand or cand in s:
            return True
        if _job_texts_overlap(cand, s):
            return True
    return False


def _extract_job_card_text(driver, toggle_el) -> str:
    """Walk up from the toggle to a parent with enough innerText (job card / tuple)."""
    try:
        raw = driver.execute_script(
            """
            var el = arguments[0];
            if (!el) return '';
            var p = el;
            for (var i = 0; i < 16 && p; i++) {
              var t = (p.innerText || '').replace(/\\s+/g, ' ').trim();
              if (t.length > 100) return t.slice(0, 4000);
              p = p.parentElement;
            }
            return (el.innerText || '').replace(/\\s+/g, ' ').trim().slice(0, 4000);
            """,
            toggle_el,
        )
        return (raw or "").strip()
    except Exception:  # noqa: BLE001
        return ""


def _role_line_from_description(desc: str, tab_label: str, index_hint: int) -> str:
    if not desc:
        return f"Job_{tab_label}_{index_hint}"
    for line in desc.replace("\r", "").split("\n"):
        t = line.strip()
        if len(t) > 3:
            return t[:200]
    return f"Job_{tab_label}_{index_hint}"


def _company_from_description(desc: str) -> str:
    if not desc:
        return "Naukri"
    lines = [ln.strip() for ln in desc.replace("\r", "").split("\n") if ln.strip()]
    if len(lines) >= 2:
        return lines[1][:255]
    if lines:
        return lines[0][:255]
    return "Naukri"


def log_info(msg: str) -> None:
    from core.logger import log_info as log

    log(msg)


def _toggle_in_recommended_job_row(driver, el) -> bool:
    """True if control sits under Naukri job / tuple / similar-job card markup."""
    try:
        return bool(
            driver.execute_script(
                """
                var n = arguments[0];
                if (!n) return false;
                for (var i = 0; i < 26 && n; n = n.parentElement, i++) {
                  var c = (n.getAttribute && n.getAttribute('class')) || '';
                  var id = n.id || '';
                  var s = ' ' + c + ' ' + id + ' ';
                  if (/JobTuple|job-tuple|jobTuple|cust-tuple|srp-jobtuple|jobCard|jobcard|similarJob|recoJob|tupleWrap|similar|mnjJob|jobFound/i.test(s))
                    return true;
                }
                return false;
                """,
                el,
            )
        )
    except Exception:  # noqa: BLE001
        return False


def _find_job_toggles_loose(driver):
    """Every visible checkbox input + configured Naukri OT checkbox icons."""
    seen = []
    out = []

    def _append(el):
        try:
            eid = getattr(el, "id", None) or str(id(el))
        except Exception:  # noqa: BLE001
            eid = str(id(el))
        for u in seen:
            if u == eid:
                return
        seen.append(eid)
        out.append(el)

    for el in driver.find_elements(By.XPATH, "//input[@type='checkbox']"):
        _append(el)

    for part in config.CHECKBOX_CSS.split(","):
        sel = part.strip()
        if not sel:
            continue
        for el in driver.find_elements(By.CSS_SELECTOR, sel):
            _append(el)

    return out


def _find_job_toggles_scoped_first(driver):
    """Toggles that live inside known job-list tuple containers (all feeds including Top Candidate)."""
    out = []
    seen_ids = []
    for xp in (
        "//div[contains(@class,'jobTuple')]//*[self::input[@type='checkbox'] | self::i[contains(@class,'naukicon-ot-checkbox')] | self::i[contains(@class,'ot-checkbox')]]",
        "//div[contains(@class,'cust-tuple')]//*[self::input[@type='checkbox'] | self::i[contains(@class,'naukicon-ot-checkbox')]]",
        "//*[contains(@class,'srp-jobtuple')]//input[@type='checkbox']",
        "//*[contains(translate(@class,'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'jobtuple')]//input[@type='checkbox']",
    ):
        try:
            for el in driver.find_elements(By.XPATH, xp):
                try:
                    if not el.is_displayed():
                        continue
                    cid = el.id
                    dup = False
                    for u in seen_ids:
                        if u == cid:
                            dup = True
                            break
                    if dup:
                        continue
                    seen_ids.append(cid)
                    out.append(el)
                except Exception:  # noqa: BLE001
                    continue
        except Exception:  # noqa: BLE001
            continue
    return out


def _find_job_toggles(driver):
    """
    Prefer tuple-scoped controls; else filter loose controls by job-row ancestry or rich card text.
    Stops the job-list iframe (few real rows) from losing to dozens of unrelated page checkboxes.
    """
    scoped = _find_job_toggles_scoped_first(driver)
    if len(scoped) > 0:
        return scoped

    loose = _find_job_toggles_loose(driver)
    filtered = []
    for el in loose:
        try:
            if not el.is_displayed():
                continue
            if _toggle_in_recommended_job_row(driver, el):
                filtered.append(el)
        except Exception:  # noqa: BLE001
            continue
    if len(filtered) > 0:
        return filtered

    hinted = []
    for el in loose:
        try:
            if not el.is_displayed():
                continue
            t = _extract_job_card_text(driver, el)
            if len(t) >= config.TOGGLE_CARD_HINT_MIN:
                hinted.append(el)
        except Exception:  # noqa: BLE001
            continue
    if len(hinted) > 0:
        return hinted

    return loose


def _nudge_recommended_jobs_visible(driver) -> None:
    """Lazy-loaded feeds: scroll inner list shells + window so job tuples attach."""
    try:
        driver.execute_script(
            """
            window.scrollTo(0, 0);
            var sel = '[class*="jobTuple"],[class*="cust-tuple"],[class*="listContainer"],[class*="recoJob"]';
            var nodes = document.querySelectorAll(sel);
            for (var i = 0; i < nodes.length && i < 10; i++) {
              try {
                var n = nodes[i];
                n.scrollTop = 0;
                n.scrollTop = Math.min(600, (n.scrollHeight || 0));
              } catch (e) {}
            }
            window.scrollBy(0, 320);
            """
        )
    except Exception:  # noqa: BLE001
        pass


def _try_click_job_toggle(driver, el) -> bool:
    """JS + Actions + native click — Naukri icons sometimes ignore a single strategy."""
    for action in (
        lambda: driver.execute_script("arguments[0].click();", el),
        lambda: ActionChains(driver).move_to_element(el).pause(0.08).click().perform(),
        lambda: el.click(),
    ):
        try:
            driver.execute_script("arguments[0].scrollIntoView({block:'center'});", el)
            time.sleep(0.08)
            action()
            time.sleep(0.12)
            return True
        except Exception:  # noqa: BLE001
            continue
    return False


def _count_toggles(driver) -> int:
    return len(_find_job_toggles(driver))


def _ensure_job_list_context(driver) -> int:
    driver.switch_to.default_content()
    best_n = _count_toggles(driver)
    best_frame = None

    for fr in driver.find_elements(By.TAG_NAME, "iframe"):
        try:
            driver.switch_to.default_content()
            driver.switch_to.frame(fr)
            n = _count_toggles(driver)
            if n > best_n:
                best_n = n
                best_frame = fr
        except Exception:  # noqa: BLE001
            pass
        finally:
            driver.switch_to.default_content()

    if best_frame is not None and best_n > 0:
        driver.switch_to.default_content()
        driver.switch_to.frame(best_frame)

    return best_n


def _wait_for_apply_or_jobs(driver) -> None:
    wait = WebDriverWait(driver, config.PAGE_READY_TIMEOUT)
    driver.switch_to.default_content()
    wait.until(
        EC.presence_of_element_located(
            (
                By.XPATH,
                "//button[contains(.,'Apply')]"
                "|//*[contains(.,'Recommended')]"
                "|//*[contains(.,'recommended')]",
            ),
        ),
    )


def _scroll_until_toggles(driver, max_rounds: int = 12) -> int:
    for _ in range(max_rounds):
        n = _count_toggles(driver)
        if n > 0:
            return n
        driver.execute_script("window.scrollBy(0, 420);")
        time.sleep(0.4)
    return _count_toggles(driver)


def prepare_recommended_page(driver) -> int:
    driver.switch_to.default_content()
    _wait_for_apply_or_jobs(driver)
    time.sleep(1.0)

    n = _ensure_job_list_context(driver)
    if n == 0:
        n = _scroll_until_toggles(driver)
    if n == 0:
        driver.switch_to.default_content()
        _ensure_job_list_context(driver)
        n = _scroll_until_toggles(driver)

    return n


def _feed_tab_keyword(tab_label: str) -> str:
    """'Profile (72)' → 'Profile' for safer tab matching."""
    s = (tab_label or "").strip()
    if "(" in s:
        s = s.split("(")[0].strip()
    return s.replace("'", "")


def _naukri_tab_wrapper_ids(key: str):
    """
    Naukri recommended jobs strip uses div.tab-wrapper[@id] + div.tab-list-item (not <a>).
    Return possible @id values for this tab label.
    """
    low = (key or "").strip().lower()
    out = []
    if low.startswith("applies"):
        out.extend(["apply", "applies", "applied"])
    elif low.startswith("profile"):
        out.append("profile")
    elif "top" in low and "candidate" in low:
        out.extend(
            [
                "top_candidate",
                "topCandidate",
                "top-candidate",
                "topCandidates",
                "topcandidates",
                "tc",
            ]
        )
    elif low.startswith("preferences"):
        out.extend(
            [
                "preferences",
                "preference",
                "prefs",
                "jobPreferences",
                "jobpreferences",
            ]
        )
    elif "you might" in low or "might like" in low:
        out.extend(
            [
                "you_might_like",
                "youMightLike",
                "might_like",
                "recommendations",
                "ymyl",
                "similarJobs",
                "similarjobs",
            ]
        )
    return out


def _tab_key_words(tab_key: str) -> list:
    parts = []
    for w in (tab_key or "").lower().split():
        wl = w.strip(".,;:!?()")
        if len(wl) >= 2:
            parts.append(wl)
    return parts


def _blob_matches_tab_key(blob: str, tab_key: str) -> bool:
    """Active strip text must contain every significant token (e.g. top + candidate)."""
    b = (blob or "").lower()
    words = _tab_key_words(tab_key)
    if not words:
        return (tab_key or "").lower().strip() in b
    for w in words:
        if w not in b:
            return False
    return True


def _active_feed_tab_blob(driver) -> str:
    """Read labels Naukri marks as selected on the recommended feed tab strip."""
    driver.switch_to.default_content()
    try:
        blob = driver.execute_script(
            """
            var parts = [];
            function pushT(n) {
              if (!n) return;
              var t = (n.innerText || n.textContent || '').replace(/\\s+/g, ' ').trim();
              if (t && t.length < 96) parts.push(t);
            }
            document.querySelectorAll('[class*="tab-list-item"]').forEach(function(n){
              var c = (n.getAttribute('class') || '') + '';
              var ar = (n.getAttribute('aria-selected') || '').toLowerCase();
              if (ar === 'true' || /\\bactive\\b|\\bselected\\b|\\bcurrent\\b/i.test(c)) pushT(n);
            });
            document.querySelectorAll('[role="tab"]').forEach(function(n){
              if ((n.getAttribute('aria-selected') || '').toLowerCase() === 'true') pushT(n);
            });
            return parts.join(' | ').toLowerCase().slice(0, 500);
            """
        )
        return (blob or "").strip().lower()
    except Exception:  # noqa: BLE001
        return ""


def _is_inside_recommended_tab_strip(driver, el) -> bool:
    try:
        return bool(
            driver.execute_script(
                """
                var n = arguments[0];
                for (var i = 0; i < 24 && n; i++) {
                  var id = (n.id || '') + '';
                  var cls = (n.getAttribute('class') || '') + '';
                  var s = id + ' ' + cls;
                  if (/tab-wrapper|tabs-container|tab-list|recommendedJob|recJob|jobTuple|mnjuser/i.test(s))
                    return true;
                  n = n.parentElement;
                }
                return false;
                """,
                el,
            )
        )
    except Exception:  # noqa: BLE001
        return False


def _element_text_matches_tab_key(txt: str, tab_key: str) -> bool:
    low = (txt or "").strip().lower()
    k = (tab_key or "").strip().lower()
    if not k or k not in low:
        return False
    return _blob_matches_tab_key(low, tab_key)


def _snap_tab_strip_scroll(driver, el) -> None:
    try:
        driver.execute_script(
            """
            var el = arguments[0];
            el.scrollIntoView({inline: 'center', block: 'nearest'});
            var p = el.parentElement;
            for (var i = 0; i < 18 && p; i++) {
              if (p.scrollWidth > p.clientWidth + 6) {
                var r = el.getBoundingClientRect();
                var pr = p.getBoundingClientRect();
                p.scrollLeft += (r.left + r.width / 2) - (pr.left + pr.width / 2);
                break;
              }
              p = p.parentElement;
            }
            """,
            el,
        )
    except Exception:  # noqa: BLE001
        try:
            driver.execute_script(
                "arguments[0].scrollIntoView({block:'center', inline:'center'});",
                el,
            )
        except Exception:  # noqa: BLE001
            pass


def _collect_feed_tab_candidates(driver, tab_key: str) -> list:
    """
    Prefer tab-list-item / role=tab inside the recommended strip (not shortest random link).
    Longer labels (e.g. 'Preferences (75)') rank before bare 'Preferences'.
    """
    driver.switch_to.default_content()
    seen_ids = []
    out = []

    def maybe_add(el):
        try:
            if not el.is_displayed():
                return
            cid = el.id
            dup = False
            for u in seen_ids:
                if u == cid:
                    dup = True
                    break
            if dup:
                return
            txt = (el.text or "").strip()
            if len(txt) > 88:
                return
            if not _element_text_matches_tab_key(txt, tab_key):
                return
            seen_ids.append(cid)
            out.append(el)
        except Exception:  # noqa: BLE001
            return

    for xp in (
        "//div[contains(@class,'tab-list-item')]",
        "//*[@role='tab']",
    ):
        try:
            for el in driver.find_elements(By.XPATH, xp)[:100]:
                maybe_add(el)
        except Exception:  # noqa: BLE001
            continue

    def sort_key(el):
        try:
            t = (el.text or "").strip()
            inside = _is_inside_recommended_tab_strip(driver, el)
            has_cnt = "(" in t and ")" in t
        except Exception:  # noqa: BLE001
            t = ""
            inside = False
            has_cnt = False
        return (0 if inside else 1, 0 if has_cnt else 1, -len(t))

    out.sort(key=sort_key)
    return out


def _try_activate_feed_tab(driver, el, tab_contains: str, tab_key: str) -> bool:
    """Scroll strip, click (JS / Actions / native), verify active tab when DOM exposes it."""
    _snap_tab_strip_scroll(driver, el)
    time.sleep(0.14)
    before = _active_feed_tab_blob(driver)
    strategies = (
        lambda e: driver.execute_script("arguments[0].click();", e),
        lambda e: ActionChains(driver).move_to_element(e).pause(0.1).click().perform(),
        lambda e: e.click(),
        lambda e: driver.execute_script(
            "arguments[0].dispatchEvent(new MouseEvent('click',{bubbles:true,cancelable:true,view:window}));",
            e,
        ),
    )
    tried_any = False
    for strat in strategies:
        try:
            strat(el)
            tried_any = True
            time.sleep(1.25)
            after = _active_feed_tab_blob(driver)
            if not after.strip():
                time.sleep(0.95)
                after = _active_feed_tab_blob(driver)
            if after.strip() and _blob_matches_tab_key(after, tab_key):
                log_info(
                    f"Batch apply: opened feed tab «{tab_contains}» (verified active «{after[:120]}»)"
                )
                return True
        except Exception:  # noqa: BLE001
            continue

    after = _active_feed_tab_blob(driver)
    if not after.strip():
        time.sleep(0.4)
        after = _active_feed_tab_blob(driver)
    if after.strip() and _blob_matches_tab_key(after, tab_key):
        log_info(
            f"Batch apply: opened feed tab «{tab_contains}» (verified active «{after[:120]}»)"
        )
        return True

    if before.strip() and after.strip() and before != after:
        log_info(
            f"Batch apply: opened feed tab «{tab_contains}» (active strip changed; token match not confirmed)"
        )
        return True

    if tried_any and not before.strip() and not after.strip():
        log_info(
            f"Batch apply: opened feed tab «{tab_contains}» (no active-state in DOM; assuming ok)"
        )
        return True

    return False


def _click_feed_tab(driver, tab_contains: str) -> bool:
    """
    Open Applies / Profile / Top Candidate / … on recommended jobs.
    Prefers tab-wrapper targets and in-strip tab-list-item (never shortest-text global match).
    Verifies aria-selected / active class when available.
    """
    tab_key = _feed_tab_keyword(tab_contains)
    if not tab_key:
        return False
    driver.switch_to.default_content()
    time.sleep(0.5)

    for twid in _naukri_tab_wrapper_ids(tab_key):
        wrap_xp = (
            f"//div[contains(@class,'tab-wrapper')][@id='{twid}']//div[contains(@class,'tab-list-item')]"
        )
        try:
            for el in driver.find_elements(By.XPATH, wrap_xp):
                try:
                    if not el.is_displayed():
                        continue
                    txt = (el.text or "").strip()
                    if not _element_text_matches_tab_key(txt, tab_key):
                        continue
                    if _try_activate_feed_tab(driver, el, tab_contains, tab_key):
                        return True
                except Exception:  # noqa: BLE001
                    continue
        except Exception:  # noqa: BLE001
            continue
        try:
            wrap = driver.find_element(
                By.XPATH,
                f"//div[contains(@class,'tab-wrapper')][@id='{twid}']",
            )
            if wrap.is_displayed() and _try_activate_feed_tab(driver, wrap, tab_contains, tab_key):
                return True
        except Exception:  # noqa: BLE001
            continue

    for el in _collect_feed_tab_candidates(driver, tab_key)[:16]:
        try:
            if _try_activate_feed_tab(driver, el, tab_contains, tab_key):
                return True
        except Exception:  # noqa: BLE001
            continue

    log_info(f"Batch apply: could not click feed tab «{tab_contains}»")
    return False


def reload_recommended_and_tab(driver, tab_label: str) -> int:
    """Navigate back to recommended jobs (post-apply redirect) and reopen the feed tab."""
    driver.switch_to.default_content()
    driver.get(config.RECOMMENDED_URL)
    time.sleep(5)
    prepare_recommended_page(driver)
    if not _click_feed_tab(driver, tab_label):
        log_info(f"Batch apply: could not switch to feed tab «{tab_label}» after reload")
        return 0
    driver.switch_to.default_content()
    time.sleep(1.0)
    driver.execute_script("window.scrollTo(0, 0);")
    time.sleep(0.55)
    _ensure_job_list_context(driver)
    _nudge_recommended_jobs_visible(driver)
    time.sleep(0.35)
    n = _scroll_until_toggles(driver, max_rounds=16)
    if n == 0:
        log_info(
            f"Batch apply: 0 toggles after tab «{tab_label}» — re-running prepare + iframe detect"
        )
        n = prepare_recommended_page(driver)
        if n == 0:
            n = _scroll_until_toggles(driver, max_rounds=16)
    log_info(f"Batch apply: toggle count on «{tab_label}» after switch = {n}")
    return n


def select_batch_deduped(
    driver,
    start_index: int,
    max_pick: int | None,
    jobs_data: list,
    tab_label: str | None = None,
) -> list:
    """
    Toggle job rows whose card text is not already in jobs.json (dedupe per NAUKRI_DEDUPE_SCOPE).
    Returns [{"index": int, "description": str}, ...] for rows that were checked on.
    """
    cap = max(1, max_pick if max_pick is not None else config.BATCH_SIZE)
    driver.execute_script("window.scrollTo(0, 0);")
    time.sleep(0.2)
    toggles = _find_job_toggles(driver)
    out = []
    batch_texts = []

    for i in range(start_index, len(toggles)):
        if len(out) >= cap:
            break
        try:
            el = toggles[i]
            text = _extract_job_card_text(driver, el)
            if len(text) < config.DEDUPE_MIN_CHARS:
                continue
            if _job_description_recorded(jobs_data, text, tab_label):
                continue
            dup_in_batch = False
            for prev in batch_texts:
                if _job_texts_overlap(text, prev):
                    dup_in_batch = True
                    break
            if dup_in_batch:
                continue
            if not _try_click_job_toggle(driver, el):
                continue
            out.append({"index": i, "description": text[:config.DESC_MAX_STORE]})
            batch_texts.append(text)
        except Exception:  # noqa: BLE001
            continue

    if not out and toggles:
        log_info(
            f"Batch apply: 0 new picks from {len(toggles)} job-row toggle(s) "
            f"(dedupe scope={config.DEDUPE_SCOPE}, min description {config.DEDUPE_MIN_CHARS} chars, or batch overlap)"
        )

    return out


def _find_apply_button_current(driver):
    """Visible Apply control in the active document (root or iframe)."""
    for xp in (
        "//button[contains(translate(normalize-space(.),'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'apply')]"
        "[contains(translate(.,'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'job')]",
        "//button[contains(.,'Apply') and contains(.,'Job')]",
        "//a[contains(.,'Apply') and contains(.,'Job')]",
        "//button[contains(normalize-space(.),'Apply')]",
        "//button[contains(.,'Apply')]",
    ):
        for el in driver.find_elements(By.XPATH, xp):
            try:
                if el.is_displayed():
                    return el
            except Exception:  # noqa: BLE001
                continue
    return None


def click_apply(driver) -> None:
    """Apply batch: search root then each iframe (recommended list is often embedded)."""
    deadline = time.time() + max(8, config.APPLY_BTN_WAIT)
    clicked = False
    clicked_from_iframe = False
    while time.time() < deadline and not clicked:
        driver.switch_to.default_content()
        btn = _find_apply_button_current(driver)
        if btn is not None:
            driver.execute_script("arguments[0].scrollIntoView({block:'center'});", btn)
            time.sleep(0.2)
            driver.execute_script("arguments[0].click();", btn)
            clicked = True
            break
        for fr in driver.find_elements(By.TAG_NAME, "iframe"):
            try:
                driver.switch_to.default_content()
                driver.switch_to.frame(fr)
                btn = _find_apply_button_current(driver)
                if btn is not None:
                    driver.execute_script("arguments[0].scrollIntoView({block:'center'});", btn)
                    time.sleep(0.2)
                    driver.execute_script("arguments[0].click();", btn)
                    clicked = True
                    clicked_from_iframe = True
                    break
            except Exception:  # noqa: BLE001
                pass
            finally:
                driver.switch_to.default_content()
        if clicked:
            break
        time.sleep(0.45)

    driver.switch_to.default_content()
    if not clicked:
        raise TimeoutException("Apply button not found in root or iframes; check page state.")

    print("Applied batch")
    if clicked_from_iframe:
        log_info("Applied batch (Apply control was inside an iframe)")
    else:
        log_info("Applied batch")
    time.sleep(1.5)


def process_all_batches(driver) -> None:
    print("Starting batch apply (reload after each Apply + modal fill)")
    log_info("Batch apply: starting")

    jobs_data = _read_jobs()
    applied_total = 0

    for tab_label in config.BATCH_TABS:
        print(f"--- Tab: {tab_label} ---")
        log_info(f"Batch apply: tab » {tab_label}")

        batches = 0
        empty_pick_rounds = 0
        modal_fail_streak = 0
        apply_click_fail_streak = 0
        while True:
            if batches >= config.MAX_BATCHES_PER_TAB:
                log_info(
                    f"Batch apply: tab «{tab_label}» — NAUKRIconfig.MAX_BATCHES_PER_TAB={config.MAX_BATCHES_PER_TAB} reached; next tab"
                )
                break
            if config.MAX_APPLY_JOBS > 0 and applied_total >= config.MAX_APPLY_JOBS:
                log_info(f"Batch apply: stopped — NAUKRIconfig.MAX_APPLY_JOBS={config.MAX_APPLY_JOBS} reached")
                print("Max apply jobs reached:", applied_total)
                _write_jobs(jobs_data)
                return

            n = reload_recommended_and_tab(driver, tab_label)
            print(f"  Toggles after reload: {n}")
            log_info(f"Batch apply: {tab_label} — {n} toggle(s) after reload")

            if n == 0:
                log_info(f"Batch apply: no job toggles on «{tab_label}» — moving to next tab")
                break

            remaining = config.MAX_APPLY_JOBS - applied_total if config.MAX_APPLY_JOBS > 0 else config.BATCH_SIZE
            take = min(config.BATCH_SIZE, remaining) if config.MAX_APPLY_JOBS > 0 else config.BATCH_SIZE

            picks = select_batch_deduped(driver, 0, take, jobs_data, tab_label)
            if not picks:
                empty_pick_rounds += 1
                apply_click_fail_streak = 0
                modal_fail_streak = 0
                log_info(
                    f"Batch apply: no new jobs to select (duplicates or short text) "
                    f"«{tab_label}» round {empty_pick_rounds}"
                )
                print(
                    f"  No picks ({empty_pick_rounds}/{config.EMPTY_PICK_TAB_ROUNDS}): {n} job-row toggles, "
                    f"dedupe={config.DEDUPE_SCOPE} (use global only if you want one job across all tabs once)"
                )
                if empty_pick_rounds >= config.EMPTY_PICK_TAB_ROUNDS:
                    log_info(
                        f"Batch apply: «{tab_label}» — no new picks after {config.EMPTY_PICK_TAB_ROUNDS} scroll rounds; next tab"
                    )
                    break
                driver.execute_script("window.scrollBy(0, 700);")
                time.sleep(0.65)
                _ensure_job_list_context(driver)
                _scroll_until_toggles(driver, max_rounds=6)
                continue

            empty_pick_rounds = 0
            pending_ids = []
            for p in picks:
                desc = (p.get("description") or "").strip()
                idx = int(p.get("index", -1))
                rec = {
                    "id": str(uuid.uuid4()),
                    "company": "Naukri",
                    "role": _role_line_from_description(desc, tab_label, idx),
                    "description": desc[:config.DESC_MAX_STORE],
                    "status": "PendingApply",
                    "source": tab_label,
                    "link": "",
                    "applied_date": str(datetime.now().date()),
                    "time": str(datetime.now()),
                }
                jobs_data.append(rec)
                pending_ids.append(rec["id"])

            _write_jobs(jobs_data)
            log_info(
                f"Batch apply: wrote {len(pending_ids)} pending row(s) with description to jobs.json"
            )

            try:
                click_apply(driver)
            except TimeoutException:
                apply_click_fail_streak += 1
                for row in jobs_data:
                    if row.get("id") in pending_ids:
                        row["status"] = "ApplyUncertain"
                _write_jobs(jobs_data)
                log_info(
                    f"Batch apply: Apply button not found (timeout) «{tab_label}» "
                    f"streak {apply_click_fail_streak}/{config.APPLY_CLICK_FAIL_TAB_BREAK}"
                )
                print(
                    f"  Apply click failed (timeout). Streak {apply_click_fail_streak}. "
                    "Check that job checkboxes are selected and Apply Jobs is visible."
                )
                if apply_click_fail_streak >= config.APPLY_CLICK_FAIL_TAB_BREAK:
                    log_info(
                        f"Batch apply: leaving «{tab_label}» after {config.APPLY_CLICK_FAIL_TAB_BREAK} Apply timeouts"
                    )
                    break
                time.sleep(1.4)
                continue

            apply_click_fail_streak = 0
            modal_ok = handle_apply_modal(driver)
            if not modal_ok:
                modal_fail_streak += 1
                log_info(
                    f"Batch apply: post-apply modal not fully cleared — streak "
                    f"{modal_fail_streak}/{config.MODAL_FAIL_TAB_BREAK}"
                )
                print("  Modal may still be open; check LWD / screening popups in the browser.")
                if modal_fail_streak >= config.MODAL_FAIL_TAB_BREAK:
                    for row in jobs_data:
                        if row.get("id") in pending_ids:
                            row["status"] = "ApplyUncertain"
                    _write_jobs(jobs_data)
                    log_info(
                        f"Batch apply: leaving «{tab_label}» after {config.MODAL_FAIL_TAB_BREAK} modal failures"
                    )
                    break
            else:
                modal_fail_streak = 0

            final_status = "Applied" if modal_ok else "ApplyUncertain"
            for row in jobs_data:
                rid = row.get("id")
                if rid in pending_ids:
                    row["status"] = final_status

            if modal_ok:
                applied_total += len(picks)
            _write_jobs(jobs_data)
            try:
                from core.application_logger import log_application
                from core.runtime_state import increment_failed, update_runtime
                from sheets_client import set_current_job

                roles = []
                for p in picks:
                    desc = (p.get("description") or "").strip()
                    idx = int(p.get("index", -1))
                    role = _role_line_from_description(desc, tab_label, idx)
                    company = _company_from_description(desc)
                    roles.append(role)
                    update_runtime(current_company=company[:255], current_job=role[:500])
                    if modal_ok:
                        log_application(company=company, role=role, status="SUCCESS")
                    else:
                        log_application(
                            company=company,
                            role=role,
                            status="FAILED",
                            error="Apply modal not fully cleared",
                        )
                        increment_failed(error="Apply modal not fully cleared")
                if roles:
                    label = roles[0] if len(roles) == 1 else f"{roles[0]} (+{len(roles) - 1} more)"
                    company = _company_from_description((picks[0].get("description") or ""))
                    set_current_job(label)
                    update_runtime(current_company=company[:255], current_job=label[:500])
            except Exception:  # noqa: BLE001
                pass
            batches += 1
            log_info(
                f"Batch apply: batch done {len(picks)} job(s); "
                f"total applied (cleared modal)={applied_total}; status={final_status}"
            )
            print(f"  Batch: {len(picks)} job(s) → {final_status}")
            time.sleep(1.2)

        log_info(f"Batch apply: tab done «{tab_label}» ({batches} batch(es))")

    print("All tab passes completed; total applied:", applied_total)
    log_info(f"Batch apply: finished; total applied={applied_total}")


def run_batch_flow(driver) -> None:
    try:
        process_all_batches(driver)
    except Exception as e:  # noqa: BLE001
        print("Batch error:", e)
        try:
            from core.application_logger import log_application
            from core.runtime_state import increment_failed, update_runtime

            log_application(company="Naukri", role="Batch", status="FAILED", error=str(e))
            increment_failed(error=str(e))
            update_runtime(last_error=str(e)[:500])
            log_info(f"Batch apply error: {e!s}")
        except Exception:  # noqa: BLE001
            pass
        raise


def run_naukri_batch_flow() -> None:
    from core.browser import start_driver
    from naukri.login import credentials_ok, login_naukri

    driver = None
    try:
        log_info("Batch apply: starting Chrome")
        driver = start_driver()

        if credentials_ok():
            login_naukri(driver)
        else:
            log_info("Batch apply: NAUKRI credentials not set; page may require login")

        driver.get(config.RECOMMENDED_URL)
        time.sleep(6)

        n = prepare_recommended_page(driver)
        print("Toggles after prepare:", n)
        log_info(f"Batch apply: found {n} toggle(s) after initial load")

        run_batch_flow(driver)

    except Exception as e:  # noqa: BLE001
        print("FLOW ERROR:", e)
        try:
            log_info(f"Batch apply flow error: {e!s}")
        except Exception:  # noqa: BLE001
            pass
        raise
    finally:
        if driver is not None:
            try:
                driver.switch_to.default_content()
            except Exception:  # noqa: BLE001
                pass
            try:
                driver.quit()
            except Exception:  # noqa: BLE001
                pass
        try:
            log_info("Batch apply: browser closed")
        except Exception:  # noqa: BLE001
            pass
