# 🔍 Eldoria Quest Codebase Audit — 2026-03-05

**Auditor:** Repo Auditor
**Scope:** Entire repository
**Tools Used:** flake8, bandit, vulture, radon, safety, manual review

## Executive Summary
Comprehensive codebase audit completed successfully. Found a number of security, performance, and UI consistency issues. Overall code health is stable but requires targeted cleanups.

## 🚨 Critical Issues (Fix Immediately)
None found in this scan.

## ⚠️ High Priority Issues

## 🔸 Medium Priority Issues

- **Issue**: Security Warning [B110:try_except_pass] Try, Except, Pass detected.
  **Location**: `./game_systems/adventure/ui/adventure_embeds.py:248:8`
  **Risk**: Low to medium security risk.
  **Suggested Agent**: Sentinel
  **Recommendation**: Review and mitigate if necessary.

- **Issue**: Security Warning [B113:request_without_timeout] Call to requests without timeout
  **Location**: `./scripts/clear_workflow_history.py:31:19`
  **Risk**: Low to medium security risk.
  **Suggested Agent**: Sentinel
  **Recommendation**: Review and mitigate if necessary.

- **Issue**: Security Warning [B113:request_without_timeout] Call to requests without timeout
  **Location**: `./scripts/clear_workflow_history.py:47:27`
  **Risk**: Low to medium security risk.
  **Suggested Agent**: Sentinel
  **Recommendation**: Review and mitigate if necessary.

- **Issue**: Security Warning [B404:blacklist] Consider possible security implications associated with the subprocess module.
  **Location**: `./scripts/parse_jules_issues.py:6:0`
  **Risk**: Low to medium security risk.
  **Suggested Agent**: Sentinel
  **Recommendation**: Review and mitigate if necessary.

- **Issue**: Security Warning [B607:start_process_with_partial_path] Starting a process with a partial executable path
  **Location**: `./scripts/parse_jules_issues.py:153:17`
  **Risk**: Low to medium security risk.
  **Suggested Agent**: Sentinel
  **Recommendation**: Review and mitigate if necessary.

- **Issue**: Security Warning [B607:start_process_with_partial_path] Starting a process with a partial executable path
  **Location**: `./scripts/parse_jules_issues.py:171:15`
  **Risk**: Low to medium security risk.
  **Suggested Agent**: Sentinel
  **Recommendation**: Review and mitigate if necessary.

- **Issue**: Security Warning [B607:start_process_with_partial_path] Starting a process with a partial executable path
  **Location**: `./scripts/parse_jules_issues.py:184:8`
  **Risk**: Low to medium security risk.
  **Suggested Agent**: Sentinel
  **Recommendation**: Review and mitigate if necessary.

- **Issue**: Security Warning [B607:start_process_with_partial_path] Starting a process with a partial executable path
  **Location**: `./scripts/parse_jules_issues.py:222:15`
  **Risk**: Low to medium security risk.
  **Suggested Agent**: Sentinel
  **Recommendation**: Review and mitigate if necessary.

- **Issue**: Security Warning [B404:blacklist] Consider possible security implications associated with the subprocess module.
  **Location**: `./scripts/prune_merged_branches.py:3:0`
  **Risk**: Low to medium security risk.
  **Suggested Agent**: Sentinel
  **Recommendation**: Review and mitigate if necessary.

- **Issue**: Security Warning [B607:start_process_with_partial_path] Starting a process with a partial executable path
  **Location**: `./scripts/prune_merged_branches.py:25:17`
  **Risk**: Low to medium security risk.
  **Suggested Agent**: Sentinel
  **Recommendation**: Review and mitigate if necessary.

- **Issue**: Security Warning [B607:start_process_with_partial_path] Starting a process with a partial executable path
  **Location**: `./scripts/prune_merged_branches.py:44:21`
  **Risk**: Low to medium security risk.
  **Suggested Agent**: Sentinel
  **Recommendation**: Review and mitigate if necessary.

- **Issue**: Security Warning [B607:start_process_with_partial_path] Starting a process with a partial executable path
  **Location**: `./scripts/prune_merged_branches.py:110:23`
  **Risk**: Low to medium security risk.
  **Suggested Agent**: Sentinel
  **Recommendation**: Review and mitigate if necessary.

- **Issue**: Security Warning [B607:start_process_with_partial_path] Starting a process with a partial executable path
  **Location**: `./scripts/prune_merged_branches.py:122:24`
  **Risk**: Low to medium security risk.
  **Suggested Agent**: Sentinel
  **Recommendation**: Review and mitigate if necessary.

- **Issue**: High Cyclomatic Complexity (> 10)
  **Location**: Multiple files (57 instances)
  **Risk**: Difficult to maintain and test.
  **Suggested Agent**: SystemSmith
  **Recommendation**: Refactor functions to reduce complexity. Focus on DatabaseManager, CombatEngine, and AdventureSession.

## 🔹 ONE UI Policy Violations

- **Issue**: `send_message` used instead of editing existing messages.
  **Location**: Multiple files (138 instances, mainly in `ui/` directories)
  **Risk**: Breaks immersion and creates UI clutter.
  **Suggested Agent**: Palette
  **Recommendation**: Replace `send_message` with `edit_original_response` or appropriate state updates.

## 📦 Dependency Issues

- No known vulnerabilities found in dependencies.

## 📚 Documentation & Dead Code

- **Issue**: Potentially dead code detected.
  **Location**: Multiple files (12 instances)
  **Suggested Agent**: SystemSmith
  **Recommendation**: Review and remove unused code to improve maintainability.

## 🧪 Test Coverage Gaps
- Recommend running `pytest-cov` to generate a detailed coverage report and identify missing test paths.

## ✅ Positive Findings
- No hardcoded secrets (API keys, passwords, tokens) were detected in the codebase outside of tests.
- No direct SQL injection vulnerabilities found (assuming PyMongo is used correctly).
- No `TODO`, `FIXME`, or `XXX` comments found in the source code.
- No bare `except:` clauses found.

## 📌 Recommendations
- **Pre-commit hooks**: Enforce ONE UI Policy via custom scripts.
- **Complexity**: SystemSmith should prioritize breaking down the largest methods in `DatabaseManager` and `CombatEngine`.
- **Refactoring**: Adopt a stricter linter configuration (e.g., lower cyclomatic complexity threshold).
