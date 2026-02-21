## 2024-05-23 — Defense Stat Integration

**Learning:** The `PlayerStats` system was missing a flat `DEF` stat, relying solely on `END` for defense calculations. This prevented buffs and items from providing direct defense bonuses (like `damage_res`).
**Action:** When adding new stat-modifying items, always ensure the underlying `PlayerStats` model and `DamageFormula` support the specific stat key (e.g., `DEF`, `RES`) to avoid silent failures where buffs are applied but ignored.
