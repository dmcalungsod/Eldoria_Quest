# Codex Keeper Journal

## Mission: Codex & Bestiary System Design

**Objective:** Design a comprehensive /codex system for Eldoria Quest that tracks player discoveries (monsters, items, factions, locations, quests) and unlocks lore/stats as rewards for exploration.

## 1. System Analysis

I have explored the codebase and identified the following key components:

*   **Data Sources:**
    *   **Monsters:** `game_systems/data/monsters.py` (Keys: `monster_001`, etc.) - Contains stats, drops, descriptions.
    *   **Items:** `game_systems/data/materials.py`, `equipments.json` - Contains names, rarities, descriptions.
    *   **Locations:** `game_systems/data/adventure_locations.py` - Contains zone info, monster lists.
    *   **Factions:** `game_systems/data/factions.py` - Contains ranks and rewards.
    *   **Quests:** `game_systems/data/quests.json` - Contains text and objectives.

*   **Player Data:**
    *   Managed via `DatabaseManager` (MongoDB).
    *   Existing collections: `players`, `inventory`, `player_quests`, `guild_members`, `adventure_sessions`.
    *   **New Collection Needed:** `player_codex` to store unlocked entries and discovery states.

*   **Integration Points:**
    *   **Combat:** `AdventureManager.simulate_adventure_step` / `AdventureSession` - Hook here for "Monster Kill" unlocks.
    *   **Looting:** `AdventureManager.end_adventure` / `_grant_rewards_internal` - Hook here for "Item Discovery" unlocks.
    *   **Exploration:** `AdventureManager.start_adventure` - Hook here for "Location Discovery".
    *   **Quests:** `QuestSystem` (not fully read yet, but `DatabaseManager` has quest methods) - Hook on completion.

## 2. Design Strategy

### Data Architecture
I will avoid duplicating data. The Codex System should reference the existing `monsters.py`, `materials.py`, etc., as the "Source of Truth" for stats and basic descriptions. The Codex will wrap this data and add:
*   **Lore Layer:** Extended descriptions (StoryWeaver's domain).
*   **Unlock Conditions:** Logic to check if a player can see the entry.
*   **Progress Tracking:** How many times a monster was killed (for tiered unlocks).

### Database Schema (`player_codex`)
```json
{
  "discord_id": 123456789,
  "unlocked_entries": ["monster_001", "item_magic_stone", "loc_forest"],
  "counters": {
    "monster_001_kills": 5,
    "item_magic_stone_found": 10
  },
  "completion_rewards": ["title_loremaster"]
}
```

### UI/UX
*   **Main Command:** `/codex`
*   **View:** `CodexHubView` (Discord UI)
    *   **Categories:** Bestiary, Item Index, Faction Chronicle, Exploration Atlas, Quest Log.
    *   **Navigation:** Dropdowns for categories, Buttons for paging.
    *   **Detail View:** Embed showing Lore, Stats (if unlocked), Drops (masked if not found).

## 3. Implementation Plan
1.  **Define Schema:** formalized in the design doc.
2.  **Define Triggers:**
    *   *On Kill:* Update kill counter -> Unlock Bestiary Entry.
    *   *On Drop:* Update item counter -> Unlock Item Entry + Bestiary Drop Info.
    *   *On Travel:* Unlock Location Entry.
3.  **Reward Structure:**
    *   100% Category completion -> Title/Badge.
    *   Lore tiers (e.g., kill 1 -> basic info, kill 10 -> deep lore).

## 4. Open Questions / Risks
*   **Performance:** Checking codex unlocks on every kill/drop might be heavy.
    *   *Mitigation:* Cache unlocks in memory or batch updates at the end of an adventure (similar to how loot is batched).
*   **Spoiler Prevention:** How to show "Undiscovered" entries without ruining the surprise?
    *   *Solution:* Show "???" or "Unknown Creature" for adjacent IDs, but hide completely unrelated ones (or just show total count "5/50 discovered").

## 5. Design Status
✅ **Completed:**
*   Design Document created at `.Jules/codex_design.md`.
*   Detailed schema defined.
*   UI/UX flow mapped out.
*   Integration points with other agents identified.

Ready for review and implementation planning.
