## 2025-10-28 — Skill Upgrade Cost Bypass

**Learning:** `SkillTrainerView._execute_upgrade` was using the `base_cost` of a skill directly from static data instead of scaling it based on the player's current skill level. This allowed high-level upgrades (which should cost exponentially more) to be purchased for the cheap Level 1 price.
**Action:** Always verify that cost calculations involving scaling factors (like skill levels) are performed server-side using the current state from the database, rather than relying on static base values or client input. Added a specific test case to verify scaling logic.

## 2025-10-29 — Infirmary Free MP Exploit

**Learning:** `DatabaseManager.execute_heal` calculated cost solely based on missing HP (`missing = max(0, max_hp - player["current_hp"])`), but the update operation set both HP and MP to their maximums. This allowed players with full HP but empty MP to restore MP for free, violating the game's scarcity economy.
**Action:** Ensure cost calculations account for *all* restored resources. Modified `execute_heal` to include missing MP in the cost formula (0.5 Aurum per point) and updated `InfirmaryView` to reflect this. Added `tests/test_infirmary_exploit.py` to prevent regression.
