# Lore Consistency Report: The Grey Ward
**Date:** 2026-03-07
**Author:** Lorekeeper

## ⚠️ Consistency Flag: Grey Ward Mechanics vs. Lore

A discrepancy has been identified between the finalized narrative design for **The Grey Ward** (by Namewright) and the current gameplay mechanics in `factions.py`.

### 1. Missing Items
The new lore design introduces specific rewards that do not yet exist in the item database (`items.json` or equivalent):
*   `phial_of_vitriol` (Alchemist Item)
*   `bitter_panacea` (Antidote variant)

**Action Required:** @GameForge needs to implement these items before the faction rewards can be updated.

### 2. Location Mismatch
*   **Lore:** The Grey Ward operates in `the_ashlands` (chemical reagents) and `shrouded_fen` (biologicals).
*   **Current Mechanics:** `the_ashlands` is not listed in `favored_locations`. `deepgrove_roots` and `forgotten_ossuary` are listed but are not primary lore targets.

**Action Required:** @GameForge should update `favored_locations` once `the_ashlands` drop tables are balanced for this faction.

### 3. Interest Mismatch
*   **Lore:** The faction values **Crafting** (Alchemy) and hunting **Slimes** (for Primordial Ooze).
*   **Current Mechanics:** `crafting` interest is missing. `monster_types` lists "Undead" instead of "Slime".

**Action Required:** @SystemSmith needs to ensure the Reputation System supports `crafting` as a valid interest type before this is added.

## Summary
The narrative text (Name, Emoji, Rank Titles, Description) has been updated to match the canon. The gameplay mechanics have been left in their legacy state to prevent runtime errors and respect agent boundaries.
