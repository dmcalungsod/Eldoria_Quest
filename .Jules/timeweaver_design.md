# ⏳ Timeweaver: Auto-Adventure Overhaul Design

**Project:** Eldoria Quest - Chronos Engine
**Agent:** Timeweaver
**Version:** 1.0.0
**Status:** Draft

---

## 1. 🎯 Executive Summary
The **Chronos Engine** transforms Eldoria Quest's adventure system from a manual, turn-based grind into a strategic, time-based idle experience. Players will dispatch their characters on expeditions of varying lengths, investing real time and resources to reap rewards. This shift respects the player's time while deepening the strategic layer of preparation (supplies, gear) and risk management (duration, location depth).

**Core Philosophy:** "Time is the ultimate resource. Spend it wisely."

---

## 2. 🔄 The Core Loop

### 2.1 Starting an Adventure
Players initiate an adventure via the `/adventure` command or a persistent "Depart" button in the Guild Hub.

1.  **Select Location:** Dropdown menu filtered by the player's Guild Rank and Level.
    *   *Constraint:* Must meet minimum requirements (e.g., Rank F for "Whispering Forest").
2.  **Select Duration:** Players choose how long to commit their character.
    *   **Scout (30m):** Low risk, shallow exploration (Floors 1-5). Good for materials.
    *   **Patrol (2h):** Moderate risk, medium exploration (Floors 6-15). Balanced XP/Loot.
    *   **Expedition (8h):** High risk, deep exploration (Floors 16-30). Best for rare drops.
    *   **Raid (24h):** Extreme risk, abyss exploration (Floors 31+). Legendary potential.
3.  **Equip Supplies:** Players select a "Supply Loadout" from their inventory.
    *   **Rations:** Required for stamina. 1 Ration per hour of travel. Failure to supply results in "Exhaustion" (stat penalties).
    *   **Torches:** Reduces ambush chance in dark zones/night. 1 Torch per 2 hours.
    *   **Potions:** Auto-consumed when HP < 30%.
4.  **Confirm & Depart:** The bot calculates the return time, deducts supplies, and locks the character state.

### 2.2 Active State
While adventuring, the character is **locked**.
*   Cannot duel, trade, or craft.
*   Profile status shows: "Adventuring in [Location] (Return: [Time])".
*   Players can check status via `/status` to see a "live" log snippet (e.g., "Currently fighting a Goblin Scout...").

### 2.3 Completion & Results
When the timer expires:
1.  **Notification:** The bot DMs the player or pings them in the adventure channel.
2.  **Report Card:** A rich embed summary is generated.
    *   **Outcome:** Success / Failure / Emergency Retreat.
    *   **Loot:** List of gathered materials and drops.
    *   **XP/Aurum:** Total gains.
    *   **Combat Log:** A collapsible or summarized view of key battles (Elites/Bosses).
    *   **Vitals:** Ending HP/MP.

---

## 3. ⏳ Time Mechanics & Risk

### 3.1 Time Tracking
*   **Server-Side Authority:** Time is tracked using UTC timestamps in the database (`start_time`, `end_time`).
*   **Resolution:** The background scheduler checks for completed adventures every 60 seconds.

### 3.2 Duration Scaling
Longer adventures aren't just "more time" — they are **deeper dives**.

| Duration | Floors | Monster Tier Odds | Event Density | Fatigue Modifier |
| :--- | :--- | :--- | :--- | :--- |
| **30m** | 1-5 | 90% Normal / 10% Elite | Low | 1.0x |
| **2h** | 6-15 | 80% Normal / 20% Elite | Medium | 1.1x |
| **8h** | 16-30 | 70% Normal / 25% Elite / 5% Boss | High | 1.25x |
| **24h** | 31+ | 60% Normal / 30% Elite / 10% Boss | Extreme | 1.5x |

*   **Fatigue Modifier:** Increases damage taken and reduces accuracy as time goes on, simulating exhaustion.

### 3.3 Cancellation (Recall)
Players can use a "Recall" button to end an adventure early.
*   **Penalty:** The character "flees" back to town.
    *   **Loot:** 50% of gathered items are lost (dropped in panic).
    *   **XP:** 50% of earned XP is retained.
    *   **Supplies:** Consumed supplies are not refunded.

---

## 4. 🤖 Auto-Resolution Engine

The engine simulates the adventure in "ticks" (virtual steps), but processes them in batches for performance.

