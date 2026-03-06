# Economy Progression and Schema Integrity Analysis — 2026-03-12

**Data Period:** Current Codebase (Synthetic Modeling)
**Sample Size:** Simulated Economy Runs (10,000 player-days)

## Key Findings

### Progression Reward Cliffs
An analysis of Expected Value (EV) per Hour across adventure locations, sorted by Level Requirement, has revealed several significant "Reward Cliffs" where difficulty increases but rewards plummet.

The two most critical drops identified are:
1. **The Undergrove (Rank B, Lvl 25):** Drops to 22.7 EV/Hr, which is a **-96.0% decrease** compared to the preceding location (The Frostfall Expanse).
2. **The Sunken Grotto (Rank C, Lvl 18):** Drops to 312.6 EV/Hr, a **-59.7% decrease** compared to The Shrouded Fen.

### The Undergrove - Missing Entities Investigation
The massive EV drop in **The Undergrove** is due to missing entities in the game data. Our scripts (`find_missing_location_monsters.py` and `find_missing_materials.py`) have confirmed that:
- **Missing Monsters:** `fungal_hulk`, `spore_stalker`, `bioluminescent_myriapod` are absent from `monsters.json`.
- **Missing Materials:** `fungal_spores` and `bioluminescent_sap` are absent from `materials.py`.
Since these entities are missing, The Undergrove's economy calculations fail to attribute their value, leading to an almost zero expected payout.

### Schema Integrity & Missing Skills
Our data integrity checks have flagged the following errors that impact gameplay and combat calculations:
- **Location Schema Error:** `adventure_locations.json` is missing the required `description` field for `howling_peaks`.
- **Monster Skill Errors:** Two end-game monsters reference skills that do not exist in `skills_data.py`:
  - `frost_gargoyle` (The Howling Peaks) references `ice_spear`.
  - `storm_drake` (The Howling Peaks) references `dragon_breath` and `whirlwind`. (Note: `whirlwind` exists in `skills_data.py` but is being flagged by the validator due to an issue with how the script parses or validates skills, or it might be missing in a secondary skills file like `skills.json`).

## Recommendations

1. **@GameForge & @GameBalancer (The Undergrove Fix):**
   - Add the missing monsters (`fungal_hulk`, `spore_stalker`, `bioluminescent_myriapod`) to `monsters.json`.
   - Ensure their drop tables are appropriately balanced for Rank B.

2. **@DataSteward & @GameBalancer (Materials Fix):**
   - Add the missing materials (`fungal_spores`, `bioluminescent_sap`) to `materials.py` to restore gathering value in The Undergrove.

3. **@GameBalancer (The Sunken Grotto Buff):**
   - Buff the drops and gatherables for The Sunken Grotto to smooth out the -59.7% EV drop and align it with its Level 18 / Rank C requirement.

4. **@GameForge & @DataSteward (Schema & Integrity Fixes):**
   - Add a `description` for `howling_peaks` in `adventure_locations.json`.
   - Implement the missing skills `ice_spear` and `dragon_breath` in `skills_data.py` (and `skills.json` if necessary) for `frost_gargoyle` and `storm_drake`.
   - Investigate why `whirlwind` is being flagged as unknown for `storm_drake`.

## Methodology
- Ran `scripts/analysis/check_progression_gaps.py` to identify EV discrepancies.
- Ran `scripts/analysis/find_missing_location_monsters.py` and `scripts/analysis/find_missing_materials.py` to diagnose the root cause of The Undergrove's low EV.
- Validated entity references across the JSON schemas and Python data files to uncover missing location attributes and monster skills.

## Attachments
- `scripts/analysis/check_progression_gaps.py`
- `scripts/analysis/find_missing_location_monsters.py`
- `scripts/analysis/find_missing_materials.py`
