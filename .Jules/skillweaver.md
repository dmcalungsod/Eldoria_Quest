## Auto-Combat Skill Formula Scaling Fix

*   **Observed Issue:** The Auto-Combat deterministic formula applied a static `1.125x` DPS multiplier for *any* offensive skill the player possessed. This completely ignored skill levels, `power_multipliers`, and stat scaling, making skill upgrades practically useless during auto-adventures. Meanwhile, standard combat applied these complex scaling metrics properly.
*   **Fix:** Extracted the core scaling logic from `DamageFormula.player_skill` into a shared, reusable method called `calculate_skill_attack_power`. Updated `AutoCombatFormula.calculate_player_dps` to iterate over all active player skills, determine the one with the highest expected raw power using the true formula, and blend it proportionally into the player's basic attack power.
*   **Player Impact:** Skill choices and upgrades now materially accelerate offline auto-adventures, properly rewarding strategic stat and skill investments.


## Auto-Adventure Skill Tree Integration

*   **Observed Issue:** The Auto-Combat deterministic formula (`AutoCombatFormula.resolve_clash`) lacked integration for new class mechanics (divine_shield, aura_of_vitality, meteor_swarm, mana_shield, summon_companion, pack_tactics), rendering them useless in offline adventures.
*   **Fix:** Mapped these skills to deterministic combat statistics:
    - `divine_shield`: 10% reduction to `monster_dps_raw`.
    - `aura_of_vitality`: Heals 2% of Max HP post-combat.
    - `meteor_swarm`: Reduces `turns_to_kill` by 15% for non-elite encounters.
    - `mana_shield`: Converts final damage taken directly to MP loss up to 50% of Max MP.
    - `summon_companion`: Buffers final damage by 20% of Max HP.
    - `pack_tactics`: Increases `player_net_dps` by 10% against bosses.
*   **Player Impact:** Players investing in specialized skill trees (like Elementalist or Warden) now benefit proportionally in offline auto-adventures, preserving class identity and balance.
