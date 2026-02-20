## 2025-02-18 — HP Overflow on Stat Reduction

**Learning:** When player stats (Max HP/MP) are reduced (e.g., unequipping items), current HP/MP were not automatically clamped to the new maximums. This allowed players to "snapshot" high health pools from temporary gear.
**Action:** Implemented a clamp check in `EquipmentManager.recalculate_player_stats` to verify `current_hp <= max_hp` after any stat update. Added `tests/test_hp_overflow.py` to prevent regression.
