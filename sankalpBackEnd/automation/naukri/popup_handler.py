"""Naukri apply popup / screening modal handler."""
import os
import random
import time

from selenium.common.exceptions import StaleElementReferenceException
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait

from core import config
from core.logger import log_info
from core.storage import read_json, write_json

def _random_fallback_reply() -> str:
    choices = [x.strip() for x in config.FALLBACK_REPLIES.split(",") if x.strip()]
    return random.choice(choices) if choices else "NO"


def _dialog_text_blobs(driver) -> str:
    """Lowercased text from likely dialog/chat containers (for keyword routing)."""
    chunks = []
    for xp in (
        "//*[@role='dialog']//*",
        "//*[contains(@class,'chat')]",
        "//*[contains(@class,'modal')]",
        "//*[contains(@class,'drawer')]",
        "//*[contains(@class,'popup')]",
    ):
        try:
            for el in driver.find_elements(By.XPATH, xp)[:50]:
                try:
                    if el.is_displayed():
                        t = (el.text or "").strip()
                        if len(t) > 2:
                            chunks.append(t)
                except Exception:  # noqa: BLE001
                    continue
        except Exception:  # noqa: BLE001
            continue
    return " ".join(chunks)[:8000].lower()


def _choose_reply_for_question(q_lower: str) -> str:
    from ai.answer_engine import generate_answer
    from ai.resume_parser import read_resume
    from models.user_config import load_user_config

    if not (q_lower or "").strip():
        return ""

    cfg = load_user_config()
    resume = read_resume()
    ans = generate_answer(question=q_lower, resume_text=resume, cfg=cfg)
    if ans:
        log_info("Popup: AI answer ready")
        return ans
    return "Can discuss further during interview"


def _find_type_message_field(driver):
    xps = [
        "//textarea[contains(translate(@placeholder,'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'type message here')]",
        "//textarea[contains(@placeholder,'Type message')]",
        "//input[contains(@placeholder,'Type message')]",
        "//input[contains(translate(@placeholder,'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'type message')]",
    ]
    for xp in xps:
        for el in driver.find_elements(By.XPATH, xp):
            try:
                if el.is_displayed():
                    return el
            except Exception:  # noqa: BLE001
                continue
    for el in driver.find_elements(By.XPATH, "//div[@contenteditable='true']"):
        try:
            if el.is_displayed() and (el.text or "").strip() == "":
                return el
        except Exception:  # noqa: BLE001
            continue
    return None


def _notify_input_changed(driver, el) -> None:
    """Fire input/change so Angular/React-style validators enable Apply/Save."""
    driver.execute_script(
        """
        var n = arguments[0];
        if (!n) return;
        n.dispatchEvent(new Event('input', { bubbles: true }));
        n.dispatchEvent(new Event('change', { bubbles: true }));
        if (typeof InputEvent === 'function') {
          try {
            n.dispatchEvent(new InputEvent('input', { bubbles: true, inputType: 'insertText' }));
          } catch (e) {}
        }
        """,
        el,
    )


def _focus_field_like_user(driver, el) -> None:
    """Click inside the control with a small offset (caret placement) so Naukri enables the button."""
    driver.execute_script("arguments[0].scrollIntoView({block:'center'});", el)
    time.sleep(0.06)
    try:
        ActionChains(driver).move_to_element_with_offset(el, 3, 3).click().pause(0.05).perform()
    except Exception:  # noqa: BLE001
        try:
            el.click()
        except Exception:  # noqa: BLE001
            driver.execute_script("arguments[0].focus();", el)


def _type_into_field(driver, el, text: str) -> None:
    tag = el.tag_name.lower()
    raw = str(text)
    if tag in ("textarea", "input"):
        _focus_field_like_user(driver, el)
        try:
            el.clear()
        except Exception:  # noqa: BLE001
            pass
        el.send_keys(raw)
        # One extra keystroke cycle wakes validators that ignore a single paste/send_keys batch.
        try:
            el.send_keys(Keys.SPACE)
            el.send_keys(Keys.BACK_SPACE)
        except Exception:  # noqa: BLE001
            pass
        _notify_input_changed(driver, el)
        time.sleep(0.12)
    else:
        _focus_field_like_user(driver, el)
        driver.execute_script(
            """
            var el = arguments[0], t = arguments[1];
            el.focus();
            el.innerText = '';
            el.dispatchEvent(new Event('input', { bubbles: true }));
            el.innerText = t;
            el.dispatchEvent(new Event('input', { bubbles: true }));
            el.dispatchEvent(new Event('change', { bubbles: true }));
            if (typeof InputEvent === 'function') {
              try {
                el.dispatchEvent(new InputEvent('input', { bubbles: true, inputType: 'insertText' }));
              } catch (e) {}
            }
            """,
            el,
            raw,
        )
        time.sleep(0.12)


def _try_dismiss_any_overlay(driver) -> bool:
    xps = [
        "//button[normalize-space()='×']",
        "//*[@aria-label='Close']",
        "//button[contains(@aria-label,'Close')]",
        "//*[contains(@class,'closeIcon')]",
        "//button[contains(@class,'close')]",
        "//button[contains(.,'Skip')][not(ancestor::*[@role='dialog'])]",
        "//button[contains(.,'Cancel')]",
    ]
    for xp in xps:
        for el in driver.find_elements(By.XPATH, xp):
            try:
                if el.is_displayed():
                    driver.execute_script("arguments[0].click();", el)
                    time.sleep(0.45)
                    return True
            except Exception:  # noqa: BLE001
                continue
    return False


