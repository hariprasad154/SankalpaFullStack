"""Centralized XPath/CSS selectors for Naukri UI."""

# Login
LOGIN_BTN_CLASS = "nI-gNb-lg-rg__login"
LOGIN_BTN_XPATHS = (
    "//a[normalize-space()='Login']",
    "//button[contains(normalize-space(.),'Login')]",
)
EMAIL_INPUT_XPATH = (
    "//input[@placeholder='Enter your active Email ID / Username' "
    "or contains(@placeholder,'Email')]"
)
PASSWORD_INPUT_XPATH = (
    "//input[@type='password' and (contains(@placeholder,'password') "
    "or contains(@placeholder,'Password'))]"
)
SUBMIT_BTN_XPATH = "//button[@type='submit']"

# Recommended page / apply
APPLY_PAGE_WAIT_XPATH = (
    "//button[contains(.,'Apply')]"
    "|//*[contains(.,'Recommended')]"
    "|//*[contains(.,'recommended')]"
)
APPLY_BUTTON_XPATHS = (
    "//button[contains(translate(normalize-space(.),'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'apply')]"
    "[contains(translate(.,'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'job')]",
    "//button[contains(.,'Apply') and contains(.,'Job')]",
    "//a[contains(.,'Apply') and contains(.,'Job')]",
    "//button[contains(normalize-space(.),'Apply')]",
    "//button[contains(.,'Apply')]",
)

JOB_TOGGLE_SCOPED_XPATHS = (
    "//div[contains(@class,'jobTuple')]//*[self::input[@type='checkbox'] | self::i[contains(@class,'naukicon-ot-checkbox')] | self::i[contains(@class,'ot-checkbox')]]",
    "//div[contains(@class,'cust-tuple')]//*[self::input[@type='checkbox'] | self::i[contains(@class,'naukicon-ot-checkbox')]]",
    "//*[contains(@class,'srp-jobtuple')]//input[@type='checkbox']",
    "//*[contains(translate(@class,'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'jobtuple')]//input[@type='checkbox']",
)
CHECKBOX_INPUT_XPATH = "//input[@type='checkbox']"
RADIO_INPUT_XPATH = "//input[@type='radio']"

# Feed tabs
TAB_LIST_ITEM_XPATH = "//div[contains(@class,'tab-list-item')]"
ROLE_TAB_XPATH = "//*[@role='tab']"

# Dialog / modal
DIALOG_TEXT_XPATHS = (
    "//*[@role='dialog']//*",
    "//*[contains(@class,'chat')]",
    "//*[contains(@class,'modal')]",
    "//*[contains(@class,'drawer')]",
    "//*[contains(@class,'popup')]",
)
TYPE_MESSAGE_XPATHS = (
    "//textarea[contains(translate(@placeholder,'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'type message here')]",
    "//textarea[contains(@placeholder,'Type message')]",
    "//input[contains(@placeholder,'Type message')]",
    "//input[contains(translate(@placeholder,'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'type message')]",
)
CONTENTEDITABLE_XPATH = "//div[@contenteditable='true']"

POPUP_VISIBLE_MARKERS = (
    "//textarea[contains(translate(@placeholder,'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'type message')]",
    "//*[contains(translate(.,'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'mention lwd')]",
    "//*[contains(translate(.,'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'serving notice')]",
    "//*[@role='dialog']//button[contains(normalize-space(.),'Save')]",
    "//div[contains(@class,'sendMsg')][normalize-space(.)='Save']",
    "//*[contains(@id,'sendMsg')][normalize-space(.)='Save']",
)

DISMISS_OVERLAY_XPATHS = (
    "//button[normalize-space()='×']",
    "//*[@aria-label='Close']",
    "//button[contains(@aria-label,'Close')]",
    "//*[contains(@class,'closeIcon')]",
    "//button[contains(@class,'close')]",
    "//button[contains(.,'Skip')][not(ancestor::*[@role='dialog'])]",
    "//button[contains(.,'Cancel')]",
)

SKIP_QUESTION_XPATHS = (
    "//label[contains(translate(.,'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'skip this question')][not(.//input[@type='radio'])]",
    "//*[@role='dialog']//label[contains(translate(.,'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'skip this question')][not(.//input[@type='radio'])]",
    "//span[contains(translate(.,'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'skip this question')]",
)

MODAL_HEADER_SKIP_XPATHS = (
    "//*[@role='dialog']//*[self::button or self::a][normalize-space(.)='Skip']",
    "//*[contains(@class,'modal') or contains(@class,'drawer') or contains(@class,'chat')]"
    "//*[self::button or self::a][normalize-space(.)='Skip'][not(contains(.,'question'))]",
)

MODAL_CHECKBOX_XPATHS = (
    "//*[@role='dialog']//input[@type='checkbox']",
    "//*[contains(@class,'modal') or contains(@class,'drawer') or contains(@class,'chat') or contains(@class,'popup')]"
    "//input[@type='checkbox']",
)
