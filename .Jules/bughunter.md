## 2025-10-28 — Skill Upgrade Cost Bypass

**Learning:** `SkillTrainerView._execute_upgrade` was using the `base_cost` of a skill directly from static data instead of scaling it based on the player's current skill level. This allowed high-level upgrades (which should cost exponentially more) to be purchased for the cheap Level 1 price.
**Action:** Always verify that cost calculations involving scaling factors (like skill levels) are performed server-side using the current state from the database, rather than relying on static base values or client input. Added a specific test case to verify scaling logic.
