# 📊 Economy Balance Analysis — 2026-02-27

**Data Period:** Current Codebase (February 2026)
**Methodology:** 1000-Hour Monte Carlo Simulation & Expected Value Calculation
**Focus:** Auto-Adventure Economy (Aurum/Material Yield per Hour)

## 🚨 Executive Summary

The economy simulation reveals a **critical imbalance** in the early-game progression. The **Deepgrove Roots (Rank D, Level 10)** zone currently yields **689.1 Total Value/Hour**, which is higher than nearly all mid-game zones and comparable to late-game zones like **The Molten Caldera (Rank A, Level 30)**. This creates a massive exploit where low-level players can farm end-game currency and materials efficiently.

Additionally, **The Shrouded Fen (Rank C)** and **Clockwork Halls (Rank B)** are significantly under-tuned, offering poor rewards for their difficulty level.

## 🔍 Key Findings

### 1. The Deepgrove Roots Anomaly (Critical)

* **Yield:** 689.1/hr (vs Expected ~150-200/hr for Rank D).
* **Cause:** The **Feral Stag (Boss, Level 11)** has a high spawn weight (15/85 ≈ 17.6%) and drops **Epic Tier Materials** (`magic_stone_flawless`, `celestial_dust`).
* **Impact:** Players will farm this zone indefinitely, bypassing mid-game content and inflating the economy with high-value materials.

### 2. The Shrouded Fen Bottleneck

* **Yield:** 152.6/hr.
* **Issue:** Despite being Rank C (Level 15+), the zone drops predominantly **Common** materials (`medicinal_herb`, `magic_stone_small`) with low sell values (5-15 Aurum).
* **Impact:** Players are incentivized to skip this zone or return to lower-level areas for better profit.

### 3. High-Tier Compression

* **Gale-Scarred Heights (Rank A, Lvl 35)** yields **768.7/hr**.
* **The Void Sanctum (Rank S, Lvl 40)** yields **774.8/hr**.
* **Issue:** The reward gap between Rank A and Rank S is negligible (<1%), reducing the incentive to push for the hardest content.

### 4. Clockwork Halls Underperformance

* **Yield:** 310.6/hr (vs Crystal Caverns ~415/hr).
* **Issue:** Low drop weights for valuable materials compared to its peer zones.

## 📊 Data Table: Simulated Yields

| Location | Rank | Lvl | Aurum/Hr | Mat Val/Hr | Total/Hr |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Willowcreek Outskirts** | F | 1 | 13.2 | 26.5 | 39.6 |
| **Whispering Thicket** | E | 5 | 26.6 | 36.5 | 63.1 |
| **Deepgrove Roots** | **D** | **10** | **244.5** | **444.6** | **689.1 ⚠️** |
| **The Ashlands** | D | 12 | 136.1 | 78.0 | 214.1 |
| **The Shrouded Fen** | **C** | **15** | **108.9** | **43.6** | **152.6 📉** |
| **The Sunken Grotto** | C | 18 | 193.2 | 108.9 | 302.1 |
| **The Crystal Caverns** | B | 20 | 215.0 | 200.0 | 415.0 |
| **The Clockwork Halls** | B | 22 | 227.0 | 83.6 | 310.6 |
| **The Forgotten Ossuary** | B | 24 | 236.4 | 160.2 | 396.7 |
| **The Frostfall Expanse** | A | 25 | 265.9 | 268.8 | 534.7 |
| **The Celestial Archipelago** | B | 28 | 281.9 | 148.0 | 429.9 |
| **The Molten Caldera** | A | 30 | 316.8 | 359.8 | 676.6 |
| **Gale-Scarred Heights** | A | 35 | 518.8 | 249.9 | 768.7 |
| **The Shimmering Wastes** | A | 37 | 266.6 | 295.6 | 562.2 |
| **The Void Sanctum** | **S** | **40** | **416.8** | **358.0** | **774.8** |

## 🎯 Recommendations

### Immediate Actions (Hotfix)

1. **Nerf Deepgrove Roots:**
    * **Action:** Move `Feral Stag` (ID 17) to `conditional_monsters` with a low weight (e.g., 5) and strict level requirement (e.g., Level 15+).
    * **Alternative:** Remove `magic_stone_flawless` and `celestial_dust` from its drop table. These are Rank S materials.

### Balance Adjustments

2. **Buff Shrouded Fen:**
    * **Action:** Upgrade drops to `magic_stone_medium` (Value 50) and `ancient_wood` (Value 25). Increase quantities for gatherables.

2. **Buff Void Sanctum:**
    * **Action:** Increase drop rate of `void_heart` (Epic, 1500) or add `magic_stone_flawless` to more monsters to justify the difficulty.

3. **Tune Clockwork Halls:**
    * **Action:** Increase drop weight of `steam_core` (Rare, 150) or `clockwork_heart` (Epic, 850) slightly.

## 🤝 Coordination

* @GameBalancer: Please review the proposed drop table changes.
* @GameForge: Ensure `Feral Stag` is correctly categorized as a Boss for Rank D.
