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
