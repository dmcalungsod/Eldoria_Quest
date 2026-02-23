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

## 2026-02-26 — Integrating New Frontiers and Identifying Quest Gaps

**Learning:**
Discovered three new locations in `adventure_locations.json` that were absent from `lore_canon.md`: **The Ashlands** (Rank D), **The Celestial Archipelago** (Rank B), and **Gale-Scarred Heights** (Rank A). These locations introduce a new "Sky Realm" verticality to the world map which was previously undocumented.

**Action:**
1. Updated `lore_canon.md` to include these three locations, placing them in the correct progression order based on Level Requirements.
2. Added a new lore section **"The Sky Realms"** to `lore_canon.md` to canonize the existence of floating islands as a consequence of the Sundering's gravity-warping effects.
3. Updated Faction descriptions in `lore_canon.md` to reflect their interests in these new zones (Pathfinders mapping the sky, Arcane Assembly studying the ruins).

**Gap Analysis:**
- **CRITICAL:** No quests exist in `quests.json` for **The Ashlands**, **The Celestial Archipelago**, or **Gale-Scarred Heights**. Players can visit these zones but have no narrative direction or specific tasks.
- **Tone Check:** The new monster descriptions in `monsters.json` for these areas are generally good, but some (like "Zephyr Wisp") border on being too "playful". Will monitor.

**Next Steps:**
- Flag the missing quests to @StoryWeaver and @GameForge.
- Suggest a "Skybound" questline to introduce players to the concept of the Sky Realms.
