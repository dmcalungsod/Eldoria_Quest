## 2024-05-23 — [Combat Narration Expansion]
**Learning:** `CombatPhrases` relies on substring matching (`if "Goblin" in name`) which is robust but requires maintenance as new monster names are added. Grouping keywords (e.g., `["Wisp", "Shade", "Revenant"]`) allows for broader coverage without writing specific lines for every single mob.
**Action:** Future narrative updates should check `game_systems/data/monsters.py` for new naming patterns and add them to the relevant keyword groups in `CombatPhrases`.

## 2026-02-21 — Atmospheric Mission Reports

**Learning:** Mission reports were static and dry. By using a dictionary mapping location IDs to atmospheric text, I significantly increased immersion without changing mechanics.
**Action:** In future narrative enhancements, look for opportunities to replace static strings with context-aware, randomized lists to keep the experience fresh.

## 2026-02-23 — [Class-Specific Combat Narration]

**Learning:** Players felt combat was repetitive. By implementing class-specific attack and victory phrases (e.g., `WARRIOR_VICTORY`, `MAGE_ATTACKS`), I was able to give each class a distinct "voice" in the logs. The `CombatPhrases.player_victory` method needed an update to accept `player_class_id`, which required a small change in `CombatEngine`.
**Action:** When adding new classes in the future, remember to add their corresponding `CLASS_ATTACKS` and `CLASS_VICTORY` constants in `combat_phrases.py` and update the selection logic.