def _popup_still_visible(driver) -> bool:
    """Heuristic: chat 'Type message here' or LWD-style question still on screen."""
    markers = [
        "//textarea[contains(translate(@placeholder,'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'type message')]",
        "//*[contains(translate(.,'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'mention lwd')]",
        "//*[contains(translate(.,'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'serving notice')]",
        "//*[@role='dialog']//button[contains(normalize-space(.),'Save')]",
        "//div[contains(@class,'sendMsg')][normalize-space(.)='Save']",
        "//*[contains(@id,'sendMsg')][normalize-space(.)='Save']",
    ]
    for xp in markers:
        for el in driver.find_elements(By.XPATH, xp):
            try:
                if el.is_displayed():
                    return True
            except Exception:  # noqa: BLE001
                continue
    return False


def _try_js_click_visible(driver, el) -> bool:
    try:
        if not el.is_displayed():
            return False
        driver.execute_script("arguments[0].scrollIntoView({block:'center'});", el)
        time.sleep(0.05)
        driver.execute_script("arguments[0].click();", el)
        return True
    except Exception:  # noqa: BLE001
        return False


def _click_checkbox_skip_targets(driver, q_lower: str) -> None:
    """
    City / multi-choice modals often omit role=dialog. Click Skip by label/span/mcc class,
    by checkbox+label text, then last checkbox in the city block (Skip is usually last).
    """
    skip_xps = (
        "//label[contains(translate(.,'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'skip this question')][not(.//input[@type='radio'])]",
        "//*[@role='dialog']//label[contains(translate(.,'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'skip this question')][not(.//input[@type='radio'])]",
        "//span[contains(translate(.,'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'skip this question')]",
        "//*[contains(@class,'mcc')][contains(translate(.,'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'skip')][not(.//input[@type='radio'])]",
        "//div[contains(@class,'label')][contains(translate(.,'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'skip this question')]",
        "//a[contains(translate(.,'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'skip this question')]",
        "//*[contains(translate(normalize-space(.),'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'skip this question')][not(.//input[@type='radio'])][self::label or self::div or self::span]",
        "//label[contains(translate(.,'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'skip')][contains(translate(.,'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'question')][not(.//input[@type='radio'])]",
    )
    clicked = False
    for xp in skip_xps:
        for el in driver.find_elements(By.XPATH, xp):
            if _try_js_click_visible(driver, el):
                clicked = True
                time.sleep(0.12)

    for span in driver.find_elements(
        By.XPATH,
        "//span[contains(translate(.,'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'skip this question')]",
    ):
        try:
            if not span.is_displayed():
                continue
            lab = span.find_element(By.XPATH, "./ancestor::label[1]")
            if _try_js_click_visible(driver, lab):
                clicked = True
                time.sleep(0.12)
        except Exception:  # noqa: BLE001
            if _try_js_click_visible(driver, span):
                clicked = True
                time.sleep(0.12)

    for inp in driver.find_elements(By.XPATH, "//input[@type='checkbox']"):
        try:
            if not inp.is_displayed():
                continue
            parts = []
            lid = (inp.get_attribute("id") or "").strip()
            if lid:
                for lb in driver.find_elements(By.TAG_NAME, "label"):
                    try:
                        if (lb.get_attribute("for") or "") != lid:
                            continue
                        parts.append((lb.text or "").lower())
                    except Exception:  # noqa: BLE001
                        continue
            for rel in ("./following-sibling::label[1]", "./preceding-sibling::label[1]", "./../label"):
                try:
                    lb = inp.find_element(By.XPATH, rel)
                    parts.append((lb.text or "").lower())
                except Exception:  # noqa: BLE001
                    continue
            blob = " ".join(parts)
            if "skip" in blob and "question" in blob:
                if _try_js_click_visible(driver, inp):
                    clicked = True
                    time.sleep(0.12)
        except Exception:  # noqa: BLE001
            continue

    if clicked:
        return

    city_hint = any(
        k in q_lower
        for k in (
            "city",
            "relocat",
            "residing",
            "location",
            "metro",
            "willing to",
        )
    )
    if city_hint or "skip" in q_lower:
        for xp in (
            "//*[contains(translate(.,'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'currently residing')]"
            "/ancestor::*[position()<=14]//input[@type='checkbox'][last()]",
            "//*[contains(translate(.,'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'willing to relocate')]"
            "/ancestor::*[position()<=14]//input[@type='checkbox'][last()]",
            "//*[contains(translate(.,'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'select the city')]"
            "/ancestor::*[position()<=14]//input[@type='checkbox'][last()]",
        ):
            for inp in driver.find_elements(By.XPATH, xp):
                if _try_js_click_visible(driver, inp):
                    time.sleep(0.12)
                    return

    if not clicked and city_hint:
        vis = []
        for inp in driver.find_elements(By.XPATH, "//input[@type='checkbox']"):
            try:
                if inp.is_displayed():
                    vis.append(inp)
            except Exception:  # noqa: BLE001
                continue
        for inp in reversed(vis[-10:]):
            if _try_js_click_visible(driver, inp):
                time.sleep(0.12)
                return

    city = (os.getenv("NAUKRI_QA_CURRENT_CITY", "") or "").strip()
    if city and city_hint:
        needle = city.replace("'", "").lower()
        if needle:
            safe = needle.replace("'", "''")
            xp = (
                "//label[contains(translate(.,'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'%s')]"
                "[not(.//input[@type='radio'])]"
                % safe
            )
            for lab in driver.find_elements(By.XPATH, xp):
                if _try_js_click_visible(driver, lab):
                    time.sleep(0.12)
                    return


def _lwd_compact_for_inline() -> str:
    """Short LWD value for small inline inputs (e.g. digits only from NAUKRI_LWD_REPLY)."""
    reply = (config.LWD_REPLY or "").strip()
    buf = []
    for ch in reply:
        if ch.isdigit():
            buf.append(ch)
        elif buf:
            break
    if buf:
        return "".join(buf)
    return "15"


def _na_apply_years_int() -> int:
    try:
        raw = (config.APPLY_YEARS or "3").strip().split()[0]
        return int(float(raw))
    except Exception:  # noqa: BLE001
        return 3


