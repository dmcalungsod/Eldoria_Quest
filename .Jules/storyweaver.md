# StoryWeaver Journal

## 2026-03-05 — Alchemist Narrative Integration

**Learning:** Narrative text is scattered across `class_data.py`, `skills_data.py`, and `combat_phrases.py`.
**Learning:** `CombatPhrases.player_attack` uses hardcoded class IDs (e.g., `player_class_id == 6` for Alchemist) to switch between narrative styles.
**Learning:** `SKILL_PHRASES` in `combat_phrases.py` allows for specific skill narration, overriding generic text.
**Action:** Always check `combat_phrases.py` when adding a new class to ensure it doesn't fall back to generic text.
**Action:** Use vivid, sensory language ("hiss", "fumes", "slurry") for Alchemist descriptions to distinguish them from Mages.
