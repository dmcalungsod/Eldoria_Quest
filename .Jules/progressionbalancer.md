## 2025-02-18 — Rank Overlap and Curve Smoothing

**Learning:** Rank F -> E progression was trivialized by quests providing almost all necessary kills. Players could advance without engaging in meaningful exploration or combat outside of specific quest objectives. Additionally, Rank B lacked an intermediate Elite Kill requirement, creating a sudden cliff at Rank A.
**Action:** Increased Rank F `normal_kills` to 40 (from 25) and Rank E to 100 (from 80) to enforce extra effort. Added `elite_kills: 65` to Rank B to smooth the curve towards Rank A.

## 2025-05-18 — Early Game Quest Overlap & Endgame Kill Disconnect

**Learning:** Rank F and E kill requirements were largely fulfilled by quest completion (3 quests ~18 kills, Rank F req 25), trivializing the "exploration" aspect. Also, Ranks B and above dropped the `normal_kills` requirement entirely, breaking the "grim survival" philosophy where hordes must still be culled.
**Action:** Increased Rank F `normal_kills` (25 -> 40) and Rank E (75 -> 120) to enforce meaningful kill quotas beyond quests. Reintroduced `normal_kills` for Rank B (600) through SS (1500) to maintain progression pressure.
