# ⏳ Timeweaver: Eldoria Quest Auto-Adventure Overhaul Design

## 🎯 Mission Objective
Transform Eldoria Quest's core gameplay loop from manual, turn-based exploration to a time-based auto-adventure experience. This design shifts progression to real-time expeditions while preserving the game's dark fantasy survival tone, material-driven economy, class identities, and guild progression. Players will make strategic choices regarding expedition length, risk level, and resource investment, and then wait real-world time to discover their fate.

---

## 1. 🔄 Core Loop

### 1.1 Starting an Adventure
*   **Command:** `/adventure depart` or interacting with a "Guild Expedition Board" button in the guild hall.
*   **UI (The Departure Board):** A rich embed containing:
    *   **Destination Selection:** Dropdown of available regions (unlocked via Guild Rank/Level).
    *   **Duration Selection:** Dropdown for expedition length (e.g., 30m, 2h, 8h, 24h).
    *   **Supply Allocation:** Options to allocate food, potions, and light sources (torches).
    *   **Risk/Reward Estimate:** Displays expected danger level, potential loot tiers, and required supplies.
*   **Action:** Clicking the "🚀 Depart" button locks the character into the adventure state.
*   **Limitations:** Only one active adventure per character at a time.

### 1.2 During the Adventure
*   **State Lock:** While adventuring, the character cannot engage in other active gameplay (duels, crafting, manual exploration).
*   **Status Tracking:** The `/adventure status` command shows a live-updating embed with:
    *   Current location and duration remaining.
    *   Estimated current HP/MP (calculated based on time elapsed).
    *   A brief "flavor" log of the most recent event (e.g., "Fending off a pack of Shadow Wolves...").
*   **Background Processing:** The bot does *not* simulate every step in real-time to save resources. Instead, it calculates the outcome either periodically in large batches or entirely upon completion.

### 1.3 Completion & Results
*   **Resolution:** When the timer expires, the `AdventureResolutionEngine` processes the entire expedition.
*   **Notification:** The bot sends a direct message (or pings the user in a designated channel) announcing the return.
*   **The Mission Report:** A detailed embed summarizing the expedition:
    *   **Outcome:** Triumphant Return, Bruised but Alive, or Critical Failure (Death).
    *   **Loot & Resources:** A consolidated list of all materials, items, Aurum, and XP gained.
    *   **Highlights:** Key events, elite monsters defeated, or rare items found.
    *   **Final Vitals:** The character's remaining HP and MP.

---

## 2. ⏳ Time Mechanics

### 2.1 Tracking Real Time
*   **Database Authority:** Adventures are recorded in an `adventure_sessions` collection/table with a `start_time`, `target_end_time`, and `duration_minutes`.
*   **Scheduler:** A background task (e.g., `discord.ext.tasks.loop` running every minute) queries for sessions where `target_end_time <= NOW()` and triggers their resolution.

### 2.2 Duration Tiers & Scaling
The length of the adventure dictates how deep into the region the player goes, affecting both risk and reward.

| Duration | Conceptual Depth | Encounter Density | Loot Rarity Modifier | Danger Multiplier |
| :--- | :--- | :--- | :--- | :--- |
| **30m (Scout)** | Outskirts / Floors 1-5 | Low | 1.0x Base | 1.0x Base |
| **2h (Patrol)** | Shallow / Floors 6-15 | Medium | 1.2x Base | 1.1x Base |
| **8h (Expedition)**| Deep / Floors 16-30 | High | 1.5x Base | 1.3x Base |
| **24h (Campaign)**| Abyss / Floors 31+ | Extreme | 2.0x Base | 1.6x Base |

*   **Fatigue:** Longer durations introduce a "Fatigue" debuff that steadily decreases combat effectiveness and increases damage taken over time, making 8h and 24h adventures significantly riskier without high stats or ample supplies.

### 2.3 Early Cancellation (Recall)
*   **Action:** Players can use a "🛑 Recall" button on the status embed to end the adventure prematurely.
*   **Consequences:**
    *   **Partial Rewards:** Only retain 50% of the loot and XP gathered up to the point of recall.
    *   **Supply Loss:** All allocated supplies are considered consumed and are not refunded.
    *   **Flavor:** "You sounded the retreat, dropping half your scavenged goods in the scramble to safety."

---

## 3. 🤖 Auto-Resolution Engine

To maintain performance, the engine uses a deterministic, statistical model rather than simulating every individual turn of combat.

### 3.1 Exploration Simulation
*   **Tick Rate:** The adventure is divided into conceptual "ticks" (e.g., 1 tick = 5 minutes).
*   **Event Generation:** For each tick, an event is rolled based on the location's event tables (Combat, Gathering, Discovery, Trap).
    *   Event probabilities shift based on the location's Danger Level and the current conceptual depth (duration elapsed).

