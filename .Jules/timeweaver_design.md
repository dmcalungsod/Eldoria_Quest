# ⏳ Timeweaver: Auto-Adventure Overhaul Design

## 1. Overview & Goals
**Mission:** Transform Eldoria Quest from a manual turn-based exploration system into a time-based auto-adventure experience.
**Core Idea:** Players dispatch their characters on expeditions that resolve in real-time. Upon return, they receive a detailed report of their journey, including battles fought, loot gathered, and any injuries sustained.

**Goals:**
*   **Respect Player Time:** Shift from active grinding to strategic management.
*   **Deepen Strategy:** Choices (Duration, Location, Supplies) matter more than button mashing.
*   **Preserve Tone:** Maintain the dark fantasy survival feel through risk of failure and resource scarcity.
*   **Scalability:** Design a system that can handle thousands of concurrent adventures without lag.

## 2. Core Player Flow

### A. Starting an Adventure
1.  **Command:** `/adventure`
2.  **UI:** An embed displays available locations (unlocked by Rank/Level).
    *   **Dropdown:** Select Destination (e.g., "🌲 Willowcreek Outskirts").
    *   **Dropdown:** Select Duration (e.g., "Short (30m)", "Long (8h)").
    *   **Button:** "Embark" (Starts the timer).
3.  **Feedback:** Bot confirms: *"You venture into the wilds. Return in 30 minutes."*

### B. The Journey (Passive)
*   The character is locked in the `adventure_sessions` database.
*   Status commands (`/status`, `/profile`) show: *"Currently Adventuring in [Location] (Returns: [Time])"*
*   Players cannot duel, craft, or change gear while adventuring.

### C. Cancellation (Retreating Early)
*   **Action:** Players can use `/adventure cancel` or click a "Retreat" button on the status embed.
*   **Consequence:** The adventure is resolved immediately up to the current time elapsed.
*   **Penalty:**
    *   **Loot:** 50% of loot gathered so far is lost (dropped in haste).
    *   **XP:** 50% XP penalty.
    *   **Cooldown:** Player cannot embark again for 15 minutes (to prevent spamming short cancels).
    *   *Reasoning:* Prevents players from checking for "good RNG" starts and cancelling immediately, while allowing legitimate retreats if they need their character for a raid/event.

### D. Completion & Results
1.  **Notification:** When the timer expires, the bot sends a DM or pings in a specific channel: *"Your adventure in Willowcreek is complete!"*
2.  **Claim:** Player uses `/adventure` again or clicks "Complete" on the notification.
3.  **Resolution:** The bot calculates the entire journey's outcome instantly based on stats + RNG.
4.  **Report:** An embed summarizes:
    *   **Encounters:** "Defeated 5 Goblins, fled from 1 Elite."
    *   **Loot:** List of materials/items found.
    *   **Vitals:** HP/MP lost (or gained via regen).
    *   **Rewards:** XP, Aurum, Reputation.

## 3. Adventure Resolution Engine
The engine simulates the adventure in "Steps" to ensure consistency and fairness.

**Simulation Logic:**
1.  **Calculate Steps:** `Steps = Duration (min) / 15`. (e.g., 60m = 4 steps).
2.  **Iterate Steps:** For each step:
    *   **Event Roll:** Roll d100.
        *   01-10: **Rare Event** (Treasure, Trap, NPC).
        *   11-50: **Combat** (Draw monster from location pool).
        *   51-80: **Gathering** (Materials based on location).
        *   81-100: **Quiet** (Regen HP/MP).
    *   **Resolution:**
        *   *Combat:* Compare Player Power vs. Monster Power. Calculate damage taken and loot dropped. If HP < 0, **Retreat**.
        *   *Gathering:* Add items to temporary loot bag.
        *   *Event:* Apply specific logic (e.g., "Found Shrine: +Buff").
3.  **Retreat Condition:** If Player HP drops to 0 during any step:
    *   Adventure ends immediately at that step.
    *   **Penalty:** 50% of gathered loot is lost. 10% Aurum lost. Player returns with 1 HP.
    *   Status: "Failed (Rescued by Guild)".

## 4. Time & Scheduling
**Tracking:**
*   **Database:** `adventure_sessions` collection.
    *   Fields: `discord_id`, `start_time`, `end_time`, `duration_minutes`, `location_id`, `active` (1).
*   **Scheduler:** A background task (`cogs/adventure_loop.py`) runs every minute.
    *   Query: `db.get_adventures_ending_before(now)`
    *   Action: Mark `notification_sent = True` (if not already), send DM/Ping.
    *   *Note:* We do NOT auto-resolve. The player must "Claim" to trigger the heavy calculation and see the result. This prevents DB locking issues and ensures the player sees the result.

**Durations:**
*   **Quick (30m):** 2 Steps. Low risk. Good for dailies.
*   **Standard (2h):** 8 Steps. Standard rewards.
*   **Long (8h):** 32 Steps. High risk (cumulative damage), but high reward (deeper floor loot tables).
*   **Expedition (24h):** 96 Steps. Only for well-geared players.

## 5. Risk & Reward Tables
**Risk Scaling:**
*   **Fatigue:** For adventures > 4 hours, enemy damage increases by 5% per hour.
*   **Supplies:** Players can equip "Rations" (consumables) to auto-heal between steps.

**Reward Scaling:**
*   **Deep Loot:** Steps beyond #20 (5 hours) have a 2x chance for Rare materials.
*   **Experience:** Base XP per step + Bonus for completion.