def _click_modal_header_skip(driver) -> bool:
    """Screening header 'Skip' (not 'Skip this question' checkbox row)."""
    xps = (
        "//*[@role='dialog']//*[self::button or self::a][normalize-space(.)='Skip']",
        "//*[contains(@class,'modal') or contains(@class,'drawer') or contains(@class,'chat')]"
        "//*[self::button or self::a][normalize-space(.)='Skip'][not(contains(.,'question'))]",
    )
    for xp in xps:
        for el in driver.find_elements(By.XPATH, xp):
            try:
                if el.is_displayed() and _try_js_click_visible(driver, el):
                    time.sleep(0.15)
                    return True
            except Exception:  # noqa: BLE001
                continue
    return False


def _question_is_skill_year_experience_band(q_lower: str) -> bool:
    """Skill-specific YOE radios, e.g. 'How many years of experience do you have in Java ?'."""
    if "experience" not in q_lower and "year" not in q_lower:
        return False
    if " java" in q_lower or " in java" in q_lower:
        return True
    if " in " in q_lower and (
        "how many" in q_lower or "experience do you have" in q_lower or "years do you have" in q_lower
    ):
        return True
    return False


def _radio_needles_skill_yoe_bands_three_plus() -> list:
    """Prefer 3–5 and >5 when NAUKRI_APPLY_YEARS is 3+ (above the 1–3 band)."""
    return [
        "3-5",
        "3 - 5",
        "3–5",
        ">5",
        "> 5",
        "5+",
        "4-5",
        "1-3",
        "1 - 3",
        "1–3",
        "2-3",
        "2 - 3",
        "<1",
        "< 1",
        "1 year",
        "no experience",
    ]


def _radio_labels_for_years_band(y: int):
    """Substrings to match Naukri '1-3 years' style bands (order = preference)."""
    if y <= 0:
        return ["<1", "< 1", "1 year", "1-3", "1 - 3"]
    if y <= 1:
        return ["<1", "< 1", "1 year", "1-3", "1 - 3", "1–3"]
    if y <= 3:
        return ["1-3", "1 - 3", "1–3", "2-3", "2 - 3", "3-5", "3 - 5"]
    if y <= 5:
        return ["3-5", "3 - 5", "4-5", "3-6", "1-3", "1 - 3"]
    return [">5", "> 5", "5+", "3-5", "3 - 5"]


def _pick_years_band_radio(driver, q_lower: str) -> bool:
    """e.g. 'years of experience in Java' + radios 1-3 / 3-5 — pick a band from NAUKRI_APPLY_YEARS."""
    if "experience" not in q_lower and "year" not in q_lower:
        return False
    y = _na_apply_years_int()
    if _question_is_skill_year_experience_band(q_lower) and y >= 3:
        needles = _radio_needles_skill_yoe_bands_three_plus()
    else:
        needles = _radio_labels_for_years_band(y)
    for needle in needles:
        safe = needle.replace("'", "''").lower()
        xps = (
            "//label[contains(translate(.,'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'%s')]"
            "[.//input[@type='radio']]"
            % safe,
            "//*[@role='dialog']//label[contains(translate(.,'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'%s')]"
            "[.//input[@type='radio']]"
            % safe,
        )
        for xp in xps:
            for lab in driver.find_elements(By.XPATH, xp):
                try:
                    if lab.is_displayed() and _try_js_click_visible(driver, lab):
                        time.sleep(0.12)
                        return True
                except Exception:  # noqa: BLE001
                    continue
    return False


def _checkbox_row_label_lower(driver, inp) -> str:
    try:
        lab = inp.find_element(By.XPATH, "./ancestor::label[1]")
        return (lab.text or "").strip().lower()
    except Exception:  # noqa: BLE001
        return ""


def _visible_modal_checkbox_inputs(driver):
    """Native checkboxes in apply modal / chat — excludes 'Skip this question' row."""
    out = []
    for xp in (
        "//*[@role='dialog']//input[@type='checkbox']",
        "//*[contains(@class,'modal') or contains(@class,'drawer') or contains(@class,'chat') or contains(@class,'popup')]"
        "//input[@type='checkbox']",
    ):
        for inp in driver.find_elements(By.XPATH, xp):
            try:
                if not inp.is_displayed():
                    continue
                row = _checkbox_row_label_lower(driver, inp)
                if "skip this question" in row:
                    continue
                out.append(inp)
            except Exception:  # noqa: BLE001
                continue
    seen_ids = []
    uniq = []
    for inp in out:
        try:
            cid = inp.id
        except Exception:  # noqa: BLE001
            cid = None
        if cid is None:
            uniq.append(inp)
            continue
        dup = False
        for u in seen_ids:
            if u == cid:
                dup = True
                break
        if dup:
            continue
        seen_ids.append(cid)
        uniq.append(inp)
    return uniq


def _try_random_unknown_modal_checkbox(driver, q_lower: str) -> bool:
    """
    No Qa.txt match: if two or more modal checkboxes (and none selected yet), pick one at random,
    log question blob to data/missed_questions.json, then click.
    """
    if config.RANDOM_UNKNOWN_CHECKBOX in ("0", "false", "no", "off"):
        return False
    if (_choose_reply_for_question(q_lower) or "").strip():
        return False
    boxes = _visible_modal_checkbox_inputs(driver)
    if len(boxes) < 2:
        return False
    for b in boxes:
        try:
            if b.is_selected():
                return False
        except Exception:  # noqa: BLE001
            continue
    pick = random.choice(boxes)
    _append_missed_question(q_lower, "random_checkbox_no_qa_match")
    if _try_js_click_visible(driver, pick):
        time.sleep(0.12)
        return True
    return False


