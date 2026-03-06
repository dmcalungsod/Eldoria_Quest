## 2025-02-18 — Rank Overlap and Curve Smoothing

**Learning:** Rank F -> E progression was trivialized by quests providing almost all necessary kills. Players could advance without engaging in meaningful exploration or combat outside of specific quest objectives. Additionally, Rank B lacked an intermediate Elite Kill requirement, creating a sudden cliff at Rank A.
**Action:** Increased Rank F `normal_kills` to 40 (from 25) and Rank E to 100 (from 80) to enforce extra effort. Added `elite_kills: 65` to Rank B to smooth the curve towards Rank A.

## 2025-05-18 — Early Game Quest Overlap & Endgame Kill Disconnect

**Learning:** Rank F and E kill requirements were largely fulfilled by quest completion (3 quests ~18 kills, Rank F req 25), trivializing the "exploration" aspect. Also, Ranks B and above dropped the `normal_kills` requirement entirely, breaking the "grim survival" philosophy where hordes must still be culled.
**Action:** Increased Rank F `normal_kills` (25 -> 40) and Rank E (75 -> 120) to enforce meaningful kill quotas beyond quests. Reintroduced `normal_kills` for Rank B (600) through SS (1500) to maintain progression pressure.

## 2026-03-03 — Boss Kill Bottleneck & Early Game Exploration

**Learning:**
1. **Early Game Overlap:** Rank F and E kill requirements were still slightly trivialized by quest kills (3 quests ~15-20 kills vs 40 req). Increasing this forces players to engage with the new Auto-Adventure system to grind "wild" kills.
2. **Mid/Late Game Bottleneck:** Boss kill requirements (Rank C: 5, B: 10, A: 20, S: 35) were scaling aggressively while Boss spawn rates remain low (often 5% conditional). This created a potential 100+ hour grind wall per rank.

**Action:**
1. Increased Rank F `normal_kills` (40 -> 50) and Rank E (120 -> 150) to encourage exploration/auto-adventure.
2. Reduced Boss Kill requirements significantly (C: 5->2, B: 10->4, A: 20->8, S: 35->15, SS: 50->25) to align with actual spawn probabilities and prevent progression stalling.

## 2026-03-04 — Rank D Kill Requirement Trivialized by Quests

**Learning:** Rank D required +10 quests and +50 kills compared to Rank E. Since 10 quests typically involve ~50 kills, the kill requirement was entirely redundant, removing the need for exploration.
**Action:** Increased Rank D `normal_kills` to 250 (+100 delta) to enforce ~50 kills from non-quest sources.

## 2026-03-09 — Rank D Kill Tuning & Endgame Boss Smoothing

**Learning:**
1. **Rank D Still Trivial:** Even with 250 kills, the 20 quest requirement often resulted in players naturally hitting ~280+ kills just by doing quests (assuming ~8 kills/quest + incidental encounters). The "exploration gap" was non-existent.
2. **Endgame Wall:** Despite previous adjustments, the gap between Rank A (8 boss kills) and S (15 boss kills) remained a massive statistical hurdle (7 extra boss kills = ~140 encounters at 5% spawn). This felt more like a "luck gate" than a skill gate.

**Action:**
1. **Rank D:** Increased `normal_kills` to **300**. This enforces a distinct gap that requires dedicated exploration or auto-adventure sessions outside of quest objectives.
2. **Endgame Smoothing:** Reduced boss kill requirements further to align with reasonable playtime expectations:
   - Rank A: 8 -> **6**
   - Rank S: 15 -> **10**
   - Rank SS: 25 -> **20**

## 2026-03-02 — Integrating Auto-Adventure Progress into Ranks

**Learning:** The auto-adventure system (TimeWeaver) introduced a massive new core loop, but it was not integrated into rank progression. This meant players could engage exclusively with the new system but still be gatekept by manual quest completion or kill requirements they weren't organically achieving.
**Action:** Integrated `total_expeditions` as a core requirement for all ranks (F: 2 -> SS: 50) in `rank_system.py` using data from `get_exploration_stats`. This formally links the new auto-adventure loop to guild advancement.

## 2026-03-05 — Continuing Auto-Adventure Integration into Ranks

**Learning:** While `total_expeditions` integrated part of Auto-Adventure progress into ranks, it allowed players to circumvent the difficulty intended by time gating. Expeditions can be short, allowing players to meet the total expeditions metric without committing to the extended duration necessary to match intended progression pace.
**Action:** Added `total_adventure_minutes` as a requirement for all ranks (F: 60 minutes -> SS: 19,200 minutes). This forces a cumulative time investment from auto-adventuring, aligning its advancement with the system's "grim survival" philosophy.

## 2026-03-12 — Rank B Level Requirements Conflict

**Learning:** The Celestial Archipelago had an incorrect `min_rank` requirement of "A" while its `level_req` was 28. Since Rank A generally corresponds to Level 30+ content (e.g., Molten Caldera), this created a logic conflict that locked level 28 Rank B players out of appropriate content.
**Action:** Changed `min_rank` from "A" to "B" for `celestial_archipelago` in `game_systems/data/adventure_locations.json` to smooth the progression curve between Rank B and Rank A.
