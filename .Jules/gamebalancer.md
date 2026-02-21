## 2024-05-22 — Potion Economy Rebalance

**Learning:** Low-level potion prices (15 Aurum) created infinite sustain loops. Players could farm low-level monsters (Slimes/Goblins) and buy more healing than the damage they took, trivializing survival. This undermined the "Grim Survival" tone. Additionally, `hp_potion_2` was less efficient than `hp_potion_1`, discouraging progression.

**Action:** Increased `hp_potion_1` to 40 Aurum and `hp_potion_2` to 90 Aurum. This makes `hp_potion_2` slightly more efficient (0.75 Aurum/HP) than `hp_potion_1` (0.8 Aurum/HP), encouraging upgrades. Simulation confirms Slime farming is now sustainable but tight (+2.8 HP/fight), while Goblin farming requires appropriate leveling to be profitable.

## 2024-05-26 — Luck Stat Scaling for All Rarities

**Learning:** The `LootCalculator` restricted Luck scaling exclusively to "High Rarity" items (Epic, Legendary, Mythical). This rendered the LCK stat effectively useless for 90% of gameplay, as it did not improve drop rates for Common, Uncommon, or Rare materials—the core components of the "Material-Driven Survival" economy. Players investing in Luck saw no return on investment for general farming.

**Action:** Removed the rarity restriction in `LootCalculator`. Luck now applies its multiplier `(1 + Luck/1000)` to ALL item drops. This ensures that Luck builds are viable for resource gathering without breaking the economy, as the scaling factor is conservative (e.g., 100 Luck = 1.1x multiplier).
