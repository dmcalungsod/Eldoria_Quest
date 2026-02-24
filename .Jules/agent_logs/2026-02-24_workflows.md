## 🤖 Copilot — CI/CD Workflow Additions Log

**Date:** 2026-02-24 06:30:18
**PR:** [#345 — Add 5 GitHub Actions workflows](https://github.com/dmcalungsod/Eldoria_Quest/pull/345)
**Branch:** `copilot/add-github-actions-workflows`

---

### ✅ Workflows Added (PR #345)

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
- **Fix Applied (PR #347):** Patched the workflow to avoid hard-failing when GHAS is unavailable.
- **Settings Link:** https://github.com/dmcalungsod/Eldoria_Quest/settings/security_analysis

#### 2. CodeQL — Missing `actions: read` Permission
- **Error:** `codeql-action/analyze` requires access to the workflow run context.
- **Fix Applied (commit `e845c80`):** Added `actions: read` permission to the CodeQL workflow's permissions block.

#### 3. CodeQL — Not Supported on Private Repos Without GHAS ⚠️ REMOVED
- **Error:** `codeql-action` requires GitHub Advanced Security, which is not active on this private repository.
- **Fix Applied (PR #348):** `codeql.yml` was **removed entirely**. CodeQL requires GHAS on private repositories.

---

### 📋 All PRs Merged Today (CI/CD Related)

| PR | Title | Status |
|----|-------|--------|
| [#345](https://github.com/dmcalungsod/Eldoria_Quest/pull/345) | Add 5 GitHub Actions workflows: dependency review, stale, release, CodeQL, coverage | ✅ Merged |
| [#347](https://github.com/dmcalungsod/Eldoria_Quest/pull/347) | Fix dependency-review and coverage-comment workflow failures | ✅ Merged |
| [#348](https://github.com/dmcalungsod/Eldoria_Quest/pull/348) | remove(codeql): not supported on private repos without GitHub Advanced Security | ✅ Merged |
| [#350](https://github.com/dmcalungsod/Eldoria_Quest/pull/350) | Fix auto-merge workflow to handle draft PRs correctly | ✅ Merged |
| [#351](https://github.com/dmcalungsod/Eldoria_Quest/pull/351) | ci: consolidate coverage reporting, add CVE audit, PR labeler, and tighten workflow permissions | ✅ Merged |

---

### 📋 Final CI/CD State (End of Day)

| Workflow | File | Status |
|---|---|---|
| Dependency Review | `dependency-review.yml` | ✅ Active (patched, non-blocking without GHAS) |
| Stale Issues & PRs | `stale.yml` | ✅ Active |
| Release | `release.yml` | ✅ Active |
| CodeQL Analysis | `codeql.yml` | ❌ Removed (requires GHAS on private repos) |
| Coverage Report | `coverage-comment.yml` | ✅ Active (patched) |
| CVE Audit | added via PR #351 | ✅ Active |
| PR Labeler | added via PR #351 | ✅ Active |

---

### 📝 Notes
- Existing workflows (`ci.yml`, `automerge.yml`, `mirror.yml`) were **not modified**.
- The `coverage-comment.yml` workflow spins up a real `mongo:5.0` service container for integration-style tests.
- The `stale.yml` workflow is configured for **30 days to stale, 7 days to close** — adjust thresholds in `.github/workflows/stale.yml` if needed.
- The `release.yml` workflow uses `softprops/action-gh-release@v2` with `generate_release_notes: true`; tag with `vX.Y.Z` to trigger a release.
- PR #351 also tightened permissions across all workflows to follow least-privilege principles.