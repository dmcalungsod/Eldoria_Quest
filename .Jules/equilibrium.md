# ⚖️ Equilibrium Journal

## [Current Date] Fix: Auto-Combat Fatigue Multiplier Ignored for High-Defense Players

**Formulaic Imbalance Discovered:**
In `game_systems/combat/auto_combat_formula.py` during `resolve_clash`, the fatigue multiplier (which should increase damage taken by the player over long auto-adventure sessions) was being mathematically ignored if the player's mitigation was higher than the monster's raw DPS.

**Quantification:**
The formula was:
`monster_net_dps = max(1.0, (monster_dps_raw - player_mitigation) * stance_vuln * fatigue_multiplier)`
Because `monster_dps_raw - player_mitigation` is negative for high-defense players, multiplying it by the fatigue multiplier simply made it a larger negative number. The `max(1.0, negative)` clamp immediately overrode it to 1.0, and then the chip damage floor (5% of ATK) was applied. Thus, a high-level player stacking defense was functionally immune to the primary attrition mechanic of the game during offline progression.

**The Fix:**
I correctly isolated the base damage, applied the zero-floor and chip damage floor FIRST, and *then* multiplied by stance and fatigue multipliers.
```python
        # Monster base damage per turn
        base_dmg = max(0.0, monster_dps_raw - player_mitigation)

        # Ensure minimum chip damage from monster (5% of its ATK)
        chip_damage = monster.get("ATK", 10) * 0.05
        base_dmg = max(base_dmg, chip_damage)

        # Apply multipliers (stance, fatigue)
        monster_net_dps = max(1.0, base_dmg * stance_vuln * fatigue_multiplier)
```

**Measured Impact:**
A simulated test (`END`=500, `DEF`=500, 10x Fatigue) demonstrated that damage per second from monsters previously stayed frozen at 5.0 regardless of fatigue. After the fix, it properly scaled to 50.0, validating the fix and ensuring the newly implemented fatigue system properly functions for all playstyles.
