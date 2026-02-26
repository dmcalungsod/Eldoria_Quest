# Timeweaver Journal

## Initial Analysis
I have explored the codebase and found that an `AdventureResolutionEngine` already exists, which simulates steps for adventures that have passed their end time. The current system uses `AdventureSession` to simulate steps, which involves:
- Fetching player stats and context.
- Simulating combat or events (60/40 split).
- Handling auto-combat (up to 8 turns).
- Managing loot and vitals.

The current implementation seems to be a "catch-up" simulation at the end of the duration. This fits the "idle" requirement, but the prompt asks for a "comprehensive design" to "transform" the game. This suggests the current system might be a prototype or incomplete, or the user wants a more robust, feature-rich version.

## Key Observations
- **Existing Logic**: `AdventureSession.simulate_step` is the core. It handles combat and events. `AdventureResolutionEngine` loops this.
- **Manual vs Auto**: The `AdventureCommands` cog suggests manual commands are removed, so we are already moving towards auto.
- **Performance**: Simulating every step (combat turns etc.) for a 24h adventure (96 steps) for many players might be heavy if done all at once. I should consider if "statistical resolution" or "batched processing" is needed, but preserving "Class Identity" suggests we need the combat logic.
- **Risk/Reward**: Currently, fatigue increases damage after 16 steps. This is a good start. I need to expand on this with explicit duration tiers (Short, Medium, Long).

## Design Goals
1.  **Formalize the Idle Loop**: Make it clear how players start and claim adventures.
2.  **Duration Tiers**: Define specific durations (e.g., 30m, 4h, 12h) with distinct modifiers.
3.  **Risk Management**: Supplies should be crucial. "Retreat" conditions.
4.  **Notification**: Discord webhooks/messages when done.
5.  **Data Structure**: Ensure the DB schema supports the new features (status, start/end time, duration, log, rewards).

## Next Steps
- Draft the `timeweaver_design.md` covering all sections from the prompt.
- Focus on "Integration" with existing systems (Floors, Supplies).
- Detail the "Auto-Resolution" logic (keep it simulation-based for fidelity, but optimize).