def _pick_first_sensible_modal_radio(driver) -> bool:
    """
    Unknown multiple-choice: pick one option so Save enables — skip 'No experience' only
    when other choices exist in the same radio group.
    """
    radios = driver.find_elements(By.XPATH, "//input[@type='radio']")
    by_name = {}
    for r in radios:
        try:
            if not r.is_displayed():
                continue
            nm = (r.get_attribute("name") or "").strip() or (r.get_attribute("id") or "").strip()
            if not nm:
                nm = "_anon_%d" % id(r)
            if nm not in by_name:
                by_name[nm] = []
            by_name[nm].append(r)
        except Exception:  # noqa: BLE001
            continue

    for nm in sorted(by_name.keys()):
        group = by_name[nm]
        if len(group) < 2:
            continue
        for inp in group:
            try:
                lab = None
                rid = (inp.get_attribute("id") or "").strip()
                if rid:
                    for lb in driver.find_elements(By.TAG_NAME, "label"):
                        if (lb.get_attribute("for") or "") == rid:
                            lab = lb
                            break
                if lab is None:
                    try:
                        lab = inp.find_element(By.XPATH, "./ancestor::label[1]")
                    except Exception:  # noqa: BLE001
                        lab = None
                t = ((lab.text or "") if lab is not None else "").strip().lower()
                if t in ("no experience", "no exp", "no"):
                    continue
                if _try_js_click_visible(driver, inp):
                    time.sleep(0.12)
                    return True
                if lab is not None and _try_js_click_visible(driver, lab):
                    time.sleep(0.12)
                    return True
            except Exception:  # noqa: BLE001
                continue
        for inp in group:
            try:
                rid = (inp.get_attribute("id") or "").strip()
                lab = None
                if rid:
                    for lb in driver.find_elements(By.TAG_NAME, "label"):
                        if (lb.get_attribute("for") or "") == rid:
                            lab = lb
                            break
                if lab is None:
                    try:
                        lab = inp.find_element(By.XPATH, "./ancestor::label[1]")
                    except Exception:  # noqa: BLE001
                        lab = None
                t = ((lab.text or "") if lab is not None else "").strip()
                val = (inp.get_attribute("value") or "").strip()
                if _is_yes_choice_label_text(t) or _radio_matches_pref(t, val, "yes"):
                    if _try_js_click_visible(driver, inp):
                        time.sleep(0.12)
                        return True
                    if lab is not None and _try_js_click_visible(driver, lab):
                        time.sleep(0.12)
                        return True
            except Exception:  # noqa: BLE001
                continue
        try:
            inp0 = group[0]
            if _try_js_click_visible(driver, inp0):
                time.sleep(0.12)
                return True
        except Exception:  # noqa: BLE001
            continue
    return False


def _is_yes_choice_label_text(text: str) -> bool:
    """True for Yes / YES / yes / 'Yes,' etc. on apply-popup radios (not 'Yesterday')."""
    raw = (text or "").strip().lower()
    if not raw:
        return False
    first = raw.replace(",", " ").split()[0].strip(".,;:!?\"'")
    if first == "yes":
        return True
    if first == "y" and len(raw.replace(",", " ").split()) == 1:
        return True
    return False


def _radio_pref_tokens() -> list:
    """Ordered tokens to match on radio labels (first match wins per group)."""
    out = []
    for chunk in (config.RADIO_DEFAULT_ORDER, config.GENERIC_POPUP_REPLY):
        if not chunk:
            continue
        for part in chunk.split(","):
            p = part.strip().lower()
            if not p or len(p) > 36:
                continue
            dup = False
            for x in out:
                if x == p:
                    dup = True
                    break
            if not dup:
                out.append(p)
    if not out:
        out.append("yes")
    return out


def _find_label_for_radio(driver, inp):
    rid = (inp.get_attribute("id") or "").strip()
    if rid:
        for lb in driver.find_elements(By.TAG_NAME, "label"):
            try:
                if (lb.get_attribute("for") or "") == rid:
                    return lb
            except Exception:  # noqa: BLE001
                continue
    for rel in ("./ancestor::label[1]", "./following-sibling::label[1]", "./preceding-sibling::label[1]"):
        try:
            return inp.find_element(By.XPATH, rel)
        except Exception:  # noqa: BLE001
            continue
    return None


def _radio_choice_label_text(driver, inp) -> str:
    lb = _find_label_for_radio(driver, inp)
    if lb is None:
        return ""
    return (lb.text or "").strip()


def _radio_matches_pref(label_text: str, value_attr: str, pref: str) -> bool:
    if not pref:
        return False
    lt = (label_text or "").strip().lower()
    vv = (value_attr or "").strip().lower()
    if pref == vv or pref == lt:
        return True
    parts = lt.replace(",", " ").split()
    first = parts[0].strip(".,;:!?\"'") if parts else ""
    if first == pref:
        return True
    if lt.startswith(pref) and len(lt) <= len(pref) + 4:
        return True
    return False


