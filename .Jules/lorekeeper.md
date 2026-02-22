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

## 2026-02-25 — Canon Expansion & NPC Integration

**Learning:**
The world of Eldoria has grown to include specific NPC personalities and class definitions that were not previously documented in the canon. The distinction between "Void" and "Veil" entities is becoming more relevant as higher-tier content (Rank S) is defined.

**Action:**
1.  **Restored & Expanded `lore_canon.md`**: Merged the existing location list (including Deepgrove Roots and Void Sanctum) with new details from `narrative_data.py` and `quests.json`.
2.  **Added NPC Roster:** Documented key figures like Guildmaster Kael, Captain Rhea, and others to ensure consistent voice in future quest text.
3.  **Added Class Descriptions:** Integrated class lore to ground mechanics in the world's history.
4.  **Refined Location Descriptions:** Added atmospheric details (hazards, specific inhabitants) to the location list.

**Observations:**
- **Consistency Check:** The "Clockwork Halls" and "Void Sanctum" are firmly established in the lore now.
- **Tone Alignment:** The "Grim but Hopeful" tone guideline remains central.
- **Correction:** I initially overlooked the existing `lore_canon.md` and `lorekeeper.md` files. I have restored the historical data and merged it with the new findings to preserve the project's memory.

**Next Steps:**
- Monitor new quest additions for adherence to the established NPC voices.
- Clarify the distinction between "Void" entities and "Veil-twisted" nature in future updates.
