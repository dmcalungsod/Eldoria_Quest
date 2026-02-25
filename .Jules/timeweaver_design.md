# ⏳ Time-Based Auto-Adventure System Design

**Author:** Timeweaver (Architect Agent)
**Date:** 2024-10-24
**Status:** Design Proposal
**Target:** Eldoria Quest Core Loop Overhaul

---

## 1. 🎯 Executive Summary
The goal of this overhaul is to transition Eldoria Quest's primary gameplay loop from manual, command-heavy exploration to a deep, strategic **idle/auto-adventure** system. This shift respects the player's time while maintaining the gritty, high-stakes survival atmosphere of Eldoria. Players will act as expedition leaders, preparing their characters for journeys into the unknown, managing risk, supplies, and duration, then reaping the rewards (or suffering the consequences) upon their return.

---

## 2. 🔄 Core Gameplay Loop

### 2.1 The "Expedition" Flow
1.  **Preparation (Manual):**
    *   Player accesses the **Adventure Board** (via UI/Button).
    *   Selects a **Destination** (unlocked by Rank/Quest).
    *   Selects an **Expedition Tier** (Duration & Risk).
    *   Selects a **Stance** (Aggressive, Defensive, Cautious).
    *   Equips **Supplies** (Food, Torches, Potions).
    *   Confirms launch.
2.  **The Journey (Idle):**
    *   The character is "Away" for the selected real-time duration.
    *   The server simulates progress in **15-minute intervals** (Steps).
    *   Players can check status via a dashboard but cannot intervene directly without aborting.
3.  **Resolution (Notification):**
    *   When time elapses (or the character retreats/dies), the player receives a notification.
    *   A comprehensive **Adventure Report** details the journey.
4.  **Rewards & Recovery (Manual):**
    *   Player claims loot, XP, and currency.
    *   Player manages injuries, repairs gear, and restocks for the next run.

### 2.2 Concurrent Adventures
*   **Base Limit:** 1 Active Adventure per Character.
*   **Future Expansion:** Potential for "Mercenary Contracts" to send secondary characters or NPCs (requires Guild update).

---

## 3. ⏳ Time Mechanics

### 3.1 Real-Time Durations (Expedition Tiers)
Instead of a slider, we offer distinct Tiers with specific risk profiles:

| Tier Name | Duration | Risk Multiplier | Step Count | Recommended For |
| :--- | :--- | :--- | :--- | :--- |
| **Scout** | 30 Minutes | 0.5x (Low) | 2 | Gathering Materials, Testing Gear |
| **Patrol** | 2 Hours | 1.0x (Normal) | 8 | Standard XP, Daily Quests |
| **Expedition**| 8 Hours | 1.5x (High) | 32 | Rare Loot, Boss Encounters, Rank Ups |
| **Odyssey** | 24 Hours | 2.5x (Extreme) | 96 | Legendary Artifacts, Deep Dungeon Dives |

### 3.2 Time Tracking
*   **Server-Side:** Start Time and End Time are stored in the database (`adventure_sessions`).
*   **Check-ins:** The `AdventureLoop` checks for completion every minute.
*   **Early Recall:** Players can abort an adventure early.
    *   **Penalty:** 50% of *unsecured* loot is lost (dropped in panic).
    *   **Reasoning:** Prevents "scumming" for specific drops and immediately retreating.

---

## 4. ⚙️ Auto-Resolution Engine

### 4.1 The "Step" Simulation
The adventure is broken down into **15-minute intervals**. Each interval is a distinct "Step" processed by the `AdventureResolutionEngine`.

**Step Logic:**
1.  **Vitals Check:** Is Player Dead? If yes, End.
2.  **Fatigue Check:** Apply fatigue penalty based on total duration active.
3.  **Event Roll:** Roll on the **Location Event Table** (modified by Stance/Supplies).
    *   **Combat (40-60%):** Encounter a monster.
    *   **Discovery (20-30%):** Find resources, chests, or lore.
    *   **Hazard (10-20%):** Trap, Weather Event, or Ambush.
    *   **Quiet (10%):** Flavor text, slight regeneration.
4.  **Resolution:** Resolve the rolled event (Combat/Skill Check).
5.  **Persistence:** Update temporary session state (HP, Loot, Log).

### 4.2 Auto-Combat
Combat uses the existing `CombatEngine` but is automated.
*   **AI:** The player character uses a simplified AI based on their **Stance**.
    *   *Aggressive:* Prioritizes high-damage skills.
    *   *Defensive:* Prioritizes mitigation and healing.
    *   *Cautious:* Flees if HP < 50%.
*   **Resolution:** Combat is simulated turn-by-turn (max 10 turns).
*   **Outcome:**
    *   **Win:** Gain XP/Loot. Continue.
    *   **Flee:** Survive but gain no loot. Continue.
    *   **Loss (Death):** Adventure Ends immediately.

### 4.3 Death & Failure
*   **Consequence:** Death is not perma-death, but it is costly.
*   **Loot Penalty:** Drop 50-75% of *gathered* loot (not equipped gear).
*   **Durability:** Significant durability loss on all equipped gear (10-20%).
*   **Recovery:** Character returns with 1 HP and must heal/rest.

---

## 5. 🔗 System Integration

### 5.1 Dungeon Floors (DepthsWarden)
*   **Depth Scaling:** Longer durations allow reaching deeper floors.
    *   *Scout:* Floors 1-3 only.
    *   *Odyssey:* Can reach Floor 20+.
