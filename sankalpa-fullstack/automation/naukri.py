"""
Backward-compatible Naukri login module.

Prefer: python main.py naukri
Implementation: naukri.login, core.browser
"""
from core.browser import start_driver
from naukri.login import credentials_ok as _credentials_ok
from naukri.login import login_naukri, run_naukri_login

__all__ = ["start_driver", "login_naukri", "run_naukri_login", "_credentials_ok"]
