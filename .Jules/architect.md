# Architect Journal

## 2025-10-28 — Expansion Design: The Frostfall Expanse

**Design Choice:**
Chosen "Major Content Expansion" over "New Class" or "Skill Tree Expansion".
**Reasoning:**
- The game currently has a solid class foundation (Warrior, Mage, Rogue, Cleric, Ranger) but lacks high-tier content beyond Rank B (Crystal Caverns).
- An expansion provides a concrete goal for players and integrates multiple systems (Combat, Crafting, Exploration).

**Theme Alignment:**
- "The Frostfall Expanse" reinforces the "Grim Survival" tone.
- The "Sheer Cold" mechanic adds a layer of survival pressure beyond simple HP management, forcing strategic preparation (potions/warm gear).

**Integration Notes:**
- **Security:** The new "Cold Damage" mechanic must be calculated server-side in `AdventureSession` to prevent client-side negation.
- **Economy:** High-value drops (Wyrm Heart) should be rare to prevent inflation.
- **Lore:** Connects to the "Sundering" via the cracked Elemental Plane.

**Next Steps:**
- Monitor implementation by Tactician (Environment Mechanics) and GameForge (Assets).
- Consider a future class "Cryomancer" or "Survivor" that utilizes this zone's mechanics specifically.
