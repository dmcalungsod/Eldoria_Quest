## 2024-05-22 — Potion Economy Rebalance

**Learning:** Low-level potion prices (15 Aurum) created infinite sustain loops. Players could farm low-level monsters (Slimes/Goblins) and buy more healing than the damage they took, trivializing survival. This undermined the "Grim Survival" tone. Additionally, `hp_potion_2` was less efficient than `hp_potion_1`, discouraging progression.

**Action:** Increased `hp_potion_1` to 40 Aurum and `hp_potion_2` to 90 Aurum. This makes `hp_potion_2` slightly more efficient (0.75 Aurum/HP) than `hp_potion_1` (0.8 Aurum/HP), encouraging upgrades. Simulation confirms Slime farming is now sustainable but tight (+2.8 HP/fight), while Goblin farming requires appropriate leveling to be profitable.

## 2024-05-26 — Luck Stat Scaling for All Rarities

**Learning:** The `LootCalculator` restricted Luck scaling exclusively to "High Rarity" items (Epic, Legendary, Mythical). This rendered the LCK stat effectively useless for 90% of gameplay, as it did not improve drop rates for Common, Uncommon, or Rare materials—the core components of the "Material-Driven Survival" economy. Players investing in Luck saw no return on investment for general farming.

**Action:** Removed the rarity restriction in `LootCalculator`. Luck now applies its multiplier `(1 + Luck/1000)` to ALL item drops. This ensures that Luck builds are viable for resource gathering without breaking the economy, as the scaling factor is conservative (e.g., 100 Luck = 1.1x multiplier).

## 2026-03-02 — Auto-Adventure Fatigue Scaling

**Learning:** Auto-adventures lacking dynamic difficulty scaling allowed players to farm indefinitely with sufficient healing, bypassing the intended "risk vs reward" curve of long expeditions. Static monster stats meant the 10th hour was no more dangerous than the 1st.

**Action:** Implemented a fatigue system in `AdventureSession`. Expeditions longer than 4 hours now incur a +5% monster damage multiplier per subsequent hour. This creates a soft cap on session length, forcing players to weigh the risk of extended farming against the escalating danger, reinforcing the survival theme. The scaling is transient (calculated per step) to avoid permanently buffing monster records in the database.

## 2026-03-08 — Buffing End-Game Adventure Zones

**Learning:** Players were not engaging with "Clockwork Halls" and "The Void Sanctum" due to low reward-to-risk ratio. The "Void Heart" was unobtainable outside of the boss, making the zone feel incomplete.
**Action:**
1.  **Clockwork Halls (Rank B):** Added `steam_core` (10%) and `clockwork_heart` (1%) to gatherables. Increased `magic_stone_medium` gatherable chance to 35% and `magic_stone_large` to 10%. Buffed Cogwork Spider and Automaton Knight drops.
2.  **The Void Sanctum (Rank S):** Added `void_heart` (2%) and `null_stone` (10%) to gatherables. Increased `magic_stone_flawless` gatherable chance to 30%. Buffed Void Stalker and Entropy Drake drops.
**Result:** These changes should make end-game farming more viable and less reliant on boss spawns for key crafting materials.

## 2026-03-08 — Buffing High-Tier Adventure Zones & Rank Logic Conflict

**Learning:** "Thunder-Crag Coast" and "Shimmering Wastes" (Rank A) lacked end-game material viability. Gatherables did not provide top-tier items consistently, and monster drop rates were too low to justify the danger relative to easier zones. Furthermore, a logical inconsistency existed between "Frostfall Expanse" (Level 25) and "Celestial Archipelago" (Level 28) both being Rank B, disrupting the intended difficulty-to-rank scaling up to Rank A (Level 30+).

**Action:**
1.  **Thunder-Crag Coast (Rank A):** Added `charged_core` (10%) to gatherables. Increased `magic_stone_large` chance to 20% by reducing lower tier items. Buffed drop amounts/chances across all native monsters and added `tempest_heart` to the elite Siren Matriarch drops.
2.  **Shimmering Wastes (Rank A):** Added `glass_heart` (1%) and buffed `concentrated_light` and `magic_stone_flawless` gatherable chances. Improved specific drop rates for all native monsters.
3.  **Celestial Archipelago:** Promoted from Rank B to Rank A to resolve the Level 28 vs Rank A/B inconsistency, realigning the late-game rank transition.

## 2026-03-02 — Rebalancing The Shrouded Fen and The Molten Caldera Economy

**Learning:** Analyst EV modeling highlighted massive imbalances: The Shrouded Fen (mid-game) under-rewarded players, while The Molten Caldera (late-game) vastly over-rewarded them. This broke the "material-driven survival" scarcity philosophy, allowing players to stockpile late-game materials too quickly while struggling mid-game.
**Action:** Rebalanced the gatherables and native monster drop tables for both zones to correct EV and align with intended tier difficulty. Increased EV for Shrouded Fen and decreased EV for Molten Caldera.

## 2026-03-08 — Economy Cliff Rebalance

**Learning:** When item values were previously buffed systemically, it created extreme dead zones because certain mid/end-game regions (Shrouded Fen, Clockwork Halls, Void Sanctum) had highly restricted drop rates that didn't scale effectively with the new item values, whereas other zones (Molten Caldera) accidentally maintained their high yields. This meant pushing to new zones strictly penalized players rather than rewarding them.
**Action:** When item values (`materials.json`) undergo systemic changes, always re-run `analyze_economy.py` to identify newly formed cliffs. Rebalance gatherables and monster weights concurrently to smooth out the Expected Value (EV) progression curve. Re-aligned The Shrouded Fen, The Clockwork Halls, The Void Sanctum, Thunder-Crag Coast, Shimmering Wastes, and Celestial Archipelago to meet scaling EV targets.

## 2026-03-04 — Auto-Adventure Economy Rebalance

**Learning:** EV tuning requires extreme precision after global material sell value updates. `analyze_economy.py` skips EV calculation for monsters not listed in `monsters.json` (like the ones intended for The Silent City of Ouros), making entire end-game locations deceptively poor in Total EV and causing massive progression cliffs between Rank A and Rank S zones.
**Action:** Always verify that newly introduced locations have their intended monsters explicitly created in the data files before trusting economy analyzer scripts. Rebalanced The Shrouded Fen, The Clockwork Halls, The Celestial Archipelago, and The Void Sanctum, and added missing Ouros monsters to ensure progression is rewarding and fair at higher ranks.

## 2026-03-13 — The Sunken Grotto Economy Rebalance

**Learning:** Analyst report showed The Sunken Grotto (Rank C, Level 18) underperforming severely (Total EV 312.6/hr) compared to The Shrouded Fen (Rank C, Level 15, Total EV 775.4/hr). This created an economy cliff early in mid-game progression.
**Action:** Increased monster drop rates for `coral_fragment`, `bioluminescent_scale`, `pearl`, `siren_voice_box` and added `magic_stone_large` and `abyssal_pearl` to Elite and Boss drops. Adjusted gatherables in `adventure_locations.json` to be more rewarding. Total EV for The Sunken Grotto increased to ~731.2/hr, putting it in line with Rank C expectations.
