# Economy Balance Analysis — 2026-03-01

**Data Period:** Current Codebase (Synthetic Modeling)
**Sample Size:** Monte-Carlo Expected Value (EV) per Location

## Key Findings

- **The Shrouded Fen (Rank C, Level 15)** is significantly under-rewarding. With an Estimated EV/Trip (30m) of **192.13**, it is less rewarding than both Deepgrove Roots (Rank D, Level 10, EV 262.76) and The Ashlands (Rank D, Level 12, EV 325.70). This creates a progression dead zone where players are incentivized to farm lower-level content rather than progress to Rank C.
- **The Clockwork Halls (Rank B, Level 22)** has an EV of **533.34**, which is lower than the previous level's location, The Crystal Caverns (Level 20, EV 838.50). This needs a buff to incentivize end-game progression.
- **The Thunder-Crag Coast (Rank A, Level 33)** has an EV of **716.00**, which is drastically lower than the Level 30 location (The Molten Caldera, EV 1500.50). This breaks the expected risk-vs-reward scaling for Rank A.
- **The Celestial Archipelago (Rank B, Level 28)** has an EV of **624.25**, lower than earlier Rank B locations like The Frostfall Expanse (EV 1116.75) and The Whispering Archives (EV 1225.50).
- **The Shimmering Wastes (Rank A, Level 37)** has an EV of **1285.50**, which is lower than The Molten Caldera (Level 30, EV 1500.50). The progression here is inconsistent.
- **The Rank Logic Conflict:** The Frostfall Expanse (Rank B, Level 25) and The Celestial Archipelago (Rank B, Level 28) vs The Molten Caldera (Rank A, Level 30). This seems generally fine, although the rewards are not aligned with the levels.

## Recommendations

1. **GameBalancer:**
    - **Buff The Shrouded Fen:** Increase drop rates or add more valuable materials to bring its EV above ~350 Aurum per 30m.
    - **Buff The Clockwork Halls:** Increase the value or drop rate of `brass_gear`, `copper_wire`, etc., to bring EV above ~900 Aurum per 30m.
    - **Tune The Thunder-Crag Coast & The Shimmering Wastes:** The rewards for these Rank A zones must scale past The Molten Caldera's high EV (1500.50). Consider buffing their unique drops.
    - **Address Celestial Archipelago:** Raise its EV above ~1300 Aurum to match its level 28 requirement.
2. **Foreman:** Update project plan tasks to track these specific EV imbalances.

## Methodology

- Synthetic modeling based on Expected Value (EV) calculation.
- EV per kill = Sum of (Item Value * Drop Rate) for each monster in a location, weighted by monster appearance chance.
- EV per gather = Sum of (Item Value) weighted by gather appearance chance.
- Estimated EV per 30m trip = (Kill EV * 10) + (Gather EV * 3), based on average encounter rates.

## Attachments
- `scripts/analysis/2026_03_01_economy_balance.py` (Analysis Script)
