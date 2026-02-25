"""
scripts/validate_logs.py

Scans `.Jules/agent_logs/` to ensure no files are dated in the future relative to GMT+8.
Exits with 1 if any future logs are found.
"""

import datetime
import os
import re
import sys

LOGS_DIR = ".Jules/agent_logs"


def get_current_date_gmt8():
    """Returns the current date in GMT+8."""
    # Simple timezone offset: UTC + 8 hours
    utc_now = datetime.datetime.utcnow()
    gmt8_now = utc_now + datetime.timedelta(hours=8)
    return gmt8_now.date()


def main():
    current_date = get_current_date_gmt8()
    print(f"📅  Validating logs against GMT+8 Date: {current_date}")

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
