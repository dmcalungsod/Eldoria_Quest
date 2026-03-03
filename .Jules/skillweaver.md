## Auto-Combat Skill Formula Scaling Fix

*   **Observed Issue:** The Auto-Combat deterministic formula applied a static `1.125x` DPS multiplier for *any* offensive skill the player possessed. This completely ignored skill levels, `power_multipliers`, and stat scaling, making skill upgrades practically useless during auto-adventures. Meanwhile, standard combat applied these complex scaling metrics properly.
*   **Fix:** Extracted the core scaling logic from `DamageFormula.player_skill` into a shared, reusable method called `calculate_skill_attack_power`. Updated `AutoCombatFormula.calculate_player_dps` to iterate over all active player skills, determine the one with the highest expected raw power using the true formula, and blend it proportionally into the player's basic attack power.
*   **Player Impact:** Skill choices and upgrades now materially accelerate offline auto-adventures, properly rewarding strategic stat and skill investments.

