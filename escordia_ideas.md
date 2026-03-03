# Ideas to Adapt from Escordia-RPG-System for Eldoria Quest

This document contains several ideas inspired by the `Escordia-RPG-System` codebase that could be adapted to improve `Eldoria Quest`.

## 1. Instance-Based Dungeons (from `dungeon.py`)
Escordia uses an instance-based dungeon progression system where players battle a specific `enemy_count` from a defined `enemy_list` before confronting a final `boss`.
* **Adaptation for Eldoria Quest:** Introduce a new type of `AdventureSession` focused on **Instanced Expeditions**. Rather than the standard time-based auto-adventure, this would allow players to enter a dungeon floor requiring X encounters before a guaranteed boss fight, yielding specific `loot_pool` rewards if successful.

## 2. Dynamic Area-Based Shops (from `shop.py`)
In Escordia, shops are tied directly to an `area_number`. Players can only access certain items when exploring specific areas.
* **Adaptation for Eldoria Quest:** While Astraeon has a central Guild Exchange, we could introduce **Wandering Merchants** or **Outpost Shops** located in specific adventure regions. Players completing an expedition in a specific region might gain access to a localized shop containing exclusive consumable items or crafting recipes.

## 3. Job Mastery and XP Scaling (from `job.py`)
Escordia's `Job` class features distinct `xp_factor` attributes, allowing different jobs to level up at different rates, alongside `preferred_weapons`.
* **Adaptation for Eldoria Quest:** Enhance the current Class system (e.g., Novice, Warrior) to allow them to be leveled up independently with varying XP requirements. Instead of tying level-ups strictly to the player's core stats, leveling up specific classes could unlock specialized class-based skills or passive combat multipliers.

---

*Note for @Foreman: These are preliminary ideas gathered from a comparative analysis of the `Escordia-RPG-System` and `Eldoria_Quest` architectures. Please review to decide which of these we should implement into the `game_systems` module.*