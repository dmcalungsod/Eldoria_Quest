import os

import requests
from dotenv import load_dotenv

load_dotenv()

# 1. Enter your repository owner and name here
REPO_OWNER = "dmcalungsod"
REPO_NAME = "Eldoria_Quest"

# 2. Enter your Fine-grained Personal Access Token here
# Make sure it has "Read and Write" access to Actions variables and workflows!
GITHUB_TOKEN = os.environ.get("PAT")

headers = {
    "Accept": "application/vnd.github+json",
    "Authorization": f"Bearer {GITHUB_TOKEN}",
    "X-GitHub-Api-Version": "2022-11-28",
}


def delete_all_runs():
    print(f"Fetching workflow runs for {REPO_OWNER}/{REPO_NAME}...")

    # Get all workflow runs
    url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/actions/runs"
    response = requests.get(url, headers=headers)

    if response.status_code != 200:
        print(f"Error fetching runs: {response.json()}")
        return

    runs = response.json().get("workflow_runs", [])

    if not runs:
        print("No workflow runs found! Your Actions history is already perfectly clean.")
        return

    print(f"Found {len(runs)} workflow runs. Deleting them now...")

    deleted_count = 0
    for run in runs:
        run_id = run["id"]
        delete_url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/actions/runs/{run_id}"

        del_response = requests.delete(delete_url, headers=headers)

        if del_response.status_code == 204:
            print(f"Successfully deleted run ID: {run_id}")
            deleted_count += 1
        else:
            print(f"Failed to delete run ID: {run_id} - {del_response.json()}")

    print(f"\nDone! Successfully wiped {deleted_count} workflow runs.")


if __name__ == "__main__":
    delete_all_runs()
