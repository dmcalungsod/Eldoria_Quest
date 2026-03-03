# Economy Progression Deep Dive Analysis — 2026-03-10

**Data Period:** Current Codebase (Synthetic Modeling)
**Topic:** Auto-Adventure Overhaul Economy Imbalances (Task 2.2)

## Key Findings

An in-depth analysis of specific Auto-Adventure zones reveals the exact reasons behind the Expected Value (EV) gaps highlighted in previous reports.

- **The Shrouded Fen (Rank C, Lvl 15):**
  - EV is dragging because the monsters drop only low-value `magic_stone_small` and `magic_stone_medium` with low drop rates, yielding a tiny 12-16 EV per kill. For comparison, it is outclassed by earlier zones.
- **The Clockwork Halls (Rank B, Lvl 22):**
  - While gathering EV is slightly better, combat drops from regular monsters are abysmal (16-40 EV per kill). Only the Automaton Knight provides decent value.
- **The Celestial Archipelago (Rank A, Lvl 28):**
  - The drop tables are extremely poor for a Rank A zone, with kills averaging 25-43 EV, aside from the Ruin Stalker. Gathering value is also weak without any high-end drops like flawless stones or rare cores.
- **The Shimmering Wastes (Rank A, Lvl 37):**
  - Suffers from an inconsistent drop table. While some monsters drop high-value items, others like the Prism Golem only drop `prism_shard` and `obsidian_shard`, yielding a measly 36 Total EV/kill which drags down the average.
- **The Silent City of Ouros (Rank S, Lvl 42):**
  - 🔴 **CRITICAL:** Three out of four monsters (`temporal_wraith`, `hollowed_sentinel`, `abyssal_creeper`) have completely empty drop tables and drop zero Aurum. This entirely ruins the zone's EV.

## Recommendations

1. **GameBalancer:**
    - **The Shrouded Fen:** Buff monster drop rates or add a mid-tier material drop to all monsters to bring kill EV up.
    - **The Clockwork Halls:** Increase the drop rate of `steam_core` and `magic_stone_large` across more monsters to push the total EV/Hr closer to the 900 Aurum target.
    - **The Celestial Archipelago:** Redesign the drop tables entirely. A Rank A zone should have monsters dropping materials worth 100+ EV on average, not 25-43.
    - **The Shimmering Wastes:** Buff the drops of the Prism Golem and increase the `concentrated_light` drop rates on the Mirage Spirit and Sun-Scorched Wraith.

2. **GameForge:**
    - **The Silent City of Ouros:** Implement the missing drop tables for `temporal_wraith`, `hollowed_sentinel`, and `abyssal_creeper` immediately. They currently drop absolutely nothing, breaking the Rank S economy.

## Methodology
- Extracted and computed EV for each specific gatherable and monster drop in the targeted zones using the base economy utilities (`calculate_expected_value_stats`).
- Calculated the expected value per gather and per kill, factoring in spawn/gather weights.

## Attachments
- `docs/analysis/deep_dive.txt` (Data dumped from specific zone script)
