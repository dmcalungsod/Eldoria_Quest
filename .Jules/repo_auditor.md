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
