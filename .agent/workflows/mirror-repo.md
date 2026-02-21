---
description: How to set up and maintain the Mirror Repo GitHub Actions workflow
---

# Mirror Repo Workflow

This workflow automatically mirrors every push (all branches) from the primary repo to a secondary GitHub account's repo (`DeeEmSea/Eldoria-Quest-Bot`). This enables using a separate Render free tier account.

## How It Works

The workflow file is at `.github/workflows/mirror.yml`. On every push to any branch, it:

1. Checks out the full repo history (`fetch-depth: 0`).
2. Runs `git push --mirror` to the mirror repo using a Personal Access Token stored in `MIRROR_TOKEN`.

## Setup Steps (One-Time)

### 1. Create the mirror repo on the secondary account

- Log into the secondary GitHub account (`DeeEmSea`).
- Create a new **empty** repository named `Eldoria-Quest-Bot` (no README, no .gitignore, no license).

### 2. Generate a Personal Access Token (PAT) on the secondary account

- Go to **Settings → Developer Settings → Personal Access Tokens → Fine-grained tokens** (or classic).
- Create a new token with `repo` (full control) scope.
- Copy the token.

### 3. Add the token as a secret in the primary repo

- Go to the **primary** repo (`dmcalungsod/Eldoria_Quest`) on GitHub.
- Navigate to **Settings → Secrets and variables → Actions → New repository secret**.
- Name: `MIRROR_TOKEN`
- Value: the PAT you generated in step 2.

### 4. Push any change to trigger the workflow

- The mirror workflow runs automatically on every push to any branch.
- Check the **Actions** tab on the primary repo to verify it ran successfully.

## Troubleshooting

| Issue | Fix |
|-------|-----|
| `403 Forbidden` | The PAT is missing `repo` scope or has expired. Regenerate it. |
| `404 Not Found` | The mirror repo doesn't exist yet, or the name is misspelled. |
| `rejected (non-fast-forward)` | The mirror repo has commits not in the source. Delete and recreate the mirror repo as empty. |
| Workflow not triggering | Ensure the `.github/workflows/mirror.yml` file is on the default branch. |

## Updating the Mirror Target

If you need to change the mirror destination, edit `.github/workflows/mirror.yml` and update the URL in the `git push --mirror` command.
