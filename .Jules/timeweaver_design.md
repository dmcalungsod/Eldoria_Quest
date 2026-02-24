# ⏳ TIMEWEAVER: Auto-Adventure System Design

**Version:** 1.0
**Status:** Draft
**Author:** Timeweaver (AI Agent)
**Date:** 2025-05-15

---

## 1. 🎯 Executive Summary
The **Auto-Adventure System** transforms Eldoria Quest by introducing a parallel progression path where players send their characters on time-based expeditions. Unlike manual play, which requires turn-by-turn input, auto-adventures run in the background, simulating exploration, combat, and resource gathering over real-world time.

This system is designed to:
-   **Respect Player Time**: Allow meaningful progression during busy periods.
-   **Enhance Strategy**: Shift focus from tactical combat to preparation (loadouts, risk assessment).
-   **Preserve Tension**: Maintain the risk of death and loss, ensuring "idle" doesn't mean "safe".

---

## 2. 🔄 Core Loop

### 2.1 The Flow
1.  **Preparation**: Player selects a destination, duration, and supplies (potions, food).
2.  **Departure**: Character is locked into the adventure state. They cannot manually explore or fight elsewhere.
3.  **Simulation**: The server calculates progress in real-time chunks (e.g., 10-minute "ticks").
    -   *Events*: Combat, Gathering, Random Encounters occur based on location data.
    -   *Resource Drain*: HP/MP fluctuates; supplies are consumed automatically if critical.
4.  **Completion**:
    -   **Success**: Timer ends. Player receives a notification and a summary of loot/XP.
    -   **Failure**: Character hits 0 HP. Adventure ends early. Partial loot is lost.
    -   **Recall**: Player manually cancels. Returns immediately with whatever was gathered so far (no penalty, just time spent).

### 2.2 Constraints
-   **One Active Adventure**: Players can only have one character adventuring at a time (Auto OR Manual).
    -   *Note*: Future expansion could allow "Retainers" or "Mercenaries" for parallel slots.
-   **Cooldowns**: None by default, but "Fatigue" mechanics (see Balance) may apply to limit 24/7 farming.

---

## 3. ⏳ Time Mechanics

### 3.1 Durations
Players choose from fixed duration tiers. Longer trips offer better efficiency but higher risk.

| Tier | Duration | Risk Modifier | Loot Quality | Recommended For |
| :--- | :--- | :--- | :--- | :--- |
| **Scout** | 30 Mins | 1.0x (Base) | Standard | Quick material runs |
| **Patrol** | 2 Hours | 1.1x (+10%) | +5% Rare | Daily tasks |
| **Expedition**| 8 Hours | 1.25x (+25%)| +15% Rare | Overnight farming |
| **Odyssey** | 24 Hours | 1.5x (+50%) | +30% Rare, Boss Chance | Weekend progression |

### 3.2 Real-Time Processing
-   **Server-Side**: The system does *not* need a running loop for every player.
-   **Calculation**:
    -   *On Check/Complete*: The system calculates `(Current Time - Start Time) / Tick Rate` to determine how many "steps" have occurred.
    -   *State Update*: It updates the database with the new state (HP, Loot) and the `last_processed_time`.

---

## 4. ⚙️ Auto-Resolution Engine

### 4.1 The "Tick" System
-   **Tick Rate**: 10 Minutes of Real Time = 1 Adventure Step.
-   **Step Logic**:
    1.  **Regen Check**: Apply natural HP/MP regen (modified by environment).
    2.  **Event Roll**:
        -   60% **Combat** (Encounter a monster from the location pool).
        -   30% **Gathering** (Find materials).
        -   10% **Flavor/Empty** (Narrative event, safe spot).

### 4.2 Combat Simulation (Fast-Sim)
To avoid heavy processing, combat is resolved via a deterministic simulation rather than turn-by-turn AI.

**Formula:**
1.  **Player Power** = `Attack * (1 + Crit%) + Defense + Speed`
2.  **Monster Power** = `ATK + DEF + Level * 5`
3.  **Win Probability** = `Player Power / (Player Power + Monster Power)`
    -   *Modifiers*: Elemental advantage, Skills (abstracted as +10% Power).
4.  **Outcome**:
    -   **Win**: Player takes `Damage = (Monster ATK * Rounds) - (Player DEF * Rounds)`.
        -   *Rounds* = `Monster HP / Player DPS`.
    -   **Loss**: Player takes lethal damage. Adventure Fails.

### 4.3 Supply Usage
Players define a "Threshold" for using items (e.g., "Use Potion if HP < 30%").
-   The simulation checks HP *after* every combat.
-   If `HP < Threshold` AND `Potion in Supplies`, consume 1 Potion and restore HP.

### 4.4 Death & Failure
-   **Condition**: HP <= 0.
-   **Penalty**:
    -   **Loot**: Lose 50% of gathered materials (randomly selected).
    -   **Aurum**: Lose 10% of carried Aurum (standard death tax).
    -   **XP**: Retain 100% of earned XP (time invested is never fully wasted).
-   **State**: Adventure status updates to `Failed`. Player must "Rescue" (command) to retrieve character.

---

## 5. 🔗 Integration with Existing Systems

### 5.1 Database Schema (`auto_adventures`)
A new MongoDB collection to track active sessions.

