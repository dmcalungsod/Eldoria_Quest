# Equilibrium Journal

## 2026-02-24 — Buff Stacking & Exponential Scaling Fix

**Learning:** Players could achieve infinite stat growth by spamming buff skills (e.g., "Rage").
**The Imbalance:**
1.  **Stacking:** `add_active_buff` simply inserted new buff records, allowing multiple instances of the same buff (e.g., 5x "Rage").
2.  **Compounding:** `CombatEngine` calculated percentage buffs based on `stats_dict` (Total Stats). Since Total Stats included existing buffs, re-applying a buff caused exponential growth (Total = Base * 1.5 * 1.5 * ...).

**The Fix:**
1.  **Database:** Modified `add_active_buff` to delete any existing active buff with the same `discord_id` and `name` before inserting. This enforces a "refresh/replace" behavior.
2.  **Math:** Updated `CombatEngine` to accept `base_stats_dict` and use it for percentage buff calculations (`_percent` keys). This ensures buffs always scale off the base value (linear scaling).

**Measured Impact:**
- **Before:** Casting +50% STR buff twice resulted in 225 STR (Base 100).
- **After:** Casting +50% STR buff twice results in 150 STR (Base 100 + 50). The second cast refreshes the duration but does not stack or compound.

**Player Impact:**
- Removes the "infinite power" exploit.
- Makes buff timing more strategic (refreshing) rather than spam-heavy.
- Preserves the value of base stat upgrades.

## 2026-03-03 — Deepgrove Roots Boss Farming Exploit

**Learning:** High-tier bosses in low-level zones can break progression if not properly gated.
**The Imbalance:**
1.  **Spawn Rate:** The "Feral Stag" (Level 11 Boss) had a 15% base spawn chance in the "Deepgrove Roots" (Level 10) adventure zone. This is excessively high for a boss encounter.
2.  **Loot:** It dropped `magic_stone_large` (100%) and `magic_stone_flawless` (25%). These are mid-to-end game resources, allowing Level 10 players to bypass intended material progression.

**The Fix:**
1.  **Spawn Logic:** Removed "Feral Stag" from the regular spawn pool. Added it to the `conditional_monsters` list with a 5% spawn chance and a strict `min_level` requirement of 12.
2.  **Loot Table:**
    - Replaced `magic_stone_large` (100%) with `magic_stone_medium` (100%).
    - Removed `magic_stone_flawless` entirely.
    - Added `magic_stone_large` as a rare (15%) drop to maintain some excitement.

**Measured Impact:**
- **Before:** A player running 100 adventures in Deepgrove Roots would encounter ~15 Feral Stags and gain ~15 Large Magic Stones and ~3-4 Flawless Stones.
- **After:** A player running 100 adventures (if Level 12+) would encounter ~5 Feral Stags and gain ~5 Medium Stones (guaranteed) and ~0-1 Large Stone.
- **Economic Integrity:** Prevents the market flooding of high-tier upgrade materials from a low-risk zone.

**Player Impact:**
- Makes the "Feral Stag" feel like a true rare encounter rather than a farming node.
- Smooths the difficulty curve for new players entering Deepgrove Roots (fewer boss wipes).

## 2026-03-07 — Night Ambush Defense Calculation Fix

**Learning:** Defense stats were completely ignored during Night Ambushes in `AdventureSession`, causing high-level tanks to take massive damage from low-level mobs.
**The Imbalance:**
1.  **Formula:** The damage logic was simply `Monster ATK * 0.8`.
2.  **Impact:** A player with 9999 Defense took the same damage as a player with 0 Defense (e.g., 80 damage from a 100 ATK mob).

**The Fix:**
1.  **Logic:** Updated `_handle_new_encounter` in `adventure_session.py` to calculate player defense using `calculate_tiered_bonus`.
2.  **Formula:** `(Monster ATK * 0.8) - (Defense Mitigation * 0.5)`.
    - **Defense Mitigation:** Standard combat mitigation formula `Def * (0.3 + 0.2 * saturation)`.
    - **Ambush Penalty:** Mitigation is reduced by 50% to reflect the surprise nature of the attack.
    - **Floor:** Damage cannot go below 1.

**Measured Impact:**
- **Low Defense (END 10, DEF 0):** Takes ~77 damage (Previously 80).
- **High Defense (END 100, DEF 100):** Takes ~17 damage (Previously 80).
- **God Mode (END 9999, DEF 9999):** Takes 1 damage (Previously 80).

**Player Impact:**
- Restores value to the Defense stat during night cycles.
- Maintains the "danger" of night travel (50% mitigation penalty) without being unfair to high-level players.

## 2026-03-08 — Formula Review & Exploit Check

**Learning:** When reviewing current gameplay formulas against Foreman's task list, no critical exploits or mathematical imbalances were detected in the auto-adventure systems or classes.
**The Observation:**
1.  **Stat Scaling:** Exponential growth on stat upgrades is safely bounded by the `_execute_upgrade` logic and `hp_gain` limits.
2.  **Regeneration:** HP/MP regeneration is strictly capped at 5% max HP/MP per step to prevent infinite loops, and `SURGE` logic properly aborts regen at full HP.
3.  **Ability Scaling:** `calculate_skill_attack_power` properly bounds scaling.
4.  **Special Abilities:** `Smite` and others are correctly balanced (0.8x multiplier for Smite as per previous adjustment).
5.  **Foreman Tasks:** No tasks were assigned to Equilibrium in `.Jules/foreman_plan.md` for this sprint.

**Outcome:**
- Verified the integrity of mathematical models.
- Since no explicit imbalances were found and no active tasks were assigned by Foreman, no code changes were made, and no PR will be submitted today as per instructions.
