## 2024-05-23 — [Combat Narration Expansion]
**Learning:** `CombatPhrases` relies on substring matching (`if "Goblin" in name`) which is robust but requires maintenance as new monster names are added. Grouping keywords (e.g., `["Wisp", "Shade", "Revenant"]`) allows for broader coverage without writing specific lines for every single mob.
**Action:** Future narrative updates should check `game_systems/data/monsters.py` for new naming patterns and add them to the relevant keyword groups in `CombatPhrases`.
