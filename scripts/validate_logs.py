"""
scripts/validate_logs.py

Scans `.Jules/agent_logs/` to ensure no files are dated in the future relative to GMT+8 (Asia/Manila).
Exits with 1 if any future logs are found.
"""

import datetime
import os
import re
import sys
from zoneinfo import ZoneInfo

LOGS_DIR = ".Jules/agent_logs"


def get_current_date_manila():
    """Returns the current date in Asia/Manila (UTC+8)."""
    manila_tz = ZoneInfo("Asia/Manila")
    # datetime.now(tz) returns a timezone-aware datetime
    return datetime.datetime.now(manila_tz).date()


def main():
    current_date = get_current_date_manila()
    print(f"📅  Validating logs against Asia/Manila Date: {current_date}")

    # Check if logs directory exists
    if not os.path.exists(LOGS_DIR):
        print(f"⚠️  Logs directory not found: {LOGS_DIR}")
        return

    future_files = []

    for filename in os.listdir(LOGS_DIR):
        # Match YYYY-MM-DD pattern at start of filename
        match = re.match(r"^(\d{4}-\d{2}-\d{2})", filename)
        if match:
            date_str = match.group(1)
            try:
                log_date = datetime.datetime.strptime(date_str, "%Y-%m-%d").date()
                if log_date > current_date:
                    future_files.append(filename)
            except ValueError:
                continue

    if future_files:
        print("❌  Future-dated logs found:")
        for f in future_files:
            print(f"  - {f}")
        print("Validation FAILED.")
        sys.exit(1)
    else:
        print("✅  All log timestamps are valid.")


if __name__ == "__main__":
    main()