### 3.2 Automated Combat
*   **Power Abstraction:** Calculate an "Offensive Rating" (DPS based on stats, weapon, and equipped skills) and "Defensive Rating" (Damage Mitigation based on armor and stats) for both the player and the encountered monster.
*   **Deterministic Clash:**
    *   Determine "Turns to Kill" (Monster HP / Player DPS).
    *   Calculate "Damage Taken" (Turns to Kill * Monster DPS * Defensive Mitigation).
*   **Variance:** Apply a small RNG factor (±10%) to the final damage taken to represent crits or dodges.
*   **Resource Consumption:** Deduct calculated damage from the player's simulated HP pool. If HP drops below a threshold (e.g., 30%) and the player allocated potions, a potion is consumed to restore HP.

### 3.3 Death & Failure
If the player's simulated HP reaches 0 during the resolution:
*   **State:** The adventure immediately halts at that tick.
*   **Grimwarden's Toll (Death Penalty):**
    *   The player is returned to town with 1 HP.
    *   All loot gathered during the expedition is lost.
    *   A portion of carried Aurum (e.g., 5%) is lost to scavengers.
    *   All allocated supplies are lost.
*   **Narrative:** The mission report is bleak, describing how the player barely escaped with their life and had to abandon their pack.

---

## 4. 🔗 Integration with Existing Systems

### 4.1 Dungeon Floors (DepthsWarden)
*   Regions in `adventure_locations.json` need a defined `danger_level` and `floor_depth_ranges`.
*   The system uses these ranges to pull appropriate monsters and events from existing tables based on the selected duration.

### 4.2 Inventory & Supplies
*   Players must physically possess supplies (Food, Potions, Torches) to allocate them to an expedition.
*   Allocated supplies are temporarily removed from the main inventory and placed in an "Expedition Pack."
*   Unused supplies (e.g., unconsumed potions) are returned upon successful completion.

### 4.3 Economy & Loot (GameBalancer)
*   Drop rates must be carefully tuned. While auto-adventuring provides passive income, the *rate per hour* should be lower than active, manual play to ensure active engagement is still rewarding.
*   Auto-adventuring should be the primary source of bulk common/uncommon materials, while manual boss fights or specific quests are required for top-tier items.

### 4.4 Guild Ranks (ProgressionBalancer)
*   Higher durations and more dangerous regions are gated by Guild Rank.
    *   Rank F: Limited to 30m / 2h in starting zones.
    *   Rank C: Unlocks 8h expeditions in dangerous zones.
    *   Rank A/S: Unlocks 24h campaigns in the Abyss.
*   Auto-adventures grant Rank Points (RP) to contribute to guild promotion, scaling with duration and difficulty.

### 4.5 Factions
*   **Passive Reputation:** Players gain base faction reputation continuously while adventuring (e.g., 1 Rep per hour).
*   **Favored Terrain:** If a player adventures in a region favored by their active faction, reputation gains are multiplied by 1.5x.

### 4.6 Achievements
*   **Time-Based Feats:**
    *   *Day Tripper:* Complete a 30m adventure.
    *   *Endurance Runner:* Complete an 8h adventure.
    *   *Sleepless in Eldoria:* Complete a 24h campaign.
*   **Survival Feats:**
    *   *Close Call:* Survive an adventure returning with less than 5% HP.
    *   *Iron Stomach:* Complete a 24h campaign without packing rations.

### 4.7 Skills & Classes (Tactician)
*   Class identities influence the auto-resolution stats:
    *   **Warrior:** High Defensive Rating, reduces fatigue penalties.
    *   **Rogue:** Increased evasion (less damage taken), higher chance to find rare gathering nodes.
    *   **Mage:** High Offensive Rating (kills faster, taking less damage over time), but fragile if hit.
    *   **Cleric:** Innate HP regeneration between ticks, reducing potion reliance.

---

## 5. 📱 UI/UX Specifications

Following the **One UI Policy**, interactions should primarily edit existing messages rather than creating new ones.

### 5.1 The Expedition Board View (`setup_view.py`)
*   **Dropdowns:**
    1.  Select Location.
    2.  Select Duration (30m, 2h, 8h, 24h).
*   **Buttons:**
    *   `[ + Potion ]` `[ - Potion ]` (Adjust potion allocation)
    *   `[ + Torch ]` `[ - Torch ]` (Adjust torch allocation)
    *   `[ 🚀 Depart ]` (Confirms and starts)
*   **Embed Updates:** As the user changes selections, the embed updates to show required level, estimated danger, and supply cost.

