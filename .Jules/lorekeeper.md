# 📓 Lorekeeper Journal

## 2024-05-22 — Harmonizing Canon and Expanding Bestiary

**Learning:**
Found that the official location list in `lore_canon.md` was missing two key zones present in the game code (`adventure_locations.py`): **The Sunken Grotto** and **The Clockwork Halls**. This creates a disconnect between the world documentation and the actual gameplay progression.
Also observed that many monsters (Slimes, Goblins, Wolves, Spiders, Treants) shared identical descriptions, which weakens the immersive "literary" tone of the game.

**Action:**
1. Updated `lore_canon.md` to include the missing locations at their correct Ranks (C and B respectively).
2. Conducted a comprehensive review of `monsters.json` and rewrote 26 duplicate descriptions. Each monster variant now has unique text that references its specific ecology, abilities, or relation to the Sundering/Veil.
3. Verified that the new descriptions adhere to the "grim but hopeful" and "material" tone guidelines.

**Next Steps:**
- Review `quests.json` to ensuring quest dialogue matches the updated monster lore.
- Check `items.py` for any generic flavor text that could be enhanced.

## 2026-03-02 — Integrating New Frontiers

**Learning:**
Reviewed `adventure_locations.json` and found five new locations missing from the canon: **The Ashlands (Rank D)**, **The Forgotten Ossuary (Rank B)**, **The Celestial Archipelago (Rank B)**, **Gale-Scarred Heights (Rank A)**, and **The Shimmering Wastes (Rank A)**.
Also confirmed that the ID conflict between Frostfall Expanse and Molten Caldera was successfully avoided (111-115 vs 106-110).
The flavor text in `narrative_data.py` is exceptionally strong, adhering well to the "material" and "grim" tone guidelines.

**Action:**
1. Updated `lore_canon.md` to include all five missing locations, placing them in their correct Rank progression.
2. Refined the description for **The Frostfall Expanse** to better match its in-game lore.
3. Verified that all monster descriptions for the new zones are consistent with the world's history (e.g., "Construct of animate permafrost", "Ancient ruins held aloft by failing magic").

**Next Steps:**
- Monitor the implementation of the "Codex" to ensure these locations are correctly categorized in the UI.
