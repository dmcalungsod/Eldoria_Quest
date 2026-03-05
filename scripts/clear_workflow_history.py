import os
from concurrent.futures import ThreadPoolExecutor, as_completed

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
    total_deleted = 0

    while True:
        print(f"Fetching up to 100 workflow runs for {REPO_OWNER}/{REPO_NAME}...")

        url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/actions/runs?per_page=100"
        response = requests.get(url, headers=headers)

        if response.status_code != 200:
            print(f"Error fetching runs: {response.json()}")
            break

        all_runs = response.json().get("workflow_runs", [])

        if not all_runs:
            print("No more workflow runs found! Your Actions history is perfectly clean.")
            break

        print(f"Found a batch of {len(all_runs)} workflow runs. Deleting them concurrently...")

        def delete_run(run_id):
            delete_url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/actions/runs/{run_id}"
            del_response = requests.delete(delete_url, headers=headers)
            if del_response.status_code == 204:
                return True
            else:
                print(f"Failed to delete run ID: {run_id} - {del_response.status_code} - {del_response.text}")
                return False

        batch_deleted = 0
        # Use max_workers=10 to avoid hitting GitHub API secondary rate limits
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(delete_run, run["id"]) for run in all_runs]
            for future in as_completed(futures):
                if future.result():
                    batch_deleted += 1

        total_deleted += batch_deleted
        print(f"Batch complete. Deleted {batch_deleted} runs in this batch.")

    print(f"\nDone! Successfully wiped a total of {total_deleted} workflow runs.")


if __name__ == "__main__":
    delete_all_runs()