### 4.1 Simulation Logic
*   **Tick Rate:** 1 Tick = 1 Minute of real time.
*   **Event Roll:** Every tick, roll for an event (Combat, Gathering, Trap, Empty).
    *   *Base Chance:* 10% Combat, 20% Gathering, 5% Trap, 65% Walking.
    *   *Modifiers:* "Danger Level" of the location increases Combat chance.

### 4.2 Automated Combat
Instead of full turn-by-turn simulation (which is CPU intensive), use a **Deterministic Combat Model**:
1.  **Matchup:** Player Stats vs. Monster Stats (from `monsters.json`).
2.  **Damage Output (DPS):** Calculate average player damage per round (Attack + Skill Avg).
3.  **Damage Intake (DTPS):** Calculate average monster damage per round (Monster Atk - Player Def).
4.  **Resolution:**
    *   `Turns to Kill = MonsterHP / PlayerDPS`
    *   `Total Damage Taken = Turns to Kill * MonsterDTPS`
5.  **Variance:** Apply a ±10% RNG factor to simulate crits/dodges.
6.  **Resource Usage:**
    *   Deduct HP.
    *   If HP < 30%, consume Potion (if equipped).
    *   If HP <= 0, trigger **Death**.

### 4.3 Death & Failure
If HP hits 0:
*   **State:** Adventure ends immediately. Status becomes "Defeated".
*   **Penalty (Standard):**
    *   **Aurum:** -10% of total held (not just gained).
    *   **Materials:** -50% of *gathered* loot (bag is torn).
    *   **XP:** -100% of XP gained *this session*.
    *   **Flavor:** "You crawl back to the guild hall, battered and empty-handed."

---

## 5. 🔗 System Integration

### 5.1 Dungeon Floors (DepthsWarden)
*   Adventures map directly to **Floor Ranges**.
*   *Design Note:* Use the existing `adventure_locations.json` but add a `floor_depth` property to scale difficulty dynamically.

### 5.2 Inventory (InventoryManager)
*   **Supply Bag:** A new "virtual slot" for adventures.
    *   *Inputs:* Rations, Torches, Potions.
    *   *Consumption:* Deducted at start.
*   **Loot Bag:** Temporary storage during adventure. Transferred to main inventory upon "Claim Rewards".

### 5.3 Economy (GameBalancer)
*   **Loot Tables:** Must be tuned so 8h AFK != 8h Manual Play.
    *   *Auto Penalty:* Drop rates for rares should be slightly lower (e.g., 80% of manual rate) to preserve the value of active play.
*   **Aurum:** Generated from monster kills standardly.

### 5.4 Rank & Progression (ProgressionBalancer)
*   **Rank Gating:**
    *   Rank F: Scout only.
    *   Rank E: Scout, Patrol.
    *   Rank D: All durations.
*   **Rank Points:** Auto-adventures grant Rank Points (RP) but at a slower rate than manual Quests.

### 5.5 Skills & Classes (Tactician)
*   **Class Traits:**
    *   *Warrior:* -10% Fatigue buildup.
    *   *Rogue:* +10% Loot rarity.
    *   *Mage:* +10% XP gain.
    *   *Cleric:* Auto-heal 5% HP per hour.

### 5.6 Factions (FactionSystem)
*   **Time-Based Reputation:** Players gain 1 Reputation Point per hour spent adventuring.
*   **Favored Locations:** Each Faction has "Favored Locations" (e.g., Pathfinders favor "Whispering Forest"). Adventuring there grants +50% Reputation gain.
*   **Faction Orders:** Special "Faction Requests" may appear as events, offering bonus Rep for specific kills during auto-adventure.

### 5.7 Achievements (ChronicleKeeper)
*   **Endurance Feats:**
    *   *Day Tripper:* Complete a 1-hour adventure.
    *   *Marathoner:* Complete an 8-hour adventure.
    *   *Iron Soul:* Complete a 24-hour adventure without using potions.
*   **Exploration Feats:**
    *   *Cartographer:* Accumulate 100 hours of exploration time.
    *   *Survivor:* Survive 10 consecutive expeditions without death.

---

## 6. 📱 UI/UX Design

### 6.1 The Departure Board (Embed)
*   **Title:** 🗺️ Expedition Planning
*   **Fields:**
    *   **Location:** [Select Menu]
    *   **Duration:** [Select Menu]
    *   **Supplies:** [Button: Auto-Fill] (Fills with best available)
    *   **Risk Estimate:** "⚠️ High Risk (Recommended Level: 15)"
