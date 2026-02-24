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
