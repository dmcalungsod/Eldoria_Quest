# Progression Reward Gaps Analysis — 2026-03-07

**Data Date:** 2026-03-07
**Metric:** Expected Value (EV) per Hour (Aurum + Material Value)

## Key Findings

### 1. 🔴 Critical Reward Cliffs
Several zones exhibit a **significant drop in rewards (>10%)** compared to the previous, lower-level zone. This disincentivizes progression, as optimal play would involve farming easier content for better returns.

*   **The Shrouded Fen (Lvl 15):** **-27.9%** drop from *The Ashlands (Lvl 12)*.
*   **The Clockwork Halls (Lvl 22):** **-14.7%** drop from *The Crystal Caverns (Lvl 20)*.
*   **The Celestial Archipelago (Lvl 28):** **-19.6%** drop from *The Frostfall Expanse (Lvl 25)*.
*   **The Thunder-Crag Coast (Lvl 33):** **-30.9%** drop from *The Molten Caldera (Lvl 30)*.
*   **The Shimmering Wastes (Lvl 37):** **-26.9%** drop from *Gale-Scarred Heights (Lvl 35)*.

### 2. ⚠️ Rank/Level Inconsistency
There is a logic break in the Rank progression vs. Level Requirement sequence:
*   **The Frostfall Expanse** is **Rank A** but requires **Level 25**.
*   **The Celestial Archipelago** is **Rank B** but requires **Level 28**.
*   Typically, Rank A zones should require higher levels than Rank B zones. This explains the massive reward drop (-19.6%) when moving from Frostfall to Archipelago.

## Data Table

| Location                  | Rank | Lvl | EV/Hr    | Delta    | Status |
|---------------------------|------|-----|----------|----------|--------|
| Willowcreek Outskirts     | F    | 1   | 39.6     | -        |
| Whispering Thicket        | E    | 5   | 63.1     | +59.1%   | 🟢 Spike
| Deepgrove Roots           | D    | 10  | 130.5    | +107.0%  | 🟢 Spike
| The Ashlands              | D    | 12  | 214.1    | +64.1%   | 🟢 Spike
| **The Shrouded Fen**      | **C**| **15**| **154.3**| **-27.9%**| 🔴 CRITICAL
| The Sunken Grotto         | C    | 18  | 302.1    | +95.7%   | 🟢 Spike
| The Crystal Caverns       | B    | 20  | 415.0    | +37.4%   |
| **The Clockwork Halls**   | **B**| **22**| **353.9**| **-14.7%**| 🔴 CRITICAL
| The Forgotten Ossuary     | B    | 24  | 396.7    | +12.1%   |
| The Frostfall Expanse     | A    | 25  | 534.7    | +34.8%   |
| **The Celestial Archipelago**| **B**| **28**| **429.9**| **-19.6%**| 🔴 CRITICAL
| The Molten Caldera        | A    | 30  | 676.6    | +57.4%   | 🟢 Spike
| **The Thunder-Crag Coast**| **A**| **33**| **467.6**| **-30.9%**| 🔴 CRITICAL
| Gale-Scarred Heights      | A    | 35  | 768.7    | +64.4%   | 🟢 Spike
| **The Shimmering Wastes** | **A**| **37**| **562.2**| **-26.9%**| 🔴 CRITICAL
| The Void Sanctum          | S    | 40  | 915.8    | +62.9%   | 🟢 Spike

## Recommendations

1.  **GameBalancer:** Buff monster drop rates or material values for **The Shrouded Fen** and **The Clockwork Halls** to ensure they offer at least +5-10% EV over their predecessors.
2.  **GameBalancer:** The **Thunder-Crag Coast** and **Shimmering Wastes** appear significantly undertuned compared to the massive spikes of Caldera and Gale-Scarred Heights. Consider normalizing the spikes or buffing the valleys.
3.  **Architect / GameBalancer:** Resolve the Frostfall/Archipelago conflict.
    *   *Option A:* Swap their Level Requirements (Frostfall -> Lvl 28, Archipelago -> Lvl 25).
    *   *Option B:* Adjust Ranks (Frostfall -> Rank B, Archipelago -> Rank A).
