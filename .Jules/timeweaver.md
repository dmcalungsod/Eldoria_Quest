# Timeweaver Journal

## Mission
Design a time-based auto-adventure system for Eldoria Quest.

## Initial Thoughts
The current system is manual, step-by-step. The new system needs to be "fire and forget" but with strategic depth.

### Key Decisions
1.  **Coexistence**: Auto-adventures will run alongside manual play. They serve different needs (active engagement vs. passive progression).
2.  **Time as Currency**: The primary cost is time. The secondary cost is supplies (HP/Food/Torches).
3.  **Simulation Fidelity**: We should reuse `CombatEngine` logic where possible but simplify the execution.
    -   *Decision*: Use a "Fast Simulation" approach. Calculate Average Damage Per Round (DPR) for both entities. Determine rounds to kill. Apply variance. This is faster than full turn-by-turn simulation with logs, but more accurate than a simple "Win %" check.
4.  **Risk/Reward**: Longer adventures reach "deeper floors" (higher difficulty modifiers) for exclusive rewards.
    -   *Mechanic*: Risk increases by +5% per hour. Loot quality increases by +5% per hour.

### Challenges
-   **Discord Limits**: We can't update a message every minute. We need a "check status" command or a final notification.
-   **State Management**: If the bot restarts, adventures must resume. The database schema needs `start_time`, `duration`, and `end_time`.
-   **Economy**: Auto-farming could inflate the economy.
    -   *Solution*: **Adventure Slots**. Starts at 1. Players can unlock a second slot at higher ranks (e.g., Rank B). Max 2 slots.
    -   *Stamina*: No stamina system, but "Fatigue" applies to the *character* if they go back-to-back? Maybe keep it simple: Just time.

### Integration Points
-   `LOCATIONS`: Already has `duration_options`. We can use these.
-   `CombatEngine`: Needs an `auto_resolve` method or a wrapper.
-   `Inventory`: Needs to support "Supplies" that are consumed automatically (Potions, Rations).
    -   *Idea*: Players can "pack" items. If HP < 30%, use Potion. If Hunger > 50%, use Ration.

## Detailed Design Notes

### Core Loop
1.  **Start**: Player uses `/adventure auto`.
2.  **Setup**: Select Location -> Duration (e.g., 30m, 1h, 4h, 8h).
3.  **Prep**: Select Loadout (Potions, Food). Shows "Win Probability" estimate based on stats vs location difficulty.
4.  **Go**: Bot confirms start. Database stores `end_time`.
5.  **Wait**: Player can check `/adventure status`.
6.  **End**: Bot sends DM or pings in channel. "Your adventure in the Whispering Thicket is complete!"

### Auto-Resolution Engine
-   **Step Interval**: 1 Step = 10 Minutes of Real Time.
-   **Step Logic**:
    -   Roll for Event (Combat, Gather, Flavor, Nothing).
    -   If Combat:
        -   Fetch Monster from Location pool.
        -   Simulate Fight (Fast Sim).
        -   If Win: Loot + XP. Consume HP/MP.
        -   If Lose: Adventure Ends. 50% Loot Lost. 10% Aurum Lost.
    -   If Gather:
        -   Roll Loot Table.
        -   Add to temporary "Bag".
-   **Completion**:
    -   Sum up all rewards.
    -   Apply to Player (DB Update).
    -   Generate Summary Report.

### Database Schema (`auto_adventures`)
-   `_id`: UUID
-   `discord_id`: Long (Index)
-   `start_time`: ISO Date
-   `end_time`: ISO Date
-   `location_id`: String
-   `duration_minutes`: Int
-   `status`: 'active', 'completed', 'failed'
-   `supplies`: JSON { "potion_hp_small": 5, ... }
-   `log`: Array of Strings (Summary)
-   `loot`: JSON { "item_key": count }

### UI/UX
-   **Setup Embed**: Shows Location Info, Recommended Level.
-   **Status Embed**: Progress Bar (Time Elapsed / Total). "Current Loot: 5x Herb, 2x Pelt". "Current HP: 80%".
-   **Result Embed**:
    -   Header: "Adventure Complete: [Location]"
    -   Body: "You survived 4 hours. Defeated 12 enemies. Gathered 25 items."
    -   Loot: List of items.
    -   XP/Aurum: Gained.

### Coordination
-   **SystemSmith**: Needs to build the `TaskScheduler` to check for `end_time <= now()`.
-   **Tactician**: Needs to write the `FastCombatSim` logic.
-   **GameBalancer**: Needs to tune the `EncounterRate` (how many monsters per hour?).

## Final Thoughts
This system respects the player's time while keeping the "Survival" aspect (you can die and lose loot). The "Supplies" mechanic adds strategy—bringing more potions allows longer/riskier runs.
