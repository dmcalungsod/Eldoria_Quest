## 🤖 Copilot — CI/CD Workflow Additions Log

**Date:** 2026-02-24
**PR:** [#345 — Add 5 GitHub Actions workflows](https://github.com/dmcalungsod/Eldoria_Quest/pull/345)
**Branch:** `copilot/add-github-actions-workflows`

---

### ✅ Workflows Added

| Workflow | File | Purpose | Trigger |
|---|---|---|---|
| **Dependency Review** | `.github/workflows/dependency-review.yml` | Blocks PRs with moderate+ severity dependency vulnerabilities; posts summary comment | `pull_request` → `main`, `master` |
| **Stale Issues & PRs** | `.github/workflows/stale.yml` | Marks issues/PRs stale after 30 days, closes after 7 more | `schedule` (daily 1 AM UTC), `workflow_dispatch` |
| **Release** | `.github/workflows/release.yml` | Auto-creates GitHub releases with generated changelogs on `v*.*.*` tags | `push` tags matching `v*.*.*` |
| **CodeQL Analysis** | `.github/workflows/codeql.yml` | Python static security analysis | `push`/`pull_request` → `main`/`master`; `schedule` (Mon 2 AM UTC) |
| **Coverage Report** | `.github/workflows/coverage-comment.yml` | Runs pytest + coverage against live MongoDB, posts coverage report as PR comment | `pull_request` → `main`, `master` |

---

### 🐛 Issues Encountered & Fixes

#### 1. Dependency Review — GitHub Advanced Security Required
- **Error:** `Dependency review is not supported on this repository. Please ensure that Dependency graph is enabled along with GitHub Advanced Security.`
- **Root Cause:** `actions/dependency-review-action@v4` requires GitHub Advanced Security (GHAS) + Dependency Graph to be enabled on the repository.
- **Fix Applied (PR #347):** Replaced the action with a lightweight pip-audit based alternative that does not require GHAS.
- **Settings Link:** https://github.com/dmcalungsod/Eldoria_Quest/settings/security_analysis

#### 2. CodeQL — Missing `actions: read` Permission
- **Error:** `codeql-action/analyze` requires access to the workflow run context.
- **Fix Applied (commit `e845c80`):** Added `actions: read` permission to the CodeQL workflow's permissions block.

---

### 📝 Notes
- Existing workflows (`ci.yml`, `automerge.yml`, `mirror.yml`) were **not modified**.
- The `coverage-comment.yml` workflow spins up a real `mongo:5.0` service container for integration-style tests.
- The `stale.yml` workflow is configured for **30 days to stale, 7 days to close** — adjust thresholds in `.github/workflows/stale.yml` if needed.
- The `release.yml` workflow uses `softprops/action-gh-release@v2` with `generate_release_notes: true`; tag with `vX.Y.Z` to trigger a release.