```json
{
  "discord_id": 123456789,
  "start_time": "ISO-8601",
  "end_time": "ISO-8601",
  "last_processed": "ISO-8601",
  "location_id": "forest_outskirts",
  "duration_minutes": 120,
  "status": "active",
  "config": {
    "risk_level": 1,
    "use_potion_threshold": 30
  },
  "state": {
    "current_hp": 150,
    "current_mp": 50,
    "loot": {"herb": 5, "pelt": 2},
    "log": ["Started journey...", "Fought Wolf...", "Found Herbs..."]
  }
}
```

### 5.2 Inventory & Economy
-   **Loot Tables**: Use the existing `AdventureRewards` tables but scaled by duration.
-   **Inventory Space**: Auto-adventures respect inventory limits. If full, new items are discarded (highest value kept).
-   **Durability**: Gear durability decreases by 1 per combat encounter.

### 5.3 Ranks & Quests
-   **Rank Progression**: Kills in auto-adventures count towards Rank Requirements at a 50% rate (to encourage manual play for promotion).
-   **Quests**: "Fetch" quests work normally. "Kill" quests work at 50% rate.

### 5.4 Factions & Achievements
-   **Factions**: Completing auto-adventures grants Reputation with the relevant local faction (e.g., *The Verdant Guard* for forest zones).
    -   *Rate*: 1 Rep per 30 minutes of successful adventuring.
-   **Achievements**: Time spent in auto-adventures counts towards specific "Explorer" achievements.
    -   *Examples*: "Marathon Runner" (100 hours total), "Survivor" (24h trip without damage).
    -   *Note*: Combat achievements (e.g., "Slayer") count at 50% rate.

---

## 6. 🎨 UI/UX Design

### 6.1 Setup Command (`/adventure auto`)
A streamlined menu using Discord Select Menus:
1.  **Location**: Dropdown of unlocked zones.
2.  **Duration**: Buttons [30m] [2h] [8h] [24h].
3.  **Supplies**: Multi-select menu (Potion x5, Ration x2).
4.  **Confirm**: Shows "Estimated Survival Chance: 85%".

### 6.2 Status Dashboard (`/adventure status`)
Displays an embed that updates on command or refresh (via button):
-   **Progress Bar**: `[▓▓▓▓▓░░░░░] 50%`
-   **Vitals**: HP: 120/200 | MP: 40/100
-   **Loot Sack**: 🌿 x12, 🦴 x4, 💰 150
-   **Latest Log**: "10:45 - Defeated Moss Golem (-15 HP)"

### 6.3 Completion Notification
When time is up, the bot DMs the user (or pings in a specific channel):
> **🌟 Adventure Complete!**
> You returned from **Whispering Thicket**.
> **Time**: 2h 00m
> **Loot**:
> - 🌿 Medicinal Herb x8
> - 🐺 Wolf Pelt x3
> - 💎 Magic Stone x1
>
> *Use `/adventure claim` to secure your rewards.*

---

## 7. ⚖️ Balance & Anti-Abuse

### 7.1 The "Lazy" Tax
Auto-adventures are roughly **70% as efficient** as optimal manual play per minute.
-   *Reason*: Manual players can use skills perfectly, kite enemies, and optimize routing. Auto is a "brute force" simulation.

### 7.2 Safety Valves
-   **Daily Limit**: Max 24 hours of auto-adventure time per rolling 24h window (prevents multi-account bot farms from infinite scaling).
-   **Bot Restarts**: The system calculates progress based on timestamps (`now - last_processed`), so downtime doesn't break adventures. They just "catch up" instantly when the bot comes back online.

---

## 8. 🛠️ Implementation Plan (Agent Coordination)

### Phase 1: Foundation (SystemSmith & DataSteward)
-   Create `auto_adventures` collection.
-   Implement `AutoAdventureManager` class.
-   Set up the "Tick" processor (background task).

### Phase 2: Simulation Logic (Tactician & GameBalancer)
-   Develop the `FastCombatSim` algorithm.
-   Calibrate "Win %" against real player stats.
-   Tune loot drop rates for auto-mode.

### Phase 3: UI & Interface (Palette)
-   Build `AutoSetupView` and `AutoStatusView`.
-   Create the "Claim Rewards" interface.

### Phase 4: Integration (DepthsWarden & ProgressionBalancer)
-   Link Location data to Auto-mode.
-   Apply Rank XP penalties/bonuses.

### Phase 5: Content & Polish
-   **GameForge**: Define "Auto-Only" events or rare drops for long durations.
-   **StoryWeaver**: Write narrative templates for adventure logs (e.g., "Found a hidden glen...", "Ambushed by goblins...").
-   **Grimwarden**: Verify death penalties feel fair but punishing. Ensure "Rescue" mechanics work.
-   **ChronicleKeeper**: Implement tracking for time-based achievements.
-   **BugHunter**: Stress test with 1000 concurrent "virtual" adventures to check database load.
-   **Visionary**: Review final player feedback loop and adjust "Lazy Tax" if needed.

---

## 9. 🔮 Future Expansions
-   **Party Mode**: Send multiple characters together for boosted safety.
-   **Mercenaries**: Hire NPCs to guard you during auto-adventures.
-   **Offline Defense**: Auto-adventures could be intercepted by "Raiding" monsters (World Events).

---

## 🔚 Final Design Note
This system shifts Eldoria from a "play only when active" game to a "living world" where your character grows while you sleep. The key is **Preparation**: the game becomes about *planning* the expedition rather than just *clicking* through it.