def _click_yes_radios_in_apply_popup(driver) -> None:
    """
    Default choice on apply-popups: pick first option matching NAUKRI_RADIO_DEFAULT_ORDER
    tokens (then NAUKRI_GENERIC_POPUP_REPLY), per radio name group — clicks input or sibling label.
    """
    prefs = _radio_pref_tokens()
    for xp in (
        "//*[@role='dialog']//input[@type='radio'][translate(@value,'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz')='yes']",
        "//*[contains(@class,'modal') or contains(@class,'drawer') or contains(@class,'chat') or contains(@class,'popup')]"
        "//input[@type='radio'][translate(@value,'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz')='yes']",
    ):
        for inp in driver.find_elements(By.XPATH, xp):
            try:
                if inp.is_displayed():
                    _try_js_click_visible(driver, inp)
                    time.sleep(0.06)
            except Exception:  # noqa: BLE001
                continue

    scope_xps = (
        "//*[@role='dialog']//input[@type='radio']",
        "//*[contains(@class,'modal') or contains(@class,'drawer') or contains(@class,'chat') or contains(@class,'popup')]"
        "//input[@type='radio']",
    )
    radios = []
    seen_ids = []
    for xp in scope_xps:
        for r in driver.find_elements(By.XPATH, xp):
            try:
                if not r.is_displayed():
                    continue
                k = id(r)
                if k in seen_ids:
                    continue
                seen_ids.append(k)
                radios.append(r)
            except Exception:  # noqa: BLE001
                continue
    if not radios:
        for r in driver.find_elements(By.XPATH, "//input[@type='radio']"):
            try:
                if r.is_displayed():
                    radios.append(r)
            except Exception:  # noqa: BLE001
                continue

    by_name = {}
    for r in radios:
        nm = (r.get_attribute("name") or "").strip()
        if not nm:
            nm = "_noname_%d" % id(r)
        if nm not in by_name:
            by_name[nm] = []
        by_name[nm].append(r)

    for nm in sorted(by_name.keys()):
        group = by_name[nm]
        if len(group) < 2:
            continue
        picked = False
        for pref in prefs:
            for inp in group:
                try:
                    lt = _radio_choice_label_text(driver, inp)
                    val = (inp.get_attribute("value") or "").strip()
                    if not (_radio_matches_pref(lt, val, pref) or _is_yes_choice_label_text(lt)):
                        continue
                    if _try_js_click_visible(driver, inp):
                        time.sleep(0.1)
                        picked = True
                        break
                    lb = _find_label_for_radio(driver, inp)
                    if lb is not None and _try_js_click_visible(driver, lb):
                        time.sleep(0.1)
                        picked = True
                        break
                except Exception:  # noqa: BLE001
                    continue
            if picked:
                break

    for xp in (
        "//*[@role='dialog']//label[.//input[@type='radio']]",
        "//*[contains(@class,'modal') or contains(@class,'drawer') or contains(@class,'chat') or contains(@class,'popup')]"
        "//label[.//input[@type='radio']]",
        "//label[.//input[@type='radio']][translate(normalize-space(.),'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz')='yes']",
    ):
        for lab in driver.find_elements(By.XPATH, xp):
            try:
                if not lab.is_displayed():
                    continue
                t = (lab.text or "").strip()
                if not _is_yes_choice_label_text(t):
                    continue
                driver.execute_script("arguments[0].scrollIntoView({block:'center'});", lab)
                time.sleep(0.05)
                driver.execute_script("arguments[0].click();", lab)
                time.sleep(0.08)
            except Exception:  # noqa: BLE001
                continue


def _handle_unknown_screening_questions(driver, q_lower: str) -> None:
    """Questions not in Qa rules: year bands; no sheet → random multi-checkbox or header Skip; else radio guess; Skip last."""
    if _pick_years_band_radio(driver, q_lower):
        return
    no_sheet = not (_choose_reply_for_question(q_lower) or "").strip()
    if no_sheet and _try_random_unknown_modal_checkbox(driver, q_lower):
        return
    if no_sheet and _click_modal_header_skip(driver):
        return
    if _pick_first_sensible_modal_radio(driver):
        return
    _click_modal_header_skip(driver)


def _handle_modal_choice_controls(driver, q_lower: str) -> None:
    """
    - Checkbox Skip (city lists, mcc labels): broad DOM — not only role=dialog.
    - Radio Yes / No / Skip: default Yes (Yes, YES, yes, …).
    - Unknown MCQ: skill YOE bands (3+ years → 3–5 />5 first), no Qa match → multi-checkbox random + missed_questions.json or header Skip, else first radio, else header Skip.
    """
    _click_checkbox_skip_targets(driver, q_lower)

    try:
        _click_yes_radios_in_apply_popup(driver)
    except Exception:  # noqa: BLE001
        pass

    _handle_unknown_screening_questions(driver, q_lower)

    try:
        _click_yes_radios_in_apply_popup(driver)
    except Exception:  # noqa: BLE001
        pass


def _try_fill_experience_from_blob(driver, q_lower: str) -> None:
    if "experience" not in q_lower and "years of" not in q_lower:
        return
    if not (config.APPLY_YEARS or "").strip():
        return
    xps = [
        "//*[@role='dialog']//*[contains(translate(.,'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'experience')]/following::input[not(@type='hidden')][@type='text' or @type='number' or not(@type)][1]",
        "//*[@role='dialog']//*[contains(translate(.,'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'experience')]/ancestor::*[position()<=6]//input[not(@type='hidden')][@type='text' or @type='number' or not(@type)][1]",
        "//*[@role='dialog']//input[contains(translate(@placeholder,'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'experience')]",
    ]
    for xp in xps:
        for el in driver.find_elements(By.XPATH, xp):
            try:
                if not el.is_displayed():
                    continue
                _focus_field_like_user(driver, el)
                el.clear()
                el.send_keys(config.APPLY_YEARS)
                el.send_keys(Keys.SPACE)
                el.send_keys(Keys.BACK_SPACE)
                _notify_input_changed(driver, el)
                time.sleep(0.1)
                return
            except Exception:  # noqa: BLE001
                continue


def _try_fill_lwd_inline_from_blob(driver, q_lower: str) -> None:
    if not any(
        k in q_lower
        for k in (
            "lwd",
            "last working day",
            "serving notice",
            "mention lwd",
            "notice period",
        )
    ):
        return
    val = _lwd_compact_for_inline()
    xps = [
        "//*[@role='dialog']//*[contains(translate(.,'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'lwd') or contains(translate(.,'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'serving notice') or contains(translate(.,'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'mention lwd')]/following::input[not(@type='hidden')][@type='text' or @type='number' or not(@type)][1]",
        "//*[@role='dialog']//*[contains(translate(.,'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'notice period')]/following::input[not(@type='hidden')][@type='text' or @type='number' or not(@type)][1]",
        "//*[@role='dialog']//input[not(@type='hidden')][@type='text' or @type='number' or not(@type)]",
    ]
    seen = []
    for xp in xps:
        for el in driver.find_elements(By.XPATH, xp):
            try:
                if not el.is_displayed():
                    continue
                if el.tag_name.lower() != "input":
                    continue
                if el in seen:
                    continue
                seen.append(el)
                ph = (el.get_attribute("placeholder") or "").lower()
                if "type message" in ph:
                    continue
                _focus_field_like_user(driver, el)
                el.clear()
                el.send_keys(val)
                el.send_keys(Keys.SPACE)
                el.send_keys(Keys.BACK_SPACE)
                _notify_input_changed(driver, el)
                time.sleep(0.1)
                return
            except Exception:  # noqa: BLE001
                continue


