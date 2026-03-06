## Auto-Combat Skill Formula Scaling Fix

*   **Observed Issue:** The Auto-Combat deterministic formula applied a static `1.125x` DPS multiplier for *any* offensive skill the player possessed. This completely ignored skill levels, `power_multipliers`, and stat scaling, making skill upgrades practically useless during auto-adventures. Meanwhile, standard combat applied these complex scaling metrics properly.
*   **Fix:** Extracted the core scaling logic from `DamageFormula.player_skill` into a shared, reusable method called `calculate_skill_attack_power`. Updated `AutoCombatFormula.calculate_player_dps` to iterate over all active player skills, determine the one with the highest expected raw power using the true formula, and blend it proportionally into the player's basic attack power.
*   **Player Impact:** Skill choices and upgrades now materially accelerate offline auto-adventures, properly rewarding strategic stat and skill investments.

# SkillWeaver Journal

## 2026-03-12: Rogue Skill Abstraction for Auto-Combat
- **Discovered Imbalance:** The new Rogue skills (e.g., Shadow Step, Venomous Strike) introduce complex mechanics (`next_hit_crit` and `conditional_multiplier`) that only worked in the turn-based engine, meaning they had zero impact on the `AutoCombatFormula` used by offline expeditions. Rogue players would get no benefit from their Class Skills in Auto-Adventure.
- **Implemented Fix:** Abstracted burst damage effects into `AutoCombatFormula.resolve_clash()`.
  - `next_hit_crit`: We model 25% uptime. Each guaranteed crit effectively deletes 1 enemy turn. We calculate `uses` and subtract `uses * monster_net_dps` directly from `final_damage_taken`.
  - `conditional_multiplier`: Massive damage spike. Modeled similarly with 25% uptime, but we subtract `1.5 * uses * monster_net_dps` to reflect the higher burst potential against poisoned targets.
- **Impact:** Rogue's new skill tree now provides tangible defensive benefits (via faster kills) in auto-adventure, aligning their offline power curve with active play.
