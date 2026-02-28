import json
import os
import subprocess
import sys
from datetime import datetime, timedelta, timezone


def log_summary(message):
    summary_file = os.environ.get("GITHUB_STEP_SUMMARY")
    if summary_file:
        with open(summary_file, "a") as f:
            f.write(message + "\n")


def main():
    log_summary("### 🧹 Branch Pruning Report")

    # Set retention period (20 hours) to allow recent branches to persist for a bit
    hours_threshold = 20
    cutoff_date = datetime.now(timezone.utc) - timedelta(hours=hours_threshold)
    print(f"Pruning merged branches older than {cutoff_date.isoformat()} ({hours_threshold} hours retention)...")

    # Get current repository
    try:
        result = subprocess.run(
            ["gh", "repo", "view", "--json", "nameWithOwner"],
            capture_output=True,
            text=True,
            check=True
        )  # nosec B603
        current_repo_json = result.stdout.strip()
    except subprocess.CalledProcessError as e:
        print(f"Error running command: {e.stderr}")
        sys.exit(1)

    if not current_repo_json:
        sys.exit(1)

    current_repo = json.loads(current_repo_json).get("nameWithOwner")
    if not current_repo:
        print("Could not determine current repository.")
        sys.exit(1)

    # Get merged PRs (limit 1000 to catch older branches that might have been missed)
    # We fetch enough fields to determine branch and merge time.
    try:
        prs_result = subprocess.run(
            [
                "gh",
                "pr",
                "list",
                "--state",
                "merged",
                "--json",
                "number,headRefName,mergedAt,headRepository",
                "--limit",
                "1000",
            ],
            capture_output=True,
            text=True,
            check=True
        )  # nosec B603
        prs_json = prs_result.stdout.strip()
    except subprocess.CalledProcessError as e:
        print(f"Error running command: {e.stderr}")
        print("No merged PRs found or error fetching them.")
        return

    if not prs_json:
        print("No merged PRs found or error fetching them.")
        return

    prs = json.loads(prs_json)
    print(f"Found {len(prs)} merged PRs to check.")

    deleted_count = 0

    for pr in prs:
        pr_number = pr.get("number")
        head_ref = pr.get("headRefName")
        merged_at_str = pr.get("mergedAt")
        head_repo = pr.get("headRepository")

        if not head_ref or not merged_at_str:
            continue

        # Parse merge date (ISO 8601)
        try:
            # Handle Z suffix for UTC
            if merged_at_str.endswith("Z"):
                merged_at_str = merged_at_str[:-1] + "+00:00"
            merged_at = datetime.fromisoformat(merged_at_str)
        except ValueError:
            print(f"Skipping PR #{pr_number}: Invalid date format {merged_at_str}")
            continue

        # Check if old enough
        if merged_at > cutoff_date:
            print(f"Skipping PR #{pr_number} ({head_ref}): Merged at {merged_at} is newer than cutoff {cutoff_date}")
            continue

        # Check if it's from the same repository (not a fork)
        if not head_repo or head_repo.get("nameWithOwner") != current_repo:
            # Only log if verbose needed, otherwise silent skip for forks
            continue

        # Check if protected branch (main/master)
        if head_ref in ["main", "master"]:
            print(f"Skipping PR #{pr_number}: Protected branch '{head_ref}'")
            continue

        # Check if branch still exists
        branch_check = subprocess.run(  # nosec B603
            ["gh", "api", f"repos/{current_repo}/branches/{head_ref}", "--silent"],
            capture_output=True,
        )

        if branch_check.returncode != 0:
            # Branch likely already deleted
            continue

        print(f"Deleting branch '{head_ref}' (merged {merged_at_str})...")

        # Delete the branch
        delete_result = subprocess.run(
            [
                "gh",
                "api",
                "--method",
                "DELETE",
                f"repos/{current_repo}/git/refs/heads/{head_ref}",
            ],
            capture_output=True,
            text=True
        )  # nosec B603

        if delete_result.returncode == 0:
            print(f"Successfully deleted branch '{head_ref}'.")
            log_summary(f"- ✅ Deleted branch `{head_ref}` (merged {merged_at_str})")
            deleted_count += 1
        else:
            error_msg = delete_result.stderr.strip()
            print(f"Failed to delete branch '{head_ref}': {error_msg}")
            log_summary(f"- ❌ Failed to delete branch `{head_ref}`: {error_msg}")

    if deleted_count == 0:
        log_summary("No branches were pruned.")
    else:
        log_summary(f"\n**Total branches pruned:** {deleted_count}")


if __name__ == "__main__":
    main()