def _nudge_modal_text_fields(driver) -> None:
    """Focus + space/backspace + events on dialog text controls so Save enables."""
    qb = _dialog_text_blobs(driver)
    _click_checkbox_skip_targets(driver, qb)
    try:
        _click_yes_radios_in_apply_popup(driver)
    except Exception:  # noqa: BLE001
        pass
    _handle_unknown_screening_questions(driver, qb)
    xps = [
        "//*[@role='dialog']//textarea",
        "//textarea[contains(translate(@placeholder,'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'type message')]",
        "//*[contains(@class,'modal') or contains(@class,'chat') or contains(@class,'drawer') or contains(@class,'popup')]"
        "//textarea",
        "//*[@role='dialog']//input[not(@type='hidden')][@type='text' or @type='number' or @type='search' or not(@type)]",
        "//*[contains(@class,'modal') or contains(@class,'chat')]"
        "//input[not(@type='hidden')][@type='text' or @type='number' or @type='search' or not(@type)]",
        "//*[@role='dialog']//div[@contenteditable='true']",
    ]
    for xp in xps:
        for el in driver.find_elements(By.XPATH, xp):
            try:
                if not el.is_displayed():
                    continue
                _focus_field_like_user(driver, el)
                tag = el.tag_name.lower()
                if tag in ("textarea", "input"):
                    try:
                        el.send_keys(Keys.SPACE)
                        el.send_keys(Keys.BACK_SPACE)
                    except Exception:  # noqa: BLE001
                        pass
                    _notify_input_changed(driver, el)
                else:
                    _notify_input_changed(driver, el)
                time.sleep(0.06)
            except Exception:  # noqa: BLE001
                continue


def _blur_active_input(driver) -> None:
    """Naukri chat often requires blur on the textarea before div.sendMsg accepts clicks."""
    try:
        driver.execute_script(
            """
            var n = document.activeElement;
            if (n && (n.tagName === 'TEXTAREA' || n.tagName === 'INPUT')) {
              n.dispatchEvent(new Event('change', { bubbles: true }));
              n.dispatchEvent(new Event('blur', { bubbles: true }));
              if (n.blur) n.blur();
            }
            """
        )
    except Exception:  # noqa: BLE001
        pass


def _visible_modal_save_buttons(driver):
    """Visible Save controls — Naukri chat uses <div class='sendMsg'>, not <button>."""
    xps = (
        "//*[@role='dialog']//div[contains(@class,'sendMsg')][normalize-space(.)='Save']",
        "//*[@role='dialog']//*[contains(@id,'sendMsg')][normalize-space(.)='Save']",
        "//*[contains(@class,'sendMsgbtn_container')]//div[contains(@class,'sendMsg')][normalize-space(.)='Save']",
        "//*[contains(@class,'modal') or contains(@class,'drawer') or contains(@class,'popup') or contains(@class,'chat')]"
        "//div[contains(@class,'sendMsg')][normalize-space(.)='Save']",
        "//*[contains(@class,'modal') or contains(@class,'drawer') or contains(@class,'popup') or contains(@class,'chat')]"
        "//*[contains(@id,'sendMsg')][normalize-space(.)='Save']",
        "//*[@role='dialog']//button[contains(normalize-space(.),'Save')]",
        "//*[@role='dialog']//button[contains(.,'Save')]",
        "//*[contains(@class,'modal') or contains(@class,'drawer') or contains(@class,'popup') or contains(@class,'chat')]"
        "//button[contains(.,'Save')]",
        "//button[normalize-space(.)='Save']",
        "//button[contains(.,'Save')]",
    )
    out = []
    seen = set()
    for xp in xps:
        for el in driver.find_elements(By.XPATH, xp):
            try:
                if not el.is_displayed():
                    continue
                h = el.size.get("height", 0) if el.size else 0
                if h and h < 4:
                    continue
                key = (el.location.get("x", 0), el.location.get("y", 0), round(h, 1))
                if key in seen:
                    continue
                seen.add(key)
                out.append(el)
            except Exception:  # noqa: BLE001
                continue
    return out


def _find_modal_action_button(driver):
    """Prefer footer Save (last visible); Naukri div.sendMsg first-class; then Submit/Continue."""
    saves = _visible_modal_save_buttons(driver)
    if saves:
        return saves[-1]
    for xp in (
        "//div[contains(@class,'sendMsg')][normalize-space(.)='Save']",
        "//*[contains(@id,'sendMsg')][normalize-space(.)='Save']",
        "//*[@role='dialog']//button[contains(.,'Submit')]",
        "//*[@role='dialog']//button[contains(.,'Continue')]",
        "//*[@role='dialog']//button[contains(.,'Confirm')]",
        "//*[@role='dialog']//button[contains(.,'Done')]",
    ):
        for el in driver.find_elements(By.XPATH, xp):
            try:
                if el.is_displayed():
                    return el
            except Exception:  # noqa: BLE001
                continue
    return None


