# ⏳ TIMEWEAVER: AUTO-ADVENTURE OVERHAUL DESIGN

## 🎯 MISSION OBJECTIVE
Transform Eldoria Quest into a time-based idle/auto-adventure RPG. Players dispatch characters on expeditions that take real time to complete, returning with loot, experience, and scars. This system replaces manual turn-based exploration with a strategic planning phase followed by automated resolution, preserving the game's dark fantasy tone and material-driven economy.

---

## 1. 🔄 CORE LOOP

The new gameplay loop focuses on **Preparation -> Dispatch -> Wait -> Results**.

1.  **Preparation (The Camp)**
    - Player selects a **Destination** (Dungeon/Wilderness).
    - Player chooses a **Duration** (Short, Standard, Long, Epic).
    - Player equips **Gear** and selects **Supplies** (Food, Potions, Tools).
    - *Strategic Choice:* Balancing risk (longer duration/harder location) vs. reward (better loot/xp) vs. cost (supplies/durability).

2.  **Dispatch (The Journey)**
    - Player confirms the expedition.
    - Character is locked into "Adventure" state.
    - Resources (Supplies) are consumed immediately.
    - A real-time timer begins.

3.  **The Wait (Idle Phase)**
    - Player can perform town activities (Crafting, Trading, Guild Management) but cannot adventure or change gear.
    - Commands: `/adventure status` shows current progress (e.g., "Exploring Floor 2...", "Fighting a Goblin...").
    - *Optional:* Players can "Recall" early for a penalty (no loot, partial XP).

4.  **Resolution (The Return)**
    - Timer expires.
    - Player receives a notification (DM or Ping).
    - Player uses `/adventure claim` (or clicks "Claim Results").
    - **Result Screen:** A detailed summary of the journey.
        - *Log:* Highlights of combat and discoveries.
        - *Loot:* Items found.
        - *Status:* HP/MP remaining, XP gained.
    - Character is unlocked.

---

## 2. ⏳ TIME MECHANICS

Time is the primary resource. Adventures are fixed-duration commitments.

### Duration Tiers
| Tier | Duration | Risk Modifier | Loot Quality | Usage Case |
| :--- | :--- | :--- | :--- | :--- |
| **Scout** | 30 Mins | Low (0.8x) | Standard | Quick material runs, testing builds. |
| **Patrol** | 2 Hours | Standard (1.0x) | Good (+10% Rarity) | Standard play session. |
| **Expedition** | 8 Hours | High (1.5x) | Excellent (+25% Rarity) | Overnight / Workday. High risk of death. |
| **Odyssey** | 24 Hours | Extreme (3.0x) | Legendary (+50% Rarity) | Weekend/Hardcore. Requires top-tier supplies. |

*Note: "Risk Modifier" affects Monster Stats (HP/ATK) and Event Difficulty.*

### Cancellation
- **Recall:** Can be done at any time.
- **Penalty:**
    - < 50% Duration: No Rewards, Supplies Lost.
    - > 50% Duration: 50% Loot/XP, Supplies Lost.
    - *Narrative:* "You fled in panic, dropping your pack."

---

## 3. ⚙️ AUTO-RESOLUTION ENGINE

The engine simulates the adventure in "steps" (ticks).

### Simulation Logic
- **Step Size:** 1 Step = 15 Minutes of real time.
- **Process:**
    1.  **Calculate Steps:** `Total Steps = Duration / 15 mins`.
    2.  **Iterate Steps:**
        - **Check Vitals:** If HP < 0, STOP (Death).
        - **Check Supplies:** Auto-eat/drink if needed (HP < 50%, Hunger).
        - **Event Roll:**
            - 60% Combat (Monster Encounter)
            - 30% Exploration (Gathering/Discovery)
            - 10% Empty/Flavor (Narrative)
    3.  **Combat Resolution:**
        - Uses `CombatHandler` (mostly existing logic).
        - **Auto-Battle:** Up to 10 rounds.
        - **AI:** Simple "Attack" or "Skill" based on MP/CD.
        - **Outcome:** Win (Loot/XP), Flee (if configured), or Die.
    4.  **Completion:** Store results in DB.

### Death Handling
- **Permadeath:** No (unless Hardcore mode added later).
- **Penalty:**
    - **Loot:** Lose 50% of gathered items (Materials).
    - **Aurum:** Lose 10% of carried gold.
    - **Durability:** 2x Equipment damage.
    - **Status:** Return with 1 HP (Requires healing).

---

## 4. 🔗 SYSTEM INTEGRATION

### Dungeon Floors (DepthsWarden)
- **Mapping:**
    - Scout: Floor 1-2
    - Patrol: Floor 1-5
    - Expedition: Floor 1-10
    - Odyssey: Floor 1-20 (Deepest)
- **Progression:** To unlock longer durations or deeper floors, players must complete specific "Boss Hunt" quests (Manual or Special Auto).

