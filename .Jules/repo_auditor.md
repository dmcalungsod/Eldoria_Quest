# Repo Auditor Journal

## 2026-03-01: Comprehensive Audit

**Tools Used:**
- `flake8`, `bandit`, `vulture`, `radon`, `safety`, `ruff`, `pytest-cov`, `grep`.

**Critical Learnings:**
1.  **Grep vs. Static Analysis**: Manual `grep` patterns (`send_message`, `print(`) were faster and more targeted for policy violations (ONE UI) than generic linters.
2.  **Bandit Noise**: The `B311` (standard pseudo-random generators) check generated 192 warnings. Since this is a game heavily relying on RNG for mechanics (loot, damage), these are mostly false positives in a security context. **Action:** Consider configuring `bandit.yaml` to skip B311 for `game_systems/` unless it involves crypto.
3.  **Complexity Metrics**: `radon cc` successfully identified `DataValidator` and `AdventureSession` as major technical debt hotspots. These correlate with areas that are harder to test.
4.  **Coverage Blind Spot**: Testing infrastructure is robust for *logic* (`game_systems`), but nonexistent for *presentation* (`cogs`). This suggests a need for a different testing strategy (e.g., `dpytest`) for Discord interactions.

**Suggestions for Future:**
-   Add a custom `ruff` plugin or pre-commit hook to strictly enforce "ONE UI" (forbid `send_message` unless `ephemeral=True`).
-   Automate the audit to run on PRs modifying `cogs/` to ensure no new `print()` statements or un-awaited coroutines slip in.
-   Install `dpytest` to enable testing of Cogs.

## 2026-02-26: Comprehensive Audit (Current Run)

**Tools Used:**
- `flake8`, `bandit`, `vulture`, `radon`, `safety`, `grep`.

**Critical Learnings:**
1.  **Side-Effects on Import**: `game_systems/data/class_equipments.py` executes logic (prints) at module level. This was caught by manual inspection/grep for `print` but missed by static analysis tools which often ignore `print`.
    *   **Action**: Recommend moving to `if __name__ == "__main__":` block.
2.  **ONE UI Enforcement**: Grep confirmed widespread use of `interaction.response.send_message` in Cogs (`faction`, `tournament`, `event`, `onboarding`). This requires a targeted refactor campaign.
3.  **Unused Imports**: `flake8` identified `cogs.shop_cog` imported in tests but unused, and several unused variables in tests. These are low-hanging fruit for cleanup.
4.  **Security Baseline**: The project is secure against common vulnerabilities (secrets, SQLi, dependencies). The primary "security" noise is RNG usage (`B311`), which is a feature, not a bug, in this RPG context.

**Process Improvements:**
-   Add a `bandit.yaml` config to exclude `B311` for the `game_systems/` directory to reduce noise in future reports.
-   Implement a custom pre-commit check for `print()` statements in non-script files.
# Repo Auditor Journal

## 2026-02-28
- **Tools used:** `flake8`, `bandit`, `vulture`, `radon`, `safety`, `pytest-cov`, and manual regex checks (`grep`).
- **Effectiveness:** Automated tools were highly effective at identifying style, security, dead code, and complexity issues. `safety` was deprecated but `bandit` caught Python-specific security concerns. Manual grep was effective for ONE UI policy violations (`send_message`).
- **Recurring Issues:** High cyclomatic complexity in UI components (e.g., `ShopView`, `QuestBoardView`). Consistent use of `send_message` in UI logic which violates the ONE UI pattern.
- **Recommendations for future:** Add pre-commit hooks for `flake8` and `vulture`. Ensure `bandit` is run in CI. Create specific lint rules for the ONE UI policy if possible (e.g., a custom flake8 plugin).
- **Limitations:** Cannot automatically determine if an `assert` in test code is a security flaw (expected) vs in production code (flaw), though `bandit` flagged test files. Ignored test files for `bandit` severity. `safety` command deprecated.
# Repo Auditor Journal

## 2026-03-01
**Critical Learnings:**
- `flake8` and `radon` are incredibly effective at identifying high-complexity technical debt in newly added game systems (`detect_element` and `apply_weather_modifiers`).
- `vulture` is useful for finding unused variables in tests and analysis scripts, though less reliable on dynamic codebases.
- `bandit` reliably flags the `urllib.request.urlopen` issue and hardcoded asserts in tests.
- `safety check` is deprecated and failed during execution (`safety scan` also failed due to environment issues). Future audits should rely on updated dependency checking tools like `pip-audit`.
- Manual grep for "send_message" in `cogs/` is still the most reliable way to find ONE UI Policy violations, as automated linters don't understand the semantic difference between `send_message` and `edit_original_response`.
- **Suggestion for prevention:** Implement a `pre-commit` hook that runs `flake8`, `vulture`, and `radon` with strict thresholds to prevent complexity and unused variables from entering the main branch. Add `bandit` to the CI pipeline to block simple security regressions like `urlopen` or hardcoded tokens.