def _save_button_is_enabled(driver, btn) -> bool:
    """div.sendMsg has no .disabled — check aria + common greyed-out classes."""
    try:
        return bool(
            driver.execute_script(
                """
                var b = arguments[0];
                if (!b) return false;
                if (b.disabled === true) return false;
                if (String(b.getAttribute('aria-disabled')).toLowerCase() === 'true') return false;
                var c = (b.getAttribute('class') || '') + ' ' + (b.className || '');
                if (/\\b(sendMsgDisabled|is-disabled|disabled)\\b/i.test(c)) return false;
                var st = window.getComputedStyle(b);
                if (st && st.pointerEvents === 'none') return false;
                return true;
                """,
                btn,
            )
        )
    except Exception:  # noqa: BLE001
        return True


def _perform_save_click(driver) -> bool:
    """Native click first (trusted), then ActionChains, then JS — re-find each try for staleness."""
    for _ in range(4):
        _blur_active_input(driver)
        time.sleep(0.08)
        btn = _find_modal_action_button(driver)
        if btn is None:
            return False
        try:
            driver.execute_script(
                "arguments[0].scrollIntoView({block:'center', inline:'nearest'});",
                btn,
            )
        except Exception:  # noqa: BLE001
            pass
        time.sleep(0.12)

        btn = _find_modal_action_button(driver)
        if btn is None:
            continue
        for action in (
            lambda b: b.click(),
            lambda b: ActionChains(driver).move_to_element(b).pause(0.08).click().perform(),
            lambda b: driver.execute_script(
                "var n=arguments[0]; if(n&&n.click)n.click();",
                b,
            ),
            lambda b: driver.execute_script(
                "arguments[0].dispatchEvent(new MouseEvent('click',{bubbles:true,cancelable:true,view:window}));",
                b,
            ),
            lambda b: driver.execute_script(
                "var n=arguments[0]; if(n){ n.focus(); "
                "n.dispatchEvent(new KeyboardEvent('keydown',{key:'Enter',code:'Enter',bubbles:true})); "
                "n.dispatchEvent(new KeyboardEvent('keyup',{key:'Enter',code:'Enter',bubbles:true})); }",
                b,
            ),
        ):
            try:
                btn = _find_modal_action_button(driver)
                if btn is None:
                    break
                action(btn)
                time.sleep(0.55)
                return True
            except StaleElementReferenceException:
                break
            except Exception:  # noqa: BLE001
                continue
    return False


def _ensure_save_then_click(driver) -> bool:
    """
    After answers: if Save stays disabled, nudge text fields (click + space) and retry.
    Clicks use native/Actions/JS with re-find. From round 2 onward we always try click too,
    since Naukri sometimes enables Save without clearing disabled-like classes in the DOM.
    """
    attempts = max(1, config.SAVE_NUDGE_ATTEMPTS)
    for i in range(attempts):
        btn = _find_modal_action_button(driver)
        if btn is None:
            return False
        looks_enabled = _save_button_is_enabled(driver, btn)
        if looks_enabled or i > 0:
            if _perform_save_click(driver):
                time.sleep(0.35)
                return True
        _nudge_modal_text_fields(driver)
        time.sleep(0.14)

    btn = _find_modal_action_button(driver)
    if btn is not None and _perform_save_click(driver):
        time.sleep(0.35)
        return True
    return False


def _modal_pass_in_current_context(driver) -> bool:
    """Choices (Skip checkbox / Yes radio), LWD + experience inline, chat + salary, then Save with retries."""
    q = _dialog_text_blobs(driver)
    _handle_modal_choice_controls(driver, q)
    _fill_popup_identity_fields(driver)
    _try_fill_lwd_inline_from_blob(driver, q)
    _try_fill_experience_from_blob(driver, q)

    msg_el = _find_type_message_field(driver)
    if msg_el is not None:
        reply = _choose_reply_for_question(q)
        if not (reply or "").strip():
            if _click_modal_header_skip(driver):
                time.sleep(0.18)
            else:
                reply = (config.GENERIC_POPUP_REPLY or "").strip() or _random_fallback_reply()
                try:
                    _type_into_field(driver, msg_el, reply)
                except Exception:  # noqa: BLE001
                    return False
        else:
            try:
                _type_into_field(driver, msg_el, reply)
            except Exception:  # noqa: BLE001
                return False

    _click_checkbox_skip_targets(driver, q)
    try:
        _click_yes_radios_in_apply_popup(driver)
    except Exception:  # noqa: BLE001
        pass
    _handle_unknown_screening_questions(driver, q)
    _fill_apply_modal_in_current_context(driver)
    time.sleep(0.2)

    clicked = _ensure_save_then_click(driver)
    time.sleep(0.35)
    return clicked


def _try_send_keys_first(driver, xpaths, text: str) -> bool:
    if not text:
        return False
    raw = str(text)
    for xp in xpaths:
        for el in driver.find_elements(By.XPATH, xp):
            try:
                if not el.is_displayed():
                    continue
                _focus_field_like_user(driver, el)
                el.clear()
                el.send_keys(raw)
                try:
                    el.send_keys(Keys.SPACE)
                    el.send_keys(Keys.BACK_SPACE)
                except Exception:  # noqa: BLE001
                    pass
                _notify_input_changed(driver, el)
                time.sleep(0.1)
                return True
            except Exception:  # noqa: BLE001
                continue
    return False


def _click_modal_submit(driver) -> bool:
    """Prefer enabled Save after nudges; same as _ensure_save_then_click."""
    return _ensure_save_then_click(driver)


