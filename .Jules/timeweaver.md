# Timeweaver Journal

## Mission
Design a comprehensive Time-Based Auto-Adventure System for Eldoria Quest.
Goal: Transform manual exploration into a deep, strategic idle experience.

## Current State Analysis
- **Codebase:** `game_systems/adventure/` contains the core logic.
- **Manager:** `AdventureManager` handles start/end.
- **Session:** `AdventureSession` handles step simulation (`simulate_step`) and auto-combat (`_resolve_auto_combat`).
- **Resolution:** `AdventureResolutionEngine` processes due adventures in a loop (15-min steps).
- **Loop:** `AdventureLoop` checks for completions every minute.

**Gap Analysis:**
- The current system exists technically but seems to lack the "Game Design" layer of user choice, meaningful risk/reward scaling, and rich feedback.
- "Manual turn-based" is mentioned as the thing to replace, yet the code shows a hybrid. The goal is to make "Auto" the *primary* interaction.
- UI needs a full spec (Buttons, Dropdowns).
- Strategic choices (Supplies, Stance) need to be impactful.

## Key Design Pillars
1.  **Time as Resource:** Real-time waiting is the cost.
2.  **Preparation is Gameplay:** Since the player can't intervene during the adventure, *preparation* (loadout, location, duration) becomes the skill check.
3.  **Narrative Delivery:** The "Report Card" at the end must be satisfying to read.

## Brainstorming: Mechanics

### Duration Tiers
Instead of a slider, offer distinct tiers with clear identities:
- **Scout (30m):** "Quick look." Low risk. Materials.
- **Patrol (2h):** "Standard." XP, Monsters.
- **Expedition (8h):** "High commitment." Bosses, Rare Loot.
- **Odyssey (24h):** "Extreme." Legendary Artifacts. High death chance.

### The "Step"
- Keep the 15-minute step interval. It's granular enough for events but efficient for the server.
- Each step is a roll:
    - **Combat:** (Based on Danger Level).
    - **Event:** (Merchant, Trap, Discovery).
    - **Gathering:** (Materials).
    - **Empty:** (Flavor text).

### Combat Resolution
- Existing `combat_engine` is robust.
- Auto-combat currently simulates turns. This is good! It respects player build diversity (crit, dodge, tank).
- **Optimization:** If simulation is too heavy for thousands of players, we might need a simplified "Power vs Power" check, but the memory says "1,100 sessions/sec" throughput, so full sim is likely fine.
- **Death:** Currently stops adventure.
    - *Idea:* "Emergency Retreat." If HP < 0, adventure ends, but you keep what you found *up to that point* minus a penalty? Or maybe you lose everything?
    - *Decision:* Harsh survival tone. Death = Drop loot. But maybe "Insurance" or specific supplies can mitigate this.

### Supplies (Logistics)
- Food (Fatigue reduction).
- Torches (Ambush prevention).
- Potions (Auto-use on low HP).
- *New:* "Recall Scroll" (allows early exit without penalty? Or automatic escape on death?).

## Integration
- **Guilds:** Contributing to guild stash via adventures?
- **Factions:** Reputation gains scaled by duration.

## UI/UX
- **Dashboard:** A persistent message in the user's DM or a private channel?
- "ONE UI" -> Edit the interaction response.
- Start Adventure -> Select Location (Dropdown) -> Select Duration (Buttons) -> Confirm.
- Active State -> Show "Time Remaining" and a "Recall" button.
- Completion -> DM notification? Or just next time they check. "Your adventure has ended."

## Plan
I will structure the design document to cover these points in detail.

## Design Completion Log (2024-10-24)

### Decisions Made
1.  **Tiered Durations:** Adopted the 4-tier system (Scout, Patrol, Expedition, Odyssey) to give clear risk/reward brackets.
2.  **Stance System:** Added "Stance" selection (Aggressive, Defensive, Cautious) to give players agency over the auto-combat AI. This solves the "mindless" problem.
3.  **One UI Policy:** The design mandates editing the interaction response for status updates rather than spamming messages.
4.  **Death Penalty:** Settled on a "Survival" approach where death means losing 50-75% of *gathered* loot, but not equipped gear. This maintains the stakes without being overly punishing (perma-death).
5.  **Integration:** Explicitly linked duration to "Dungeon Floors" (DepthsWarden) to ensure deep progression is gated by time investment and risk.

### Agent Coordination
- Identified **Tactician** as critical for implementing the Stance AI logic.
- **SystemSmith** needs to update the schema for `duration_type` and `config` (stance).
- **Palette** is needed for the "Report Card" visual design.

### Reflections
- The existing codebase is surprisingly robust (`AdventureSession` already has step logic). The main work is in the *wrapper* (UI, selection) and the *tuning* (Duration tiers, Stance logic).
- The transition from "Manual" to "Auto" is essentially about shifting the decision point from *during* the adventure to *before* the adventure.