*   **Action:** [Button: 🚀 Depart]

### 6.2 Status Command (`/status`)
*   **Embed:**
    *   **Status:** ⚔️ Fighting (Goblin Scout)
    *   **Time:** 01:15:00 / 02:00:00
    *   **HP:** 75% | **MP:** 40%
    *   **Loot:** 12x Iron Ore, 3x Goblin Ear
*   **Action:** [Button: 🛑 Recall]

### 6.3 Mission Report (DM/Channel)
*   **Title:** 📜 Expedition Report: Whispering Forest
*   **Color:** Green (Success) / Red (Failure)
*   **Visual:** ASCII art or small image of the location.
*   **Summary:** "You explored 12 floors, defeated 45 enemies, and found 1 rare item."
*   **Rewards:** [List]

---

## 7. ⚖️ Balance Considerations

*   **Anti-Inflation:** To prevent AFK economy flooding, we limit **Concurrent Adventures** to 1 per player.
*   **Time-Gating:** A cooldown of 1 hour between "Raid" (24h) adventures.
*   **Active vs Passive:** Manual play should always yield *more* per minute, but Auto play yields *more* per day (since it runs while sleeping).

---

## 8. 🛠️ Technical Specifications

### 8.1 Database Schema
**Table:** `adventure_sessions`
```sql
CREATE TABLE adventure_sessions (
    session_id SERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL,
    location_id VARCHAR(50) NOT NULL,
    start_time TIMESTAMP NOT NULL,
    end_time TIMESTAMP NOT NULL,
    duration_minutes INT NOT NULL,
    status VARCHAR(20) DEFAULT 'active', -- active, completed, failed, recalled
    hp_current INT NOT NULL,
    mp_current INT NOT NULL,
    supplies JSONB DEFAULT '{}', -- {"ration": 2, "torch": 1}
    log JSONB DEFAULT '[]', -- Stores key events for report
    loot_cache JSONB DEFAULT '{}'
);
```

### 8.2 Scheduler (SystemSmith)
*   **Loop:** `tasks.loop(minutes=1)`
*   **Logic:**
    1.  Query `adventure_sessions` where `end_time <= NOW()` AND `status = 'active'`.
    2.  For each, run `ResolutionEngine.finalize()`.
    3.  Update DB status to `completed`.
    4.  Notify user.

### 8.3 Interaction Handling
*   **Buttons:** Must handle "Interaction Failed" gracefully if the bot restarts.
*   **Persistence:** State is purely DB-driven. Bot restart does not kill adventures.

---

## 9. 🤝 Agent Coordination

*   **@SystemSmith:** Implement the `adventure_sessions` table and the background `tasks.loop`. Ensure timezone handling is UTC.
*   **@DataSteward:** Update `adventure_locations.json` to include `floor_depth` and `danger_level` fields.
*   **@Tactician:** Implement `CombatEngine.simulate_encounter(player, monster)` — the deterministic version of combat.
*   **@Palette:** Design the "Departure Board" and "Mission Report" embeds. Use standard emoji sets.
*   **@GameBalancer:** Tune the `Fatigue Modifier` and `Loot Drop Rates` for auto-sessions.
*   **@Grimwarden:** Implement the Death Penalty logic (-10% Aurum, -50% Loot) within the `ResolutionEngine`.
*   **@StoryWeaver:** Write flavor text templates for "Adventure Log" events (e.g., "Found a hidden cache...", "Ambushed by shadows...").
*   **@ChronicleKeeper:** Create the new Achievements (`Day Tripper`, `Marathoner`) in `achievement_system.py`.
*   **@ProgressionBalancer:** Define the Rank Point (RP) yield per hour for each adventure tier.
*   **@GameForge:** Create the new Supply items (`Ration`, `Pitch Torch`) in `recipes.py`.
*   **@DepthsWarden:** Map current locations to specific "Floor Depths" (1-5, 6-15, etc.) for difficulty scaling.
*   **@BugHunter:** Stress test the scheduler with 100+ concurrent simulated sessions.
*   **@Visionary:** Review the final "Risk vs. Reward" balance to ensure manual play remains viable.

---

## 10. 🔮 Future Expansions
*   **Party System:** Allow players to form a squad (Tank/Healer/DPS) for better odds.
*   **Mercenaries:** Hire NPCs to fill party slots.
*   **Seasons:** "Winter" season increases supply consumption (Cold).