*   **Risk:** Deeper floors have exponentially higher monster stats.

### 5.2 Inventory & Supplies
*   **Preparation Phase:** Crucial.
    *   **Rations:** Consumed every 4 steps (1 hour). Lack of rations = Fatigue (Stat penalty).
    *   **Torches:** Reduce Ambush chance in dark zones/night.
    *   **Potions:** Auto-consumed when HP < 30%.
    *   **Tools:** Pickaxes/Skinning Knives increase gathering yields.

### 5.3 Economy & Loot (GameBalancer)
*   **Scarcity:** Material drops are weighted. Common mats are plentiful in *Scout* missions. Rare mats require *Expedition* or *Odyssey* lengths.
*   **Aurum:** Earned from monster kills and "Bounties" (auto-completed quests).

### 5.4 Rank & Progression (ProgressionBalancer)
*   **Requirements:** Rank-ups now require "Successful Expeditions" of specific tiers (e.g., "Complete 3 Expeditions to the Molten Caldera").
*   **Kills:** Auto-kills count towards Rank kill quotas.

### 5.5 Factions
*   **Reputation:** Gained per successful step in Faction Territory.
*   **Missions:** "Faction Mandates" can be selected during prep to focus on specific enemies for bonus Rep.

---

## 6. 🖥️ UI/UX Design (One UI)

### 6.1 The Adventure Board (Embed)
*   **Trigger:** Button on Character Profile or `/adventure` (if allowed).
*   **Visuals:**
    *   **Dropdown:** Select Location (shows difficulty/level).
    *   **Buttons (Row 1):** Scout (30m), Patrol (2h), Expedition (8h), Odyssey (24h).
    *   **Buttons (Row 2):** Loadout Presets (Quick Equip).
    *   **Footer:** "Current Supplies: 5 Rations, 2 Torches."

### 6.2 Active Status
*   **Command:** `/status` (or checking Profile).
*   **Display:**
    *   "🟢 **Patrol in Whispering Woods**"
    *   "⏳ Time Remaining: 01:15:00"
    *   "🎒 Loot: 12 Items | 💰 450 Aurum"
    *   "❤️ HP: 85% | 🍗 Supplies: Good"
    *   **Button:** `Recall` (Warns about penalty).

### 6.3 The Report Card (Completion)
*   **Format:** Rich Embed sent to user.
*   **Sections:**
    *   **Header:** Success/Failure banner.
    *   **Log Summary:** "Encountered 4 Wolves, Discovered Ancient Shrine, Weathered a Storm."
    *   **Loot:** Grid display of items found.
    *   **XP/Rep:** Progress bars.
    *   **Damage:** "Armor took 15 durability damage."

---

## 7. ⚖️ Balance Considerations

*   **Active vs. Idle:** Idle is the *primary* progression. Active play (if kept) should be for specific, short-term goals (duels, arena, crafting).
*   **Economy Protection:**
    *   **Global Cap:** Limits on how many "Odysseys" can be run per week? (Maybe not needed if difficulty is high enough).
    *   **Fatigue:** Characters who run back-to-back Odysseys start with a debuff ("Exhausted"). Requires downtime or "Rest" action.
*   **Risk:** An *Odyssey* (24h) should have a >50% failure rate for unprepared players. It must be scary.

---

## 8. 🛠️ Technical Implementation

### 8.1 Database Schema (`adventure_sessions`)
```json
{
  "discord_id": 123456789,
  "start_time": "ISO-TIMESTAMP",
  "end_time": "ISO-TIMESTAMP",
  "duration_type": "patrol", // scout, patrol, expedition, odyssey
  "location_id": "whispering_woods",
  "status": "active", // active, completed, failed
  "log": ["Step 1: ...", "Step 2: ..."],
  "loot": {"wood": 10, "wolf_pelt": 2},
  "metrics": {
    "monsters_killed": 5,
    "damage_taken": 150
  },
  "config": {
    "stance": "defensive",
    "auto_potion": true
  }
}
```

### 8.2 Scheduler (`AdventureLoop`)
*   Runs every 1 minute.
*   Finds sessions where `end_time <= NOW` AND `status == 'active'`.
*   Calls `AdventureResolutionEngine.resolve_session()`.

### 8.3 Simulation Performance
*   **Batch Processing:** Simulate steps in chunks if the bot is lagging, but 15-min intervals are distinct.
*   **Optimistic Updates:** UI shows "Estimated Completion" but server is authority.

---

## 9. 🔮 Future Expansions

1.  **Party Expeditions:** Link multiple players to one session ID. Shared loot, combined power.
2.  **Mercenaries:** Hire NPCs to run Scout missions for you (passive income).
3.  **Dynamic World:** Global events (e.g., "Goblin Invasion") change risk/reward modifiers for specific zones for 24h.

---

## 🤝 Agent Coordination Notes

*   **@SystemSmith:** Implement the Scheduler and DB schema updates.
*   **@DataSteward:** Define loot tables for the new Duration Tiers.
*   **@GameForge:** Write flavor text for the "Quiet" and "Discovery" events.
*   **@DepthsWarden:** Map floors to duration tiers (e.g., Odyssey = Floor 20 access).
*   **@Tactician:** Refine the auto-combat logic for the Stance system.
*   **@Palette:** Design the "Report Card" embed visuals.
