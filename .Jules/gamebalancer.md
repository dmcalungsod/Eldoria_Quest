## 2024-05-23 — Progression Wall in XP Curve

**Learning:** Systemic imbalance discovered where the default quadratic XP curve (`1000 * L^2`) combined with linear Monster XP rewards (`25 * L`) created an exponential grind wall. By level 20, players needed ~650 kills per level, making progression effectively impossible without engaging with thousands of battles. This violated the principle of "progression should feel earned, not impossible."

**Action:** Adjusted the XP curve formula to `200 * L^2 + 800 * L`. This significantly reduces the mid-to-late game requirement (e.g., Level 20 drops from ~390k to ~96k XP) while maintaining the early game pacing (Level 1 stays at 1000 XP). Future curve adjustments should always be simulated against average XP income sources (monsters/quests) to ensure the "time-to-level" metric remains within reasonable bounds (e.g., 50-150 encounters/quests per level).
