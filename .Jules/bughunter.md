## 2025-10-28 — Skill Upgrade Cost Bypass

**Learning:** `SkillTrainerView._execute_upgrade` was using the `base_cost` of a skill directly from static data instead of scaling it based on the player's current skill level. This allowed high-level upgrades (which should cost exponentially more) to be purchased for the cheap Level 1 price.
**Action:** Always verify that cost calculations involving scaling factors (like skill levels) are performed server-side using the current state from the database, rather than relying on static base values or client input. Added a specific test case to verify scaling logic.

## 2025-02-18 — HP/MP Snapshotting on Unequip

**Learning:** Players could "snapshot" high HP/MP values by equipping stat-boosting gear, healing, and then unequipping the gear. `recalculate_player_stats` updated the maximums but did not clamp the current values, allowing `current_hp > max_hp`. This created an exploit where players could enter combat with inflated health.
**Action:** Implemented an atomic clamp using MongoDB's `$min` operator in `DatabaseManager.clamp_player_vitals`. Updated `EquipmentManager.recalculate_player_stats` to call this method whenever stats change. This ensures `current_hp` never exceeds `max_hp`, even if `max_hp` drops significantly.
