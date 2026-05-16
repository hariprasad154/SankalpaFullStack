"""
Backward-compatible entry for batch apply.

Prefer: python main.py batch
Implementation: naukri.apply_engine
"""
from naukri.apply_engine import run_batch_flow, run_naukri_batch_flow

__all__ = ["run_batch_flow", "run_naukri_batch_flow"]

if __name__ == "__main__":
    run_naukri_batch_flow()
