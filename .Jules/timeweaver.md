# Timeweaver Journal

## Initial Research
- Reviewed `AdventureManager`: Current system seems to support a mix of immediate processing and session-based tracking.
- Reviewed `CombatEngine`: Solid turn-based logic. The auto-adventure system needs to adapt this for "simulated" combat without necessarily running every single turn in full detail if performance is a concern, or just run it as is if the volume is manageable. given it's a discord bot, full simulation might be heavy if many players are adventuring. *Decision: We should probably simulate "encounters" rather than strictly "steps" to save processing, or use a simplified resolution for auto-adventures.*
- Reviewed `AdventureSession`: Needs to be checked to see if it supports the "log" of events that will be generated over time.

## Design Thoughts
- **Time vs Steps**: The prompt suggests "Clear mapping of time to steps: e.g., 1 step = 1 minute". This is a good baseline.
- **Interruption**: Players might want to check status.
- **Supplies**: Crucial for the "survival" aspect. Food/Torches should be consumed over time.
- **Risk**: Longer adventures = deeper floors = higher monster level.

## Next Steps
- Define the database schema changes needed.
- Define the "Resolution Engine" logic.
- Draft the UI flow.

## Database & Data Analysis
- **Monsters**: `monsters.json` contains detailed stats. We can reuse this.
- **Items**: `recipes.py` shows consumables. We need to ensure supplies like "rations" or "torches" are properly tagged for auto-adventure usage.
- **Adventure Session**: The `AdventureSession` class already supports `logs`, `loot`, and `steps_completed`. We need to expand this to handle "time elapsed" and "next processing time".

## Design Refinements
- **Core Loop**: User selects duration -> Bot calculates "end time" and "next step time" -> Database stores session -> Background task checks for "due" sessions -> Processes X steps based on time elapsed -> Updates DB -> Notifies user if complete.
- **Supplies**: Players should "equip" supplies for the journey.
- **Combat**: Auto-resolve using `CombatEngine` but perhaps in "fast mode" (just calc damage/results, skip detailed logs if not needed, or generate a summary log).

## Open Questions
- How to handle "death" in auto-adventure? Should they lose everything? Or just a portion? *Memory says: 10% Aurum, 50% Material, 100% XP loss.* We should stick to this or refine for auto-adventure specific (maybe less harsh since it's passive? Or harsher because it's riskier?). Let's stick to the memory standard for consistency but maybe add a "Rescue" mechanic later.
- **Discord Interaction**: We can't update a message every minute. We should update the "status" embed only on user request or at key milestones (25%, 50%, 75%, 100%).

## Drafting the Design Document Structure
1. **Title & Vision**: "Chronos Engine" - Time as the primary resource.
2. **Core Loop**:
   - `/adventure` command -> Select Location -> Select Duration -> Select Supplies -> Start.
   - Background Task: Checks DB every minute (or 5 mins).
   - "Recall": Allow early cancel with penalty (no loot from unfinished steps).
3. **Time Mechanics**:
   - Short (30m), Medium (2h), Long (8h), Epic (24h).
   - Multipliers for risk/reward based on duration? Or just linear scaling?
   - *Idea*: "Pushing it" mechanic. Going longer than comfortable adds fatigue.
4. **Resolution Engine**:
   - `ResolutionEngine` class.
   - Calculates "Events per hour".
   - Simulates combat using `CombatEngine` (headless mode).
   - Handles supply consumption (1 ration/hour, 1 torch/dungeon floor).
5. **UI/UX**:
   - Start: Dropdowns for location/time. Button for supplies.
   - Status: `/status` or Button on original message to "Refresh".
   - End: DM with summary image/embed.
6. **Integration**:
   - `InventoryManager` for deducting supplies.
   - `PlayerStats` for determining success chance of events.
   - `LevelUpSystem` for rewards.
