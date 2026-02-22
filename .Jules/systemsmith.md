## 2024-05-22 — Quest Update Desync

**Learning:** `AdventureRewards` was updating quest progress based on *potential* drops rather than *actual* drops, allowing players to complete collection quests without obtaining items.
**Action:** Always verify that reward processing logic operates on the *result* of RNG checks, not the input probabilities. Use explicit `actual_drops` lists.

## 2024-05-23 — Additive vs Multiplicative Luck Scaling

**Learning:** `AdventureRewards` used a linear additive formula for Luck bonuses (`base_chance + luck_bonus`), which could push drop rates over 100% or multiply rare drop rates by 50x at max stats, breaking the economy.
**Action:** Always implement stat-based scaling (like Luck or Crit) using multiplicative formulas (`base * (1 + bonus)`) to preserve the rarity curve and prevent trivializing high-tier content.

## 2025-05-18 — Restore HP on Level Up

**Learning:** Players were not receiving full HP restoration upon leveling up, unlike MP which was restored. This created an inconsistency and felt unrewarding.
**Action:** Updated `AdventureManager._grant_rewards_internal` to restore `current_hp` to `max_hp` when `leveled_up` is True. This ensures a fresh start for the new level.

## 2025-05-24 — Dynamic Stat Practice Thresholds

**Learning:** The "Practice" system (gaining stats via XP from combat actions) used a fixed threshold (100 XP) while the Vestige Point cost scaled exponentially. This created a loophole where high-level players could grind low-level actions to bypass the intended progression curve.
**Action:** Implemented a dynamic threshold formula (`100 + BaseStat * 5`) for practice XP. Progression systems must always scale difficulty with player power to prevent trivialization of end-game growth.
