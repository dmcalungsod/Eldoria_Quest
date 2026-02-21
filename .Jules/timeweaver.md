# ⏳ TimeWeaver Journal

## Mission
To reimagine Eldoria Quest as a time-based auto-adventure game while preserving its dark fantasy survival roots.

## Initial Research & Codebase Exploration

### Current System (`AdventureManager`, `AdventureSession`)
- Currently uses a "simulate step" approach where the user manually triggers steps or auto-resolves combat in small chunks.
- Data is stored in `adventure_sessions` collection in MongoDB.
- Existing fields: `start_time`, `end_time`, `duration_minutes`, `active`, `logs`, `loot_collected`.
- This structure is actually very close to what is needed for time-based adventures. The `duration_minutes` field is already there.

### Locations (`adventure_locations.py`)
- Locations already define `duration_options` (e.g., [30, 60, 120] minutes).
- Monster tables and gatherables are well-structured for RNG generation.

### Database (`DatabaseManager`)
- Robust singleton pattern.
- `adventure_sessions` collection can be reused.
- Need to ensure `get_active_adventure` is efficient for the background task if we have many players.

## Design Decisions

### 1. The Core Loop
- **Start:** User selects location -> Selects Duration (Short/Medium/Long) -> Embarks.
- **Wait:** The bot calculates the end time.
- **End:** A background task checks for `end_time <= now`. It triggers a "Completion" process.
- **Resolution:**
    - I will implement a "Resolution Engine" that simulates the adventure in one go upon completion.
    - It will calculate:
        - Total Encounters = Duration / X minutes.
        - Total Loot = Encounters * Loot Chance.
        - Total Damage Taken = Encounters * Monster Damage (mitigated by DEF/Skills).
        - XP/Aurum.
    - **Survival Aspect:** If `Total Damage > Player HP`, the adventure "Failures" or "Retreats". The player returns with reduced loot (e.g., 50%) and 1 HP.

### 2. Time vs. Steps
- Instead of simulating every second, I'll abstract it to "1 Step per 15 Minutes".
- 30m Adventure = 2 Steps.
- 8h Adventure = 32 Steps.
- Each step has a chance for: Combat, Gathering, Event, or Empty.

### 3. Risk/Reward
- **Short Adventures:** Safer, good for quick materials.
- **Long Adventures:** Higher chance of "Deep" exploration (better loot tables), but fatigue mechanics or escalating damage could apply.

### 4. Integration
- **Economy:** Auto-adventures will flood the economy with materials. I need to ensure sinks (crafting, guild projects) are robust. *Note for GameBalancer.*
- **Guilds:** Reputation is already hooked in `end_adventure`.

## Next Steps
- Draft the full design document in `.Jules/timeweaver_design.md`.
