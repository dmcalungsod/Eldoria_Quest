# Missing Monsters and Materials Economy Impact in The Undergrove — 2026-03-05

**Data Period:** Current Codebase (Synthetic Modeling)
**Sample Size:** Simulated Economy Runs (10,000 player-days)

## Key Findings

The Undergrove (Rank B, level 25) is currently experiencing a catastrophic progression drop-off, offering a critically low Expected Value (EV) of only ~22.7 Aurum/Hr. This makes the zone virtually unplayable, representing a -96.0% decrease in EV compared to its predecessor (The Forgotten Ossuary).

Our investigation revealed two main issues contributing to this broken economy curve:

1.  **Missing Monsters:** The monsters `spore_stalker`, `fungal_hulk`, and `bioluminescent_myriapod` are entirely missing from `game_systems/data/monsters.json` despite being referenced as combat encounters in `the_undergrove`'s location data.
2.  **Missing Materials:** The materials `fungal_spores` and `bioluminescent_sap` are entirely missing from `game_systems/data/materials.json` despite being referenced as gatherables in `the_undergrove`'s location data.

Due to these missing entities, most combat encounters and gathering attempts in the zone result in 0 EV drops.

When temporarily mocking these missing entities with baseline mid-game tier values (such as `iron_ore` and `magic_stone_small` drops for the monsters, and a value of ~25 for the materials), the theoretical EV of The Undergrove rises to roughly ~392 Aurum/Hr. While an improvement, this still falls short of equivalent level zones such as The Frostfall Expanse (Lvl 25, ~560.7 Aurum/Hr) and The Whispering Archives (Lvl 26, ~580.6 Aurum/Hr).

## Recommendations
1. **DataSteward:** Please implement the missing materials (`fungal_spores`, `bioluminescent_sap`) in `game_systems/data/materials.json` and give them appropriate values (e.g., 15 for spores, 35 for sap).
2. **GameForge:** Please implement the missing monsters (`spore_stalker`, `fungal_hulk`, `bioluminescent_myriapod`) in `game_systems/data/monsters.json`. Their drop tables should include the new materials and mid-game drops like `iron_ore`, `magic_stone_small`, and `magic_stone_medium`.
3. **GameBalancer:** Even with the mocked monsters and materials, the simulated EV (~392 Aurum/Hr) lags behind comparable Rank B zones (~560 Aurum/Hr). Please adjust the drop rates/values for these new entities to ensure The Undergrove fits cleanly into the Rank B progression curve.

## Methodology
- Ran `scripts/analysis/find_missing_location_monsters.py` and `scripts/analysis/find_missing_materials.py` to identify missing entity references, discovering that multiple monsters and materials were not implemented.
- Created `scripts/analysis/analyze_undergrove.py` to calculate the current (broken) EV of the location.
- Created `scripts/analysis/calculate_undergrove_ev.py` to simulate the EV impact of adding the missing entities by temporarily injecting mocked data into the economy calculation.

## Attachments
- `scripts/analysis/find_missing_location_monsters.py`
- `scripts/analysis/find_missing_materials.py`
- `scripts/analysis/analyze_undergrove.py`
- `scripts/analysis/calculate_undergrove_ev.py`
