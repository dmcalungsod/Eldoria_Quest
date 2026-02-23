## 2024-05-23 — [Combat Narration Expansion]
**Learning:** `CombatPhrases` relies on substring matching (`if "Goblin" in name`) which is robust but requires maintenance as new monster names are added. Grouping keywords (e.g., `["Wisp", "Shade", "Revenant"]`) allows for broader coverage without writing specific lines for every single mob.
**Action:** Future narrative updates should check `game_systems/data/monsters.py` for new naming patterns and add them to the relevant keyword groups in `CombatPhrases`.

## 2026-02-21 — Atmospheric Mission Reports

**Learning:** Mission reports were static and dry. By using a dictionary mapping location IDs to atmospheric text, I significantly increased immersion without changing mechanics.
**Action:** In future narrative enhancements, look for opportunities to replace static strings with context-aware, randomized lists to keep the experience fresh.
