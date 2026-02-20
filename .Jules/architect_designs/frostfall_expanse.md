# Expansion Design: The Frostfall Expanse

## Concept
A desolate, frozen wasteland where the sun never rises, cursed by the shattered remains of an ancient Ice Elemental. It serves as the **Rank A** progression zone, introducing severe environmental hazards and high-stakes survival.

## Lore (for StoryWeaver)
The Frostfall Expanse was once a fertile valley until the Sundering cracked the Elemental Plane of Ice above it. Now, it is a tomb of eternal winter. Adventurers speak of "The Cold That Bites"—a magical chill that ignores armor and drains the will to live. The few survivors huddle in the ruins of Frostwatch Keep.

## Location Specification (for Adventure System)
- **ID:** `frostfall_tundra`
- **Name:** The Frostfall Expanse
- **Emoji:** ❄️
- **Min Rank:** A
- **Level Req:** 25
- **Duration Options:** [60, 120, 240, 480]
- **Description:** "A blinding blizzard hides predators that hunt by body heat. The cold itself is an enemy."
- **Gatherables:**
  - `froststeel_ore` (Weight: 40)
  - `ever_ice` (Weight: 30)
  - `magic_stone_large` (Weight: 30)

## Monsters (for GameForge)
*IDs 106-110 to follow Crystal Caverns*

1.  **Frostbit Wolf (ID 106)** - *Common*
    -   **Level:** 26
    -   **Stats:** Fast, Medium ATK, Low DEF.
    -   **Skill:** *Pack Tactics* (Multi-hit).
    -   **Drops:** Wolf Pelt, Frost Fang.

2.  **Ice Construct (ID 107)** - *Common*
    -   **Level:** 27
    -   **Stats:** Slow, High HP, High DEF (Weak to Fire/Blunt).
    -   **Skill:** *Shatter* (Explodes on death for minor AOE).
    -   **Drops:** Glacial Shard, Ancient Gear.

3.  **Wendigo (ID 108)** - *Elite*
    -   **Level:** 29
    -   **Stats:** Very High ATK, Lifesteal.
    -   **Skill:** *Devour* (Heals on hit).
    -   **Drops:** Cursed Bone, Wendigo Antler.

4.  **Glacial Wyrm (ID 110)** - *Boss*
    -   **Level:** 32
    -   **Stats:** Massive HP, AOE Freeze.
    -   **Skill:** *Absolute Zero* (Stuns/Freezes player for 1 turn).
    -   **Drops:** Wyrm Heart, Froststeel Ore (Rare).

## Items & Equipment (for GameForge)
-   **Material:** *Froststeel Ore* (High-tier metal, blue-tinged).
-   **Material:** *Ever-Ice* (Unmelting ice for magic crafting).
-   **Weapon:** *Wyrmfang Dagger* (Chance to slow enemy).
-   **Armor:** *Glacial Plate* (High DEF, +Cold Resistance).

## Mechanics (for Tactician)
-   **Environmental Hazard:** *Sheer Cold*
    -   Every 10 turns in combat, the player takes **5% Max HP** damage as "Cold Damage" unless they have a "Warmth" buff (from potion or campfire item).
    -   *Implementation Note:* Add `check_environment` step in `AdventureSession.simulate_step`.
-   **Status Effect:** *Frostbite*
    -   Reduces AGI by 20%. Applied by Wolf and Wyrm.

## Integration Plan
1.  **GameForge:** Add monsters to `monsters.py` and items to `items` module.
2.  **Tactician:** Implement "Environmental Hazard" logic in `AdventureSession`.
3.  **AdventureManager:** Register `frostfall_tundra` in `adventure_locations.py`.
4.  **ChronicleKeeper:** Add achievement "Icebreaker" for defeating the Glacial Wyrm.
