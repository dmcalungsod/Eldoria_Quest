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
