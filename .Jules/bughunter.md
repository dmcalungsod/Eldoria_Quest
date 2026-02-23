## 2025-10-28 — Skill Upgrade Cost Bypass

**Learning:** `SkillTrainerView._execute_upgrade` was using the `base_cost` of a skill directly from static data instead of scaling it based on the player's current skill level. This allowed high-level upgrades (which should cost exponentially more) to be purchased for the cheap Level 1 price.
**Action:** Always verify that cost calculations involving scaling factors (like skill levels) are performed server-side using the current state from the database, rather than relying on static base values or client input. Added a specific test case to verify scaling logic.

## 2025-10-29 — Infirmary Free MP Exploit

**Learning:** `DatabaseManager.execute_heal` calculated cost solely based on missing HP (`missing = max(0, max_hp - player["current_hp"])`), but the update operation set both HP and MP to their maximums. This allowed players with full HP but empty MP to restore MP for free, violating the game's scarcity economy.
**Action:** Ensure cost calculations account for *all* restored resources. Modified `execute_heal` to include missing MP in the cost formula (0.5 Aurum per point) and updated `InfirmaryView` to reflect this. Added `tests/test_infirmary_exploit.py` to prevent regression.

## 2025-10-30 — Shop Stale State

**Learning:** `ShopView` relied on cached `current_aurum` in its state to update the UI after a purchase attempt. If a player's balance changed externally (e.g., spent elsewhere) while the shop was open, a failed purchase would still display the old (stale) balance, confusing the user.
**Action:** Implemented the "Refetch Critical Data" pattern. `ShopView` now explicitly fetches fresh player data from the database after every transaction attempt (successful or not) to ensure the UI reflects the true server state. Added `tests/test_shop_stale_state.py` to verify this behavior.

## 2026-02-23 — Adventure Double Claim Race Condition

**Learning:** `AdventureManager.end_adventure` fetched the active session and then updated it separately, leaving a window where concurrent requests could claim rewards multiple times before the session was closed. This is a classic "Time-of-check to time-of-use" (TOCTOU) vulnerability.
**Action:** Implemented `DatabaseManager.mark_adventure_claiming` to atomically transition the session status from `in_progress`/`completed` to `claiming` using `find_one_and_update`. This ensures only one request can proceed to reward distribution. Always use atomic operations for critical state transitions involving economy or rewards.