def _fill_popup_identity_fields(driver) -> bool:
    """Email / phone / DD/MM (or similar) in apply screening popups — values from env."""
    filled = False
    if config.POPUP_EMAIL and _try_send_keys_first(
        driver,
        [
            "//*[@role='dialog']//input[@type='email']",
            "//*[contains(@class,'modal') or contains(@class,'drawer') or contains(@class,'chat') or contains(@class,'popup')]"
            "//input[@type='email']",
            "//input[@type='email']",
            "//*[@role='dialog']//input[contains(translate(@placeholder,'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'mail')]",
            "//*[@role='dialog']//input[contains(translate(@placeholder,'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'email')]",
            "//label[contains(translate(.,'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'email')]/following::input[1]",
            "//label[contains(translate(.,'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'mail')]/following::input[1]",
            "//input[contains(translate(@name,'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'email')]",
        ],
        config.POPUP_EMAIL,
    ):
        filled = True

    if config.POPUP_PHONE and _try_send_keys_first(
        driver,
        [
            "//*[@role='dialog']//input[@type='tel']",
            "//*[contains(@class,'modal') or contains(@class,'drawer') or contains(@class,'chat') or contains(@class,'popup')]"
            "//input[@type='tel']",
            "//*[@role='dialog']//input[contains(translate(@placeholder,'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'mobile')]",
            "//*[@role='dialog']//input[contains(translate(@placeholder,'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'phone')]",
            "//*[@role='dialog']//input[contains(translate(@placeholder,'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'contact')]",
            "//label[contains(translate(.,'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'mobile')]/following::input[1]",
            "//label[contains(translate(.,'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'phone')]/following::input[1]",
            "//input[contains(translate(@name,'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'phone')]",
            "//input[contains(translate(@name,'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'mobile')]",
        ],
        config.POPUP_PHONE,
    ):
        filled = True

    if config.POPUP_DATE_DDMM and _try_send_keys_first(
        driver,
        [
            "//*[@role='dialog']//input[contains(translate(@placeholder,'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'dd')]",
            "//*[@role='dialog']//input[contains(translate(@placeholder,'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'mm')]",
            "//*[@role='dialog']//input[contains(translate(@placeholder,'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'yy')]",
            "//*[@role='dialog']//input[contains(translate(@placeholder,'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'dob')]",
            "//*[@role='dialog']//input[contains(translate(@placeholder,'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'birth')]",
            "//*[@role='dialog']//input[contains(translate(@placeholder,'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'date')]",
            "//label[contains(translate(.,'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'birth')]/following::input[1]",
            "//label[contains(translate(.,'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'dob')]/following::input[1]",
            "//*[contains(@class,'modal')]//input[contains(translate(@placeholder,'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'dd/mm')]",
        ],
        config.POPUP_DATE_DDMM,
    ):
        filled = True

    return filled


def _fill_apply_modal_in_current_context(driver) -> bool:
    filled = False
    if _fill_popup_identity_fields(driver):
        filled = True
    if config.APPLY_YEARS and _try_send_keys_first(
        driver,
        [
            "//input[contains(@placeholder,'Experience') or contains(@placeholder,'experience')]",
            "//input[contains(@name,'experience') or contains(@name,'Experience')]",
            "//input[contains(@id,'experience') or contains(@id,'Experience')]",
            "//label[contains(.,'Experience')]/following::input[1]",
        ],
        config.APPLY_YEARS,
    ):
        filled = True

    if config.EXPECTED_SALARY and _try_send_keys_first(
        driver,
        [
            "//input[contains(@placeholder,'Expected') or contains(@placeholder,'expected')]",
            "//input[contains(@name,'expected') or contains(@name,'Expected')]",
            "//label[contains(.,'Expected')]/following::input[1]",
        ],
        config.EXPECTED_SALARY,
    ):
        filled = True

    if config.CURRENT_SALARY and _try_send_keys_first(
        driver,
        [
            "//input[contains(@placeholder,'Current') or contains(@placeholder,'current')]",
            "//input[contains(@name,'current') or contains(@name,'Current')]",
            "//label[contains(.,'Current')]/following::input[1]",
        ],
        config.CURRENT_SALARY,
    ):
        filled = True

    if config.NOTICE and _try_send_keys_first(
        driver,
        [
            "//input[contains(@placeholder,'Notice') or contains(@placeholder,'notice')]",
            "//input[contains(@name,'notice') or contains(@name,'Notice')]",
            "//label[contains(.,'Notice')]/following::input[1]",
            "//textarea[contains(@placeholder,'Notice')]",
        ],
        config.NOTICE,
    ):
        filled = True

    return filled


def handle_apply_modal(driver) -> bool:
    """
    Post-Apply popups (LWD / notice / skills chat, salary forms).
    Bounded rounds + time budget to avoid infinite loops.
    Unknown questions: fill NAUKRI_GENERIC_POPUP_REPLY or random NO/0/N/A, Save, then dismiss if stuck.
    Returns True if no blocking popup remains (best-effort).
    """
    time.sleep(0.6)
    t0 = time.time()
    rounds = 0
    stagnant = 0

    while rounds < config.MODAL_MAX_ROUNDS and (time.time() - t0) < config.MODAL_MAX_SECONDS:
        rounds += 1
        progressed = False
        driver.switch_to.default_content()

        progressed |= _modal_pass_in_current_context(driver)

        for fr in driver.find_elements(By.TAG_NAME, "iframe"):
            try:
                driver.switch_to.default_content()
                driver.switch_to.frame(fr)
                progressed |= _modal_pass_in_current_context(driver)
            except Exception:  # noqa: BLE001
                pass
            finally:
                driver.switch_to.default_content()

        now_visible = _popup_still_visible(driver)
        if not now_visible:
            log_info("Batch apply: post-apply popup cleared")
            driver.switch_to.default_content()
            return True

        if progressed:
            stagnant = 0
            log_info("Batch apply: modal step progressed")
        else:
            stagnant += 1

        if stagnant >= 2:
            if _try_dismiss_any_overlay(driver):
                log_info("Batch apply: dismissed popup after no progress (close/skip)")
                stagnant = 0
            else:
                log_info("Batch apply: popup stuck — stopping modal loop")
                break

        time.sleep(0.35)

    driver.switch_to.default_content()
    if _popup_still_visible(driver):
        _try_dismiss_any_overlay(driver)
        log_info("Batch apply: final dismiss attempt after modal handling")

    driver.switch_to.default_content()
    still = _popup_still_visible(driver)
    if still:
        log_info("Batch apply: warning — popup may still be visible; continuing run")
    return not still


