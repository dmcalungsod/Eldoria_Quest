# Codex & Bestiary System Design

## Overview
The **Codex & Bestiary** is a living encyclopedia that chronicles a player's journey through Eldoria. It serves as a centralized repository for Lore, Monster Statistics, Item Information, Faction History, and Exploration Milestones.

**Core Philosophy:**
*   **Knowledge is Reward:** Unlocking entries provides intrinsic motivation.
*   **Visible Progress:** Completion percentages encourage exploration.
*   **Immersion:** Deepens the world-building by providing context to gameplay elements.

## Command Structure

### `/codex`
The primary entry point. Opens the main **Codex Hub**.

*   **Usage:** `/codex [optional: category]`
*   **Arguments:**
    *   `category` (Optional): Jump directly to a section (Bestiary, Items, Factions, Locations, Quests).

## UI/UX Design

### 1. Codex Hub (Main Menu)
*   **Embed:** Displays the player's overall completion statistics.
    *   **Title:** `[Player Name]'s Codex`
    *   **Description:** "A record of your discoveries in Eldoria."
    *   **Fields:**
        *   📖 **Bestiary:** `12/50 (24%)`
        *   🏺 **Item Index:** `45/200 (22.5%)`
        *   🏛️ **Factions:** `1/3 Discovered`
        *   🗺️ **Atlas:** `4/10 Zones Mapped`
        *   📜 **Quests:** `15 Completed`
*   **Navigation (Dropdown/Buttons):**
    *   `Select Category...` (Dropdown) -> Updates the embed to the selected category view.
    *   `🔍 Search` (Button) -> Opens a modal to search entries by name.

### 2. Category Views
Each category has a specific layout.

#### 📖 Bestiary View
*   **List View:** Displays a paginated list of monsters.
    *   **Unlocked:** Shows Name and Tier icon (e.g., `[Normal] Goblin Grunt`).
    *   **Locked:** Shows `???` or `Undiscovered Beast`.
*   **Detail View (On Selection):**
    *   **Title:** Monster Name (e.g., "Goblin Grunt")
    *   **Image:** (Optional) Monster sprite/art.
    *   **Lore:** Atmospheric description (from `monsters.py` + extended lore).
    *   **Stats:** HP, ATK, DEF (Unlocked after 1 Kill).
    *   **Habitat:** Locations where it spawns.
    *   **Drops:** List of drops.
        *   *Hidden:* "???" until the player has received the drop at least once.
    *   **Kill Count:** "Defeated: 42 times"

#### 🏺 Item Index View
*   **List View:** Filterable by type (Weapon, Armor, Material, Consumable).
*   **Detail View:**
    *   **Title:** Item Name.
    *   **Rarity:** Color-coded.
    *   **Description:** Flavor text.
    *   **Source:** "Dropped by [Monster Name]" or "Crafted" or "Shop".
    *   **Stats:** (If equipment) ATK/DEF bonuses.

#### 🏛️ Faction Chronicle
*   **View:** Tabs for each faction.
*   **Content:**
    *   **Lore:** History of the faction.
    *   **Standing:** Current Rank and Reputation.
    *   **Rewards:** List of rewards for each rank (locked/unlocked status).

#### 🗺️ Exploration Atlas
*   **View:** List of known locations.
*   **Detail View:**
    *   **Name:** Location Name.
    *   **Description:** Zone lore.
    *   **Monsters:** List of monsters found here (links to Bestiary).
    *   **Resources:** List of gatherable materials.

#### 📜 Quest Log (Historical)
*   **View:** List of completed quests.
*   **Detail:** Summary of the quest and the reward received.

---

## Data Schema

### 1. Static Codex Data (`game_systems/codex/codex_data.py`)
This module will aggregate data from existing systems and add the Codex-specific layer (Lore).

```python
# Conceptual Structure
CODEX_DATA = {
    "monsters": {
        "monster_001": {
            "lore_extended": "Goblins... [Long Description]",
            "unlock_thresholds": {"basic": 1, "lore": 10, "stats": 1}
        },
        ...
    },
    "items": { ... },
    "locations": { ... }
}
```

### 2. Player Unlock Data (MongoDB: `player_codex`)
A new collection to track individual player progress.

```json
{
  "_id": ObjectId("..."),
  "discord_id": 123456789,
  "bestiary": {
    "monster_001": {
      "kills": 5,
      "seen_drops": ["item_goblin_ear"]
    },
    "monster_002": {
      "kills": 0, # Locked
      "seen_drops": []
    }
  },
  "items": {
    "item_iron_sword": { "count": 1, "discovered": true }
  },
  "locations": ["forest_outskirts", "whispering_thicket"],
  "factions": {
    "pathfinders": { "rank": 2, "reputation": 550 }
  },
  "quests": [1, 2, 5] # List of completed Quest IDs
}
```

---

## Unlock Triggers

### 📖 Bestiary
*   **Encounter:** Adds entry as "Seen" (Name revealed, stats hidden).
*   **First Kill:** Unlocks "Basic" entry (Lore, Habitat).
*   **Kill Count (e.g., 10):** Unlocks "Stats" (HP/ATK/DEF).
*   **Drop Acquisition:** Unlocks specific items in the "Drops" list.

### 🏺 Items
*   **Acquisition:** Unlocks entry when item is added to inventory (loot, craft, buy).
*   **Identification:** (Future) If unidentified items are added.

### 🗺️ Locations
*   **Visit:** Unlocks entry upon `start_adventure` in a new zone.
*   **Scouting:** (Future) "Scout" action could reveal potential monsters without fighting them.

### 🏛️ Factions
*   **Join:** Unlocks the faction entry.
*   **Rank Up:** Updates the entry with new lore/rewards.

### 📜 Quests
*   **Completion:** Adds to the log upon `quest_complete`.

---

## Integration with Other Agents

| Agent | Responsibility |
| :--- | :--- |
| **StoryWeaver** | Writes extended lore descriptions for Monsters, Factions, and Locations. |
| **GameForge** | Ensures new monsters/items have valid keys and basic descriptions in `data/`. |
| **DepthsWarden** | Provides dungeon floor lore and secrets for the Atlas. |
| **DataSteward** | Manages the `player_codex` MongoDB schema and migration. |
| **Palette** | Designs the specific Embed layouts and Iconography. |
| **ChronicleKeeper** | Adds Achievements related to Codex completion (e.g., "Scholar of the Depths"). |
| **CodexKeeper** | (Me) Oversees the `CodexManager` implementation and maintains the design. |

---

## Progress Tracking

*   **Global Completion:** Percentage of total entries unlocked.
*   **Category Completion:** Percentage per category.
*   **Badges/Titles:**
    *   `Novice Scholar`: 10% Completion.
    *   `Loremaster`: 100% Bestiary Completion.
    *   `Cartographer`: 100% Atlas Completion.

---

## Technical Considerations

1.  **Lazy Loading:** Do not load the entire `player_codex` document into memory unless the user opens the UI.
2.  **Batch Updates:**
    *   During combat/adventure, cache "new discoveries" in the `AdventureSession`.
    *   Flush updates to `player_codex` only when `end_adventure` is called to minimize DB writes.
3.  **Data Consistency:** Ensure `codex_data.py` keys match `monsters.py` keys exactly. Unit tests should verify this.

## Future Expansions
*   **Monster Weaknesses:** Unlocking elemental weakness info (Fire > Ice) after trying specific attacks.
*   **Community Goals:** "Global Kill Count" for bosses displayed in the Codex.
