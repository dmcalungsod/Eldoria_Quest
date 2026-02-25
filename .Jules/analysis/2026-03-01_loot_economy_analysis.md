# 📊 Loot Economy Analysis Report — 2026-03-01

**Data Sources:** `monsters.json`, `adventure_locations.json`, `materials.py`

## 🌍 Location Analysis (Risk vs Reward)

| Location | Rank | Level | Avg Combat Power | Avg Loot Value (Gold) | Efficiency (Gold/CP) |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **Willowcreek Outskirts** | F | 1 | 1152 | 9.3g | 8.04 |
| **Whispering Thicket** | E | 5 | 2397 | 10.8g | 4.52 |
| **Deepgrove Roots** | D | 10 | 9755 | 18.4g | 1.89 |
| **The Ashlands** | D | 12 | 23843 | 26.6g | 1.12 |
| **The Shrouded Fen** | C | 15 | 21296 | 12.0g | 0.56 |
| **The Sunken Grotto** | C | 18 | 40373 | 29.8g | 0.74 |
| **The Crystal Caverns** | B | 20 | 51350 | 63.2g | 1.23 |
| **The Clockwork Halls** | B | 22 | 65856 | 29.2g | 0.44 |
| **The Forgotten Ossuary** | B | 24 | 77942 | 57.5g | 0.74 |
| **The Frostfall Expanse** | A | 25 | 142985 | 99.5g | 0.70 |
| **The Celestial Archipelago** | B | 28 | 209715 | 41.6g | 0.20 |
| **The Molten Caldera** | A | 30 | 185850 | 125.3g | 0.67 |
| **Gale-Scarred Heights** | A | 35 | 444180 | 72.8g | 0.16 |
| **The Shimmering Wastes** | A | 37 | 505860 | 70.3g | 0.14 |
| **The Void Sanctum** | S | 40 | 1180160 | 117.0g | 0.10 |

## 🔍 Deep Dive: Deepgrove Roots vs Shrouded Fen

- **Deepgrove Roots (Rank D):** 18.4g / 9755 CP = **1.89** eff
- **Shrouded Fen (Rank C):** 12.0g / 21296 CP = **0.56** eff

**⚠️ IMBALANCE DETECTED:** Lower-rank zone `Deepgrove Roots` is **3.4x** more efficient than higher-rank `Shrouded Fen`. Players are incentivized to farm the easier zone.

## 🚨 Outliers & Anomalies (Top 10 Efficient Monsters)

| Monster | Tier | CP | Loot Value | Efficiency |
| :--- | :---: | :---: | :---: | :---: |
| Verdant Slime | Normal | 835 | 9.2g | 11.01 |
| Hollow Spiderling | Elite | 9112 | 74.5g | 8.18 |
| Fen Wisp | Normal | 4857 | 34.5g | 7.10 |
| Goblin Grunt | Normal | 1363 | 9.5g | 6.97 |
| Glimmer Slime | Normal | 1363 | 9.2g | 6.75 |
| Thicket Spider | Normal | 3768 | 19.5g | 5.17 |
| Goblin Scout | Normal | 2025 | 9.5g | 4.69 |
| Bramble Goblin | Normal | 2025 | 9.5g | 4.69 |
| Rookwood Shade | Elite | 22365 | 89.5g | 4.00 |
| Feral Stag | Boss | 166492 | 627.0g | 3.77 |