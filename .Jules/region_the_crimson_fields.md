# Region Design: The Crimson Fields

## Core Identity
- **Name:** The Crimson Fields
- **Theme:** A haunted, fog-shrouded battlefield where the dead do not rest. Rusty weapons stick out of the earth like gravestones.
- **History:** Here, the Vanguard of Eldoria made their last stand against the first wave of Void beasts. Their sacrifice bought time for the survivors to seal the rifts, but their spirits are trapped in an eternal loop of battle.
- **Cultural Flavor:** Considered forbidden ground by locals. Only "Grave Wardens" venture here to lay spirits to rest or scavenge ancient relics.

## Geography & Locations
- **The Avenue of Spears:** A road lined with impaled weaponry.
- **Fortress Ruin:** A crumbled keep where the commander fell.
- **The Weeping Creek:** A stream that runs red with rust and ghostly essence.
- **Mass Grave Hill:** A mound where thousands are buried.

## Inhabitants
- **Factions:**
    - **Grave Wardens:** Neutral monks/clerics who fight the undead.
    - **Scavengers:** Bandits looting the dead.
- **Monsters:**
    - **Restless Squire (Lvl 14):** Weak undead.
    - **Tarnished Knight (Lvl 14):** Heavily armored but slow.
    - **Spectral Archer (Lvl 15):** Ranged threats.
    - **Carrion Crow (Lvl 13):** Feeds on magical residue.
    - **The Fallen General (Lvl 16 Boss):** A powerful revenant.

## Gameplay Elements
- **Access Requirements:** Rank D (Level 14). Accessible from the Guild Map.
- **Exploration Mechanics:** Standard exploration with a focus on morale (narrative).
- **Resources:**
    - **Tarnished Steel:** Scrap metal.
    - **Spirit Dust:** Magic component.
    - **Ghostly Essence:** Rare drop.
    - **Crimson Flower:** Alchemical ingredient (grows on blood).
- **Dangers:**
    - **Hauntings:** Random morale debuffs.
    - **Old Traps:** Unexploded magical mines/runes.

## Integration with Existing Systems
- **Guild Ranks:** Fills the gap in Rank D (12 -> 15), providing a combat-focused alternative to the Ashlands.
- **Crafting:** Introduces `Spirit Dust` and `Tarnished Steel` for mid-tier crafting recipes.
- **Quests:** Potential for "Recover the General's Sword" or "Lay the Spirits to Rest" quests.
- **Atmosphere:** Features unique atmospheric text describing the fog, the rust, and the whispers of the dead.

## Agent Coordination
- **GameForge:** Implement monsters (`Restless Squire`, `Tarnished Knight`, `Spectral Archer`, `Carrion Crow`, `The Fallen General`) and items (`Tarnished Steel`, `Spirit Dust`, `Ghostly Essence`, `Crimson Flower`).
- **DepthsWarden:** Potential connection to a "Catacombs" dungeon floor.
- **StoryWeaver:** Expand on the "Vanguard" lore.
- **Namewright:** "The Crimson Fields" is evocative. Locations like "Avenue of Spears" fit well.

## JSON Implementation (Draft)
```json
    "crimson_fields": {
        "name": "The Crimson Fields",
        "emoji": "⚔️",
        "min_rank": "D",
        "level_req": 14,
        "duration_options": [
            60,
            120,
            240
        ],
        "monsters": [
            [
                "monster_restless_squire",
                30
            ],
            [
                "monster_tarnished_knight",
                30
            ],
            [
                "monster_spectral_archer",
                25
            ],
            [
                "monster_carrion_crow",
                15
            ]
        ],
        "night_monsters": [
            [
                "monster_tarnished_knight",
                40
            ],
            [
                "monster_spectral_archer",
                40
            ],
            [
                "monster_restless_squire",
                20
            ]
        ],
        "conditional_monsters": [
            {
                "monster_key": "monster_fallen_general",
                "weight": 5,
                "min_level": 16
            }
        ],
        "description": "A haunted battlefield shrouded in fog. Rusty weapons and the spirits of the fallen litter the ground.",
        "gatherables": [
            [
                "tarnished_steel",
                40
            ],
            [
                "spirit_dust",
                30
            ],
            [
                "crimson_flower",
                20
            ],
            [
                "magic_stone_medium",
                10
            ]
        ],
        "special_events": [
            "trap_pit",
            "hidden_stash",
            "ancient_shrine"
        ]
    }
```
