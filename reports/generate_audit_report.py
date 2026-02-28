
with open("reports/flake8.txt") as f:
    flake8_out = f.read()

with open("reports/bandit.txt") as f:
    bandit_out = f.read()

with open("reports/vulture.txt") as f:
    vulture_out = f.read()

with open("reports/complexity.txt") as f:
    complexity_out = f.read()

report = """# 🔍 Eldoria Quest Codebase Audit — 2026-02-28

**Auditor:** Repo Auditor
**Scope:** Entire repository
**Tools Used:** flake8, bandit, vulture, radon, pytest-cov, manual review

## Executive Summary
Comprehensive codebase audit completed. Key findings include a critical pip vulnerability in the test environment, a medium security risk with `urlopen`, several instances of unused variables (dead code), UI policy violations (using `send_message` improperly), and high complexity in some methods. Test coverage is 73% across core components.

## 🚨 Critical Issues (Fix Immediately)
- **Issue**: Critical Vulnerability CVE-2026-1703 (pip version 25.3 detected in tests)
  **Location**: `tests/test_pip_security.py` / Environment
  **Risk**: Known CVE allows arbitrary code execution during package installation.
  **Suggested Agent**: Sentinel
  **Recommendation**: Update testing environment to `pip==26.0.1` and fix `scripts/build.sh`.

## ⚠️ High Priority Issues
- **Issue**: ONE UI Policy Violations (`send_message` used instead of edits/ephemeral properly)
  **Location**: Various cogs (e.g., `cogs/quest_hub_cog.py:69`, `cogs/tournament_cog.py:127`)
  **Risk**: Clutters Discord UI and violates the established design pattern.
  **Suggested Agent**: Palette
  **Recommendation**: Refactor commands to use `edit_original_response` or appropriate UI updates.

## 🔸 Medium Priority Issues
- **Issue**: [B310:blacklist] Audit url open for permitted schemes
  **Location**: `scripts/chronicler/post_update.py:100`
  **Risk**: Allowing use of file:/ or custom schemes is often unexpected and could lead to path traversal/LFI.
  **Suggested Agent**: Sentinel
  **Recommendation**: Validate the `req` URL scheme explicitly permits only `https://`.

- **Issue**: High Cyclomatic Complexity in UI methods
  **Location**: `cogs/shop_cog.py` (`build_item_select`), `cogs/infirmary_cog.py` (`build_infirmary_embed`)
  **Risk**: Hard to maintain, prone to bugs.
  **Suggested Agent**: SystemSmith
  **Recommendation**: Break down complex UI building methods into smaller, testable helpers.

## 📦 Dependency Issues
- Pip is outdated and vulnerable (25.3 -> 26.0.1)
- Other dependencies should be scanned properly once pip is updated.

## 📚 Documentation Gaps
- **Issue**: Missing docstrings in `cogs/` and some `game_systems/` modules (flagged by manual review and flake8).
  **Suggested Agent**: SystemSmith / Any
  **Recommendation**: Enforce docstring requirements in CI/CD pipeline.

## 🧪 Test Coverage Gaps
- Total Coverage: 73%
- **Low Coverage Areas**: `cogs/adventure_cog.py` (0%), `cogs/adventure_loop.py` (0%), `cogs/character_cog.py` (0%), `game_systems/character/ui/adventure_menu.py` (32%).
- **Suggested Agent**: BugHunter
  **Recommendation**: Prioritize writing tests for `adventure_loop` and core cogs.

## ✅ Positive Findings
- Core systems (`game_systems/combat`, `game_systems/core`) have strong test coverage (>80%).
- Database module utilizes parameterization properly (no obvious SQL injection vulnerabilities found).
- Use of abstract base classes and clear type hints in many areas.

## 📌 Recommendations
- Implement `pre-commit` hook to catch flake8 and vulture errors before they reach the main branch.
- Add `bandit` to the CI pipeline to prevent future security regressions.
"""

with open(".Jules/audit_report_2026-02-28.md", "w") as f:
    f.write(report)