### 5.2 Status View (`status_view.py`)
*   Accessed via `/adventure status`.
*   Displays a progress bar (text-based, e.g., `[██████░░░░] 60%`) and estimated time remaining.
*   Button: `[ 🛑 Recall ]`. Clicking this edits the message to a confirmation prompt: "Are you sure? You will lose 50% of your loot. `[ Confirm ]` `[ Cancel ]`".

### 5.3 Mission Report Embed (`adventure_embeds.py`)
*   A visually distinct embed sent upon completion.
*   Uses color coding (Green = Success, Orange = Recalled, Red = Defeated).
*   Sections: `Adventure Summary`, `Loot Acquired`, `Experience & Wealth`, `Vitals`.

---

## 6. ⚖️ Balance & Anti-Abuse Measures

*   **Concurrency Limit:** Strictly one active adventure per player. Attempting to start another returns an error.
*   **Reward Scaling:** Loot tables for auto-adventures apply a `0.8x` multiplier compared to manual drops to preserve the premium on active play.
*   **The "Overnight" Problem:** 8h and 24h adventures require significant supply investment. A player cannot just spam 24h adventures without first actively gathering or buying the necessary food and potions.
*   **Stamina/Energy:** To prevent infinite looping, characters might require a "Rest Period" in town equal to 10% of their expedition duration before departing again.

---

## 7. 🛠️ Technical Requirements

### 7.1 Database Schema
**Collection/Table:** `adventure_sessions`
```json
{
  "user_id": 123456789,
  "location_id": "whispering_forest",
  "status": "active", // active, completed, failed, recalled
  "start_time": "2023-10-27T10:00:00Z",
  "end_time": "2023-10-27T12:00:00Z",
  "duration_minutes": 120,
  "hp_current": 150,
  "mp_current": 50,
  "supplies": {
    "potions": 3,
    "torches": 1
  },
  "loot_cache": {},
  "log": []
}
```

### 7.2 Scheduler & Bot Restarts
*   A `discord.ext.tasks.loop` runs every 60 seconds to find sessions where `end_time <= NOW()` and `status == "active"`.
*   **Crash Recovery:** Because the state is entirely DB-driven, if the bot restarts, it will simply resume checking the scheduler loop. Any sessions that completed while the bot was offline will be immediately processed and the user notified.

### 7.3 Discord Interaction Timeouts
*   Resolving a 24h adventure in one batch might take > 3 seconds, leading to a Discord "Interaction Failed" error if triggered by a user action (like `/status`).
*   **Solution:** All long-running calculations must use `await interaction.response.defer()` immediately.
*   The background scheduler runs independently of interactions, so it will naturally avoid the 3-second limit, safely DMing the user when done.

---

## 8. 🤝 Coordination Notes for Other Agents

*   **@SystemSmith:** Build the database schema (`adventure_sessions`) in section 7.1 and the background scheduler (`discord.ext.tasks.loop`) to process completions. Ensure robust crash recovery (if the bot restarts, it should pick up missed completions). Ensure `defer()` is used correctly.
*   **@DataSteward:** Update `adventure_locations.json` with `danger_level` and tier data. Define the abstract loot tables for auto-resolution.
*   **@Tactician:** Develop the statistical combat abstraction model. We cannot use the full turn-based combat engine for background processing; we need a fast, deterministic formula comparing player stats to monster stats.
*   **@GameBalancer:** Tune the drop rates, XP yields, and the Fatigue debuff scaling for longer durations.
*   **@Grimwarden:** Implement the death penalty logic within the resolution engine. Ensure the loss of loot and supplies feels punishing but fair.
*   **@Palette:** Design the rich embeds for the Expedition Board, Status, and Mission Reports. Ensure compliance with the One UI policy.
*   **@DepthsWarden:** Map out which existing monsters and events correspond to the conceptual "depths" of the different duration tiers.
*   **@GameForge:** Create new destination descriptions and special event items related to auto-adventures.
*   **@StoryWeaver:** Write immersive result narratives for the Mission Report.
*   **@ChronicleKeeper:** Add achievements for time-based feats.
*   **@ProgressionBalancer:** Integrate auto-adventure progress into rank advancement.
*   **@BugHunter:** Test edge cases (timeouts, multiple concurrent).
*   **@Visionary:** Overall priority and player feedback.

---

## 9. 🔮 Future Expansions (Phase 2+)

*   **Party Expeditions:** Allow players to form groups. The system averages their stats and resolves the adventure for the whole party, splitting loot.
*   **Mercenary System:** Hire NPC companions to boost stats for difficult campaigns.
*   **Dynamic Weather/Seasons:** Weather conditions at the time of departure (or changing during a 24h campaign) impact the difficulty and loot tables.
*   **Special Events:** Occasional "Raid Targets" appear on the board requiring a 24h commitment from multiple guild members to defeat.
