## 2024-05-23 — [Combat Narration Expansion]
**Learning:** `CombatPhrases` relies on substring matching (`if "Goblin" in name`) which is robust but requires maintenance as new monster names are added. Grouping keywords (e.g., `["Wisp", "Shade", "Revenant"]`) allows for broader coverage without writing specific lines for every single mob.
**Action:** Future narrative updates should check `game_systems/data/monsters.py` for new naming patterns and add them to the relevant keyword groups in `CombatPhrases`.

## 2026-02-21 — Atmospheric Mission Reports

**Learning:** Mission reports were static and dry. By using a dictionary mapping location IDs to atmospheric text, I significantly increased immersion without changing mechanics.
**Action:** In future narrative enhancements, look for opportunities to replace static strings with context-aware, randomized lists to keep the experience fresh.

## 2026-02-28 — The Wailing Chasm & The Blind Choir

**Learning:** When writing for subterranean or sensory-deprived environments (like The Wailing Chasm), focusing on the *absence* of something (e.g., "absolute, terrifying silence") or the physical sensation of sound (e.g., "a cold vibration pulses through the tome", "making your teeth ache") creates a much stronger emotional reaction than simply describing what is seen in the dark.
**Action:** In future updates to sound-based or void-corrupted mechanics, emphasize the physical, bodily impact of the corruption rather than just visual descriptors. Allow NPCs like "Whispering" Thorne to reflect the psychological toll of the environment in their dialogue.
## 2026-03-01 — Flavor Text for The Silent City of Ouros

**Learning:** When requested by Foreman to add narrative context to a newly implemented region (e.g., The Silent City of Ouros), appending to `MISSION_FLAVOR_TEXT` in `game_systems/data/narrative_data.py` is the safest and most effective way to enhance the player's immersion. This avoids inadvertently making gameplay changes or adding mechanical content like quests.
**Action:** Future narrative improvements for new regions should focus on expanding `game_systems/data/narrative_data.py` or existing text repositories strictly without modifying mechanical arrays (such as `quests.json`), unless specifically tasked to update the flavor text of existing elements.
