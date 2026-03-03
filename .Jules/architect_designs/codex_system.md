# Expansion Design: The Eldoria Codex

## 🎯 Concept
**"Knowledge is the first weapon of the survivor."**

The Eldoria Codex is a living encyclopedia that fills as players explore, fight, and collect. It transforms the grind into a collection game, providing tangible rewards for mastering the world's content. It addresses player feedback for "More Lore" and provides a long-term goal for completionists.

## 📚 Structure
The Codex is divided into four main sections:
1.  **Bestiary**: A record of all monsters encountered.
2.  **Atlas**: A guide to discovered locations and their resources.
3.  **Armory**: A collection of all weapons, armor, and items found.
4.  **Legends**: A hall of fame for earned titles and achievements.

---

## 🦁 Bestiary: The Hunter's Log
Tracks every monster in `game_systems/data/monsters.json`.

### Research Tiers
Each monster has a "Research Level" based on kill count.
*   **Tier 0: Unknown (0 Kills)**
    *   Display: `???` (Name hidden), Image Silhouette.
*   **Tier 1: Sighted (1 Kill)**
    *   Display: Name, Image, Basic Description.
    *   *Reward:* +1% XP from this monster.
*   **Tier 2: Studied (10 Kills)**
    *   Display: HP, Attack, Defense, Elemental Weakness (if any).
    *   *Reward:* +2% XP, +1% Damage vs this monster.
*   **Tier 3: Researched (50 Kills)**
    *   Display: Skills (names & effects), Drop Table (Common/Uncommon items).
    *   *Reward:* +3% XP, +3% Damage.
*   **Tier 4: Mastered (100 Kills + Elite Variant if applicable)**
    *   Display: Full Lore Entry, Rare/Boss Drops, Spawn Locations.
    *   *Reward:* Title (e.g., "Goblin Bane"), +5% Damage, increased rare drop chance (1.1x).

### Data Integration
*   **Key:** Monster ID (e.g., `1`, `106`).
*   **Hook:** `CombatEngine.on_monster_death(player_id, monster_id)` triggers `CodexManager.add_kill(player_id, monster_id)`.

---

## 🗺️ Atlas: The Cartographer's Journal
Tracks locations defined in `game_systems/data/adventure_locations.py`.

### Discovery Status
*   **Undiscovered**: Hidden from list.
*   **Discovered**: Visited once. Shows Name, Emoji, Description.
*   **Surveyed**: Completed 10 expeditions. Shows "Common Monsters" and "Gatherables".
*   **Mapped**: Completed 50 expeditions + Found all "Special Events". Shows "Night Monsters" and "Boss Spawn Conditions".

### Data Integration
*   **Key:** Location Key (e.g., `forest_outskirts`).
*   **Hook:** `AdventureSession.complete_adventure(player_id, location_key)` updates visit count.

---

## ⚔️ Armory: The Collector's Vault
Tracks items from `equipments.json` and `consumables.json`.

### Collection Status
*   **Unseen**: Hidden.
*   **Seen**: Encountered (e.g., dropped but not picked up, or seen in shop). Shows Name/Type.
*   **Owned**: Currently or previously in inventory. Shows Full Stats, Flavor Text, Drop Source.

### Set Bonuses (Future Feature)
*   Collecting all items in a "Set" (e.g., "Molten Set") grants a cosmetic profile badge.

---

## 💾 Data Model (DatabaseManager)

### Collection: `player_codex`
```json
{
  "user_id": 123456789,
  "bestiary": {
    "1": {"kills": 45, "seen": true},
    "106": {"kills": 2, "seen": true}
  },
  "atlas": {
    "forest_outskirts": {"visits": 12, "events_found": ["hidden_stash"]}
  },
  "armory": {
    "gen_sword_001": {"owned": true, "first_acquired": "2026-02-24T12:00:00Z"}
  },
  "last_updated": "2026-02-24T12:00:00Z"
}
```

---

## 🛠️ Agent Assignments

### 📜 CodexKeeper (New Logic)
*   **Role:** Manages the `CodexCog` and UI.
*   **Tasks:**
    1.  Implement `/codex` command with subcommands (`monster [name]`, `location [name]`, `item [name]`).
    2.  Create `CodexEmbedBuilder` to generate dynamic pages based on Research Tier.
    3.  Implement "Research Progress" bars in embeds.

### 🗄️ DatabaseManager
*   **Task:** Create `get_codex(user_id)` and `update_codex(user_id, category, key, value)` methods.
*   **Optimization:** Ensure `codex` data is loaded lazily or cached, as it can get large.

### ⚔️ Tactician (Combat)
*   **Task:** In `CombatEngine._end_combat`, add a call to `CodexManager.record_kill(player_id, monster_id)`.
*   **Task:** In `DamageFormula`, add a check: `if Codex.get_tier(player, monster) >= 2: damage *= 1.01`.

### 🌍 AdventureSystem (Exploration)
*   **Task:** In `AdventureSession`, trigger `CodexManager.record_visit` upon completion.
*   **Task:** When a "Special Event" (e.g., finding a shrine) occurs, record it in the Codex.

### 🔨 GameForge (Content)
*   **Task:** Review `monsters.json` and ensure every monster has a `description` (Lore).
*   **Task:** Review `adventure_locations.py` and ensure descriptions are immersive.
*   **Task:** Create "Research Notes" items that drop from bosses (instantly add +5 kills to Codex count).

---

## 📅 Timeline & Success Criteria
*   **Phase 1 (Data):** DB Schema & Tracking Hooks. (1 Week)
*   **Phase 2 (UI):** Basic `/codex` command & Bestiary. (1 Week)
*   **Phase 3 (Integration):** Atlas & Armory + Combat Bonuses. (1 Week)

**Success Metric:** Players actively checking `/codex` to see drop rates and weaknesses.