### Inventory (Supply System)
- **New Item Tag:** `[Supply]`
- **Loadout:** Players select a "Backpack" of supplies.
- **Capacity:** Limited by Bag Size (e.g., Small Pouch = 3 slots, Large Backpack = 10 slots).
- **Essentials:**
    - **Rations:** Prevent "Starvation" debuff (Stat penalty).
    - **Potions:** Auto-used at < 30% HP.
    - **Torches:** Reduce Ambush chance in Dungeons.
    - **Tools:** Pickaxe/Hatchet for gathering events.

### Economy
- **Loot Tables:** Adjusted for volume. Auto-adventures generate *more* items but take *longer*.
- **Aurum:** Earned from monster kills and "Bounty" events.
- **Sink:** Supplies cost Aurum/Materials, creating a loop.

### Ranks & Factions
- **Rank Up:** Requires "Successful Expeditions" count + Specific Item turn-ins.
- **Reputation:** Gained per hour spent adventuring in Faction territories.

### Achievements (ChronicleKeeper)
- **Time-Based Feats:** "Survivor" (Complete an Odyssey), "Marathon Runner" (1000 hours adventured).
- **Efficiency Feats:** "Speedrunner" (Clear a Scout mission in record time - if variability added).
- **Risk Feats:** "Minimalist" (Complete an Expedition with no supplies).

---

## 5. 🖥️ UI/UX DESIGN

### Start Adventure (Embed)
- **Title:** Expedition Planning
- **Fields:**
    - `Destination`: [Dropdown] (e.g., "Whispering Woods")
    - `Duration`: [Buttons] (30m, 2h, 8h, 24h)
    - `Supplies`: [Multi-Select Menu] (Select from Inventory)
- **Footer:** "Estimated Risk: Moderate | Recommended Level: 5"

### Status Command (`/adventure`)
- **Embed:** "Current Expedition: The Whispering Woods"
- **Visual:** Progress Bar `[====>------] 45%`
- **Fields:**
    - `Status`: "Battling a Wolf..."
    - `Loot So Far`: "3x Iron Ore, 1x Wolf Pelt"
    - `Vitals`: ❤️ 78% 💙 40%
- **Button:** `[Recall]` (Red)

### Result Screen (DM/Ping)
- **Title:** Expedition Complete!
- **Color:** Green (Success) / Red (Failure)
- **Description:** "You returned from the woods, weary but triumphant."
- **Fields:**
    - `Loot`: List of items (with rarities).
    - `XP`: "+450 XP (Level Up!)"
    - `Events`: "Defeated 12 Enemies, Found 3 Ore Veins."
- **Button:** `[Claim & Rest]`

---

## 6. ⚖️ BALANCE CONSIDERATIONS

- **Pacing:** Auto-adventure is slower than manual "grinding" but requires zero effort.
    - *Goal:* 8h Auto ≈ 1h Manual efficiency.
- **Supplies:** Essential. Going without food/torches should be viable only for "Scout" missions. Long missions require investment.
- **Risk Curve:**
    - Scout: 95% Survival Rate
    - Odyssey: 60% Survival Rate (without optimized gear).

---

## 7. 🛠️ TECHNICAL REQUIREMENTS

### Database Schema (`adventure_sessions`)
- `session_id`: UUID
- `user_id`: Discord ID
- `start_time`: Timestamp
- `end_time`: Timestamp
- `duration_type`: Enum (scout, patrol, etc.)
- `location_id`: String
- `status`: Enum (active, completed, failed, recalled)
- `log`: JSON (Array of event strings)
- `loot`: JSON (Map of item_id -> count)
- `vitals_snapshot`: JSON (HP, MP at start/current)
- `supplies`: JSON (Item_id -> remaining count)

### Scheduler (`AdventureLoop`)
- **Frequency:** Check every 1 minute.
- **Logic:**
    1. Query `adventure_sessions` where `end_time <= NOW` AND `status = 'active'`.
    2. For each:
        - Run `AdventureResolutionEngine.resolve(session)`.
        - Update DB `status = 'completed'`.
        - Send Discord Notification.

### Bot Restarts
- Adventures are stateless on the bot (stored in DB).
- On startup, bot simply resumes checking the DB. No data lost.

---

## 8. 🚀 FUTURE EXPANSIONS

- **Party System:** Send multiple characters (players) together for shared loot and reduced risk.
- **Mercenaries:** Hire NPC guards to increase success chance.
- **Caravans:** Trade missions (high risk, high gold, no XP).
- **Seasons:** "Winter" increases supply cost; "Blood Moon" increases combat difficulty.

---

## 🤝 AGENT COORDINATION

- **@SystemSmith**: Implement the `AdventureLoop` scheduler and DB schema updates.
- **@DataSteward**: Define the new `AdventureSession` document structure.
- **@GameForge**: Update `LOCATIONS` to include difficulty tiers and travel times.
- **@DepthsWarden**: Map dungeon floors to Adventure Duration tiers.
- **@Tactician**: update `CombatEngine` to support "simulation mode" (no visuals, just math).
- **@Palette**: Design the `Start` and `Result` embeds.
- **@StoryWeaver**: Write flavor text for "Empty" steps and "Recall" narratives.
