# Economy Progression and Schema Integrity Analysis — 2026-03-13

**Data Period:** Current Codebase (Synthetic Modeling)
**Sample Size:** Simulated Economy Runs

## Key Findings

### Progression Reward Cliffs
An analysis of Expected Value (EV) per Hour across adventure locations, sorted by Level Requirement, has revealed several significant "Reward Cliffs" where difficulty increases but rewards plummet.

The two most critical drops identified are:
1. **The Undergrove (Rank B, Lvl 25):** Drops to 22.7 EV/Hr, which is a **-96.0% decrease** compared to the preceding location (The Frostfall Expanse).
2. **The Sunken Grotto (Rank C, Lvl 18):** Drops to 731.2 EV/Hr, a **-5.7% decrease** compared to The Shrouded Fen. (This has improved massively since yesterday's -59.7% drop due to GameBalancer's updates, but could still use a slight nudge to feel rewarding for the increased difficulty).
3. **The Crystal Caverns (Rank B, Lvl 20):** Drops to 434.4 EV/Hr, a **-40.6% decrease** compared to The Sunken Grotto.
4. **The Forgotten Ossuary (Rank B, Lvl 24):** Drops to 412.4 EV/Hr, a **-79.6% decrease** compared to The Clockwork Halls.
5. **The Molten Caldera (Rank A, Lvl 30):** Drops to 500.3 EV/Hr, an **-80.4% decrease** compared to The Celestial Archipelago.
6. **Gale-Scarred Heights (Rank A, Lvl 35):** Drops to 793.2 EV/Hr, a **-59.9% decrease** compared to The Thunder-Crag Coast.

### The Undergrove - Missing Entities Investigation
The massive EV drop in **The Undergrove** remains due to missing entities in the game data. Our scripts (`find_missing_location_monsters.py` and `find_missing_materials.py`) have confirmed that:
- **Missing Monsters:** `fungal_hulk`, `spore_stalker`, `bioluminescent_myriapod` are absent from `monsters.json`.
- **Missing Materials:** `fungal_spores` and `bioluminescent_sap` are absent from `materials.py`.
Since these entities are missing, The Undergrove's economy calculations fail to attribute their value, leading to an almost zero expected payout.

### Schema Integrity & Missing Skills
Our data integrity checks have flagged the following errors that impact gameplay and combat calculations:
- **Location Schema Error:** `adventure_locations.json` is missing the required `description` field for `howling_peaks`.
- **Monster Skill Errors:** Two end-game monsters reference skills that do not exist in `skills_data.py`:
  - `frost_gargoyle` (The Howling Peaks) references `ice_spear`.
  - `storm_drake` (The Howling Peaks) references `dragon_breath`.
  - `storm_drake` references `whirlwind`, which exists in `skills.json` and `combat_phrases.py` but is being flagged as missing.

## Recommendations

1. **@GameBalancer (Economy Fixes):**
   - Review and buff EV drops for the locations identified as critical drops (The Crystal Caverns, The Forgotten Ossuary, The Molten Caldera, Gale-Scarred Heights).

2. **@Foreman (Task Tracking):**
   - The tasks for fixing The Undergrove and the Schema integrity issues are already listed in the plan (Tasks E.1, E.2, E.4, E.5). Ensure they remain a priority.
   - The Sunken Grotto buff (Task E.3) has been partially successful, but could use a slight final adjustment.
   - Add new tasks for GameBalancer to buff the newly identified progression gaps.

## Methodology
- Ran `scripts/analysis/check_progression_gaps.py` to identify EV discrepancies.
- Ran `scripts/analysis/find_missing_location_monsters.py` and `scripts/analysis/find_missing_materials.py` to diagnose the root cause of The Undergrove's low EV.
- Validated entity references across the JSON schemas and Python data files to uncover missing location attributes and monster skills.

## Attachments
- `scripts/analysis/check_progression_gaps.py`
- `scripts/analysis/find_missing_location_monsters.py`
- `scripts/analysis/find_missing_materials.py`
