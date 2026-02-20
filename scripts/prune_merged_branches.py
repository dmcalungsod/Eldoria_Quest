import json
import subprocess
import sys
from datetime import datetime, timezone, timedelta

def run_command(command_list):
    try:
        # Use shell=False and pass list for safety
        result = subprocess.run(
            command_list,
            capture_output=True,
            text=True,
            check=True
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        # Avoid printing full command if it contains secrets (though here it's just branch names)
        # But for debugging, print stderr
        print(f"Error running command: {e.stderr}")
        return None

def main():
    days_threshold = 3
    cutoff_date = datetime.now(timezone.utc) - timedelta(days=days_threshold)
    print(f"Pruning merged branches older than {cutoff_date.isoformat()}...")

    # Get current repository
    current_repo_json = run_command(["gh", "repo", "view", "--json", "nameWithOwner"])
    if not current_repo_json:
        sys.exit(1)

    current_repo = json.loads(current_repo_json).get("nameWithOwner")
    if not current_repo:
        print("Could not determine current repository.")
        sys.exit(1)

    # Get merged PRs (limit 100 should be sufficient for regular cleanup)
    # We fetch enough fields to determine branch and merge time.
    prs_json = run_command(
        ["gh", "pr", "list", "--state", "merged", "--json", "number,headRefName,mergedAt,headRepository", "--limit", "100"]
    )

    if not prs_json:
        print("No merged PRs found or error fetching them.")
        return

    prs = json.loads(prs_json)

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
        branch_check = subprocess.run(
            ["gh", "api", f"repos/{current_repo}/branches/{head_ref}", "--silent"],
            capture_output=True
        )

        if branch_check.returncode != 0:
            # Branch likely already deleted
            continue

        print(f"Deleting branch '{head_ref}' (merged {merged_at_str})...")

        # Delete the branch
        delete_cmd = ["gh", "api", "--method", "DELETE", f"repos/{current_repo}/git/refs/heads/{head_ref}"]
        delete_result = subprocess.run(
            delete_cmd,
            capture_output=True,
            text=True
        )

        if delete_result.returncode == 0:
            print(f"Successfully deleted branch '{head_ref}'.")
        else:
            print(f"Failed to delete branch '{head_ref}': {delete_result.stderr.strip()}")

if __name__ == "__main__":
    main()