## 6. Integration with Existing Systems
*   **Inventory:** Loot is added directly to inventory upon "Claim". Overflow items are discarded or put in a temporary "overflow" stash (if implemented).
*   **Economy:**
    *   *Input:* Materials from adventures.
    *   *Sink:* Crafting, Repairs, Guild Projects.
    *   *Balance:* Adjust drop rates in `adventure_locations.py` if inflation occurs.
*   **Guilds:**
    *   **Rank:** Adventure completion counts towards "Quests Completed" or a new "Expeditions" metric.
    *   **Reputation:** Granted based on duration and location difficulty.
*   **Dungeon Floors:**
    *   Higher floors = Higher difficulty locations.
    *   "Floors" can be represented as different Location IDs (e.g., `dungeon_floor_1`, `dungeon_floor_5`).
*   **Achievements & Factions:**
    *   **Achievements:** New time-based badges (e.g., "The Wanderer" for 100h total adventure time, "Iron Lung" for completing 24h expedition without dying).
    *   **Factions:** Factions may control certain zones. Adventuring in a zone controlled by an opposing faction increases combat risk but grants specific Faction Reputation.

## 7. UI/UX Specifications

### Adventure Start Embed
**Title:** 🌲 Willowcreek Outskirts
**Description:** *The safe edge of the forest. Slimes and weak goblins lurk here.*
**Fields:**
*   **Difficulty:** ⭐ (Rank F)
*   **Est. Duration:** 30m - 8h
*   **Supplies:** [Rations: 0] [Torches: 0]

**Components:**
*   `SelectMenu` (Duration): "30 Minutes", "1 Hour", "4 Hours", "8 Hours"
*   `Button` (Green): "Embark"
*   `Button` (Grey): "Change Location"

### Adventure Report Embed
**Title:** 📜 Adventure Report: Willowcreek
**Description:** *You return weary but triumphant.*
**Fields:**
*   **Summary:** 8 Steps | 4 Battles | 3 Harvests
*   **Loot:** 🪵 Ancient Wood (x5), 🌿 Herb (x3)
*   **XP/Aurum:** +150 XP | +50 🪙
*   **Health:** 100/100 HP (Used 1 Ration)

## 8. Database Schema
**Collection:** `adventure_sessions` (Update)
```json
{
  "discord_id": 123456789,
  "location_id": "forest_outskirts",
  "start_time": "ISO-8601",
  "end_time": "ISO-8601",
  "duration_minutes": 60,
  "active": 1,
  "status": "in_progress", // or "completed", "claimed"
  "supplies": {
      "rations": 2,
      "torches": 1
  },
  "log": [] // Only for specialized debugging, main log generated at end
}
```

## 9. Technical Implementation Plan
**Phase 1: Database & Logic (SystemSmith)**
*   Update `AdventureManager` to handle time-based starts.
*   Implement `AdventureResolutionEngine` class.
*   Update `DatabaseManager` schema.

**Phase 2: UI & Commands (Palette)**
*   Create `AdventureSetupView`.
*   Create `AdventureReportEmbed`.
*   Update `/adventure` command.

**Phase 3: Background Tasks (SystemSmith)**
*   Implement `check_adventure_completion` loop.
*   Add notification logic.

**Phase 4: Integration (GameBalancer)**
*   Tune drop rates for time-based yields.
*   Adjust monster damage for auto-resolution balance.

## 10. Balance & Tuning Guidelines
*   **Initial Tuning:** Aim for 80% success rate for on-level content without supplies.
*   **Supply Usage:** Rations should be almost mandatory for Long (8h) adventures.
*   **XP Rate:** Auto-adventure XP/hour should be ~60% of active manual play to encourage active play but reward idle time.

## 11. Future Expansions
*   **Party Adventures:** Send multiple characters (alts or guildmates).
*   **Dynamic Events:** "Goblin Raid" event boosts loot for 24h.
*   **Caravans:** Trade missions (High risk, High Aurum, No XP).

## 12. Agent Coordination
This design overhaul touches every system. Assignments are as follows:

*   **GameForge:** Design new adventure locations (e.g., specialized resource nodes) and event tables.
*   **DepthsWarden:** Map Dungeon Floors 1-100 to Adventure Duration/Difficulty tiers. Provide monster pools for deep delves.
*   **Tactician:** Provide the combat formulas for the `Resolution Engine`. Needs to be stateless (Power Rating vs. Monster Rating).
*   **GameBalancer:** Calibrate the economy. Ensure the influx of materials from 8h adventures doesn't crash the market. Adjust "Fatigue" penalties.
*   **ProgressionBalancer:** Set Rank requirements for new adventure durations (e.g., 24h unlocks at Rank A).
*   **Grimwarden:** Define death penalties and "Rescue" mechanics. Ensure the "Survival" tone persists even in auto-mode.
*   **StoryWeaver:** Write flavor text for the Adventure Reports (e.g., "You narrowly escaped a rockslide", "The campfire burned low...").
*   **ChronicleKeeper:** Create new Achievements for time milestones (e.g., "The Marathoner").
*   **Equipper:** Design "Travel Supplies" (Rations, Tent, Torches) that boost success rates.
*   **DataSteward:** Manage the static data files for `LOCATIONS` and `LOOT_TABLES`.
*   **SystemSmith:** Lead developer for the Scheduler, Database schema updates, and Background Task Loop.
*   **Palette:** Design the "Start Adventure" and "Adventure Report" embeds/views.
*   **BugHunter:** Stress test the scheduler with simulated 10k users. Test "Cancel" mechanics for exploits.
*   **Visionary:** Oversee the transition from manual to auto, gathering player feedback to adjust "Fun vs. Wait" balance.
