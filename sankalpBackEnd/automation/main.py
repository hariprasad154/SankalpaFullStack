"""
Automation entrypoint for sankalpa-fullstack.

  python main.py ingest   — JSON file loop (../data/jobs.json, logs.json)
  python main.py naukri   — Chrome + Naukri login only (mark2)
  python main.py flow     — Mark3: recommended page + tabs + scrape to JSON
  python main.py batch   — autoApply.txt: batch checkbox Apply on recommended page
  python main.py          — AUTOMATION_MODE: ingest | naukri | flow | batch

Requires cwd = automation/.
"""
import os
import sys

from dotenv import load_dotenv

load_dotenv()


def _print_usage() -> None:
    print(
        "Sankalpa automation\n"
        "  python main.py ingest   — file-based job/log loop\n"
        "  python main.py naukri   — Chrome + Naukri login (hold, then close)\n"
        "  python main.py flow     — Mark3: recommended jobs + tabs + JSON\n"
        "  python main.py batch    — batch Apply (5 checkboxes per batch, configurable)\n"
        "  python main.py          — AUTOMATION_MODE: ingest | naukri | flow | batch\n"
    )


def main() -> None:
    arg = sys.argv[1].lower() if len(sys.argv) > 1 else None
    env_mode = os.getenv("AUTOMATION_MODE", "ingest").lower().strip()

    if arg in ("-h", "--help", "help"):
        _print_usage()
        return

    if arg == "naukri":
        from naukri import run_naukri_login

        run_naukri_login()
        return

    if arg == "flow":
        from naukri_flow import run_mark3_flow

        run_mark3_flow()
        return

    if arg == "batch":
        from naukri.apply_engine import run_naukri_batch_flow

        run_naukri_batch_flow()
        return

    if arg == "ingest":
        from ingest_loop import run_forever

        run_forever()
        return

    if arg is not None and arg not in ("ingest", "naukri", "flow", "batch"):
        print(f"Unknown command: {sys.argv[1]!r}\n")
        _print_usage()
        sys.exit(2)

    if env_mode == "naukri":
        from naukri import run_naukri_login

        run_naukri_login()
        return

    if env_mode == "flow":
        from naukri_flow import run_mark3_flow

        run_mark3_flow()
        return

    if env_mode == "batch":
        from naukri.apply_engine import run_naukri_batch_flow

        run_naukri_batch_flow()
        return

    from ingest_loop import run_forever

    run_forever()


if __name__ == "__main__":
    main()
