# 📓 Analyst Journal

This journal documents key insights, successful methodologies, and lessons learned from data analysis tasks.

---

## 2026-03-01: Economy Simulation
**Focus:** Simulating the impact of the new "Scavenger" mechanic on daily Aurum influx.

**Methodology:**
- Created `scripts/analysis/analyze_economy.py` to simulate 10,000 player-days.
- Compared `old_system` (Combat Only) vs `new_system` (Combat + Scavenge).

**Key Findings:**
- The new mechanic increases average daily Aurum by 12%.
- Low-level players benefit most (+25% Aurum), reducing early-game churn.

**Outcome:**
- Validated the Scavenge mechanic. Recommended proceeding with deployment.

---

## 2026-03-07: Progression Reward Gaps Analysis
**Focus:** Analyzing the "Reward per Hour" curve across all adventure zones to ensure smooth progression.

**Methodology:**
- Created `scripts/analysis/check_progression_gaps.py` to calculate EV/Hour (Aurum + Material Value) for each zone.
- EV Calculation accounts for:
    - 40% Gathering Chance (Material Value) + 60% Combat Chance (Aurum + Material Drops).
    - Tier Multipliers (Normal x1.5, Elite x5.0, Boss x20.0).
    - Luck Bonus (Simulated at 10 Luck).
- Sorted results by Level Requirement to visualize the progression curve.

**Key Findings:**
- Identified 5 "Critical Reward Cliffs" where rewards drop >10% despite difficulty increasing:
    - Shrouded Fen (-27.9%), Clockwork Halls (-14.7%), Celestial Archipelago (-19.6%), Thunder-Crag Coast (-30.9%), Shimmering Wastes (-26.9%).
- Uncovered a structural inconsistency: **The Frostfall Expanse** is Rank A (Lvl 25) while **The Celestial Archipelago** is Rank B (Lvl 28). This inverted ranking contributes to the reward drop.

**Outcome:**
- Published detailed report `.Jules/analysis/2026-03-07_progression_reward_gaps.md` with actionable recommendations for @GameBalancer.
- Recommendations include specific buff targets and resolving the Rank/Level conflict.

## 2026-02-27: Database Unavailability
**Focus:** Routine player metrics extraction.

**Methodology:**
- Attempted to query the MongoDB player database for class popularity and rank distribution metrics using `scripts/analysis/class_popularity.py`.

**Key Findings:**
- Connection to the main analytics database (`localhost:27017`) was refused or timed out, indicating no live data snapshot was provided for this cycle.

**Outcome:**
- No meaningful analysis could be performed on real player data today due to database unavailability. Resting and preparing for the next cycle.
