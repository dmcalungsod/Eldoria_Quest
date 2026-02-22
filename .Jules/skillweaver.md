
# SkillWeaver Journal

## 2024-05-22: Fixed Player Self-Buff Skills

### Observed Issue
Skills like **Endure** (Warrior), **Blessing** (Cleric), and **Stealth** (Rogue) were defined with `buff_data` in `skills_data.py`, but this data was ignored by the combat engine. Using these skills would consume MP and log a flavor message, but no actual stat bonus was applied or persisted.

- **Observed:** Using "Endure" resulted in no change to END stat.
- **Root Cause:** `CombatEngine._execute_player_skill` simply logged a message for buff skills and did not calculate or return the buff effect. `CombatHandler` had logic to load buffs from the database but no logic to save new ones generated during combat.

### Fix Implementation
1.  **Modified `CombatEngine` (`game_systems/combat/combat_engine.py`)**:
    - Added `_apply_skill_buffs` method to parse `buff_data`.
    - Implemented logic to handle `_percent` keys (e.g., `END_percent`) by calculating flat bonuses based on current stats.
    - Implemented `all_stats_percent` logic to boost all primary stats.
    - Updated `run_combat_turn` to return a `new_buffs` list containing the calculated buffs.

2.  **Modified `CombatHandler` (`game_systems/adventure/combat_handler.py`)**:
    - Updated `resolve_turn` to process `new_buffs` from the engine result.
    - Added logic to persist these buffs to the database using `self.db.add_active_buff`, converting turn duration to seconds (1 turn = 60s).

### Verification
- **Unit Test:** Verified `CombatEngine` returns correct buff objects for single-stat and multi-stat (`Blessing`) buffs.
- **Integration Test:** Verified `CombatHandler` correctly calls `add_active_buff` with the right parameters and duration.
- **Regression:** Ran existing `tests/test_buff_system.py` and `tests/test_damage_scaling.py` to ensure no regressions.

### Impact
Players using buff skills will now receive the intended stat boosts for the duration of combat (or until time expires). This restores functionality to support classes and tank builds.
