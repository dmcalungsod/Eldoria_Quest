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

## 2026-03-03 — Novice Protection Implementation

**Learning:** Level 1-5 players were frequently dying or retreating during early encounters due to low starting max HP and high incoming damage relative to early gear. Players hit the 30% auto-retreat threshold rapidly, making early game unplayable and frustrating.
**Action:** Implemented a Novice Protection buff injected via `AdventureSession._fetch_session_context()` for players level <= 5. The buff grants `novice_protection_reduction` (halves incoming damage) and `novice_protection_boost` (+20% outgoing damage). This smooths the onboarding curve while retaining original stats, allowing novices to gain enough XP and materials to naturally overcome the initial hurdle. Also patched a `KeyError` with `{m_name}` in `CombatPhrases.player_buff()` caused when abilities target the player but contextualize the enemy.