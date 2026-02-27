# Region Design: The Rust-Wastes

## Core Identity
- **Name:** The Rust-Wastes
- **Theme:** Industrial decay, scavenging, corrupted technology.
- **History:** Once a disposal site for the Clockwork Halls' failed experiments, this valley has become a breeding ground for mechanical horrors and desperate scavengers. The Sundering animated the refuse, giving life to piles of scrap and pools of oil.
- **Culture:** The few sentient inhabitants are Kobold scavengers who worship "The Great Machine" (a massive, broken engine at the center of the wastes) and adorn themselves in rusted armor.

## Geography
- **Scrapheap Canyon:** A winding maze of jagged metal shards and unstable piles of debris.
- **The Oil Pits:** Treacherous pools of black, viscous sludge that slow movement and burn when ignited.
- **Gear-Grinder Pass:** A narrow choke point where ancient, broken machinery still spins and crushes anything foolish enough to get close.

## Inhabitants
- **Factions:**
    - **The Rust-Biters:** A tribe of Kobold scavengers who aggressively defend their trash.
    - **The Galvanized:** A cult of constructs that seem to be building *something* from the scrap.
- **Monsters:**
    - **Scrap Rat (Lvl 8):** oversized vermin with metal shards embedded in their fur.
    - **Kobold Scavenger (Lvl 9):** Cunning trap-makers armed with makeshift weapons.
    - **Oil Slime (Lvl 9):** A sticky, flammable ooze that coats its victims in tar.
    - **Junk Golem (Lvl 10):** A lumbering construct of random debris, surprisingly durable.
    - **The Galvanized Horror (Lvl 12 Boss):** A monstrosity of fused metal and flesh, guarding the heart of the wastes.

## Gameplay
- **Access:** Rank E (Level 8). Fills the progression gap between *Whispering Thicket* and *Deepgrove Roots*.
- **Mechanics:**
    - **Tetanus Risk:** Physical attacks have a chance to inflict a damage-over-time bleed.
    - **Oil Slick:** Fire attacks deal bonus damage to oil-coated enemies.
- **Resources:**
    - **Common:** Rusted Scrap, Iron Ore
    - **Uncommon:** Copper Wire, Oil Flask (New/Existing?), Bolt & Nut
    - **Rare:** Intact Gear
- **Dangers:** Ambushes from scrap piles, environmental hazards (falling debris).

## Integration with Existing Systems
- **Rank:** Fits perfectly into Rank E.
- **Materials:** Utilizes `rusted_scrap` and `copper_wire` which are already in the game but underutilized at low levels.
- **Quests:** Potential for "Recover the Lost Tech" or "Cull the Scavengers" quests.

## Agent Coordination
- **GameForge:** Implement monsters (IDs 161-165) and loot tables.
- **StoryWeaver:** Write flavor text for "Scrapheap Canyon" and boss encounters.
- **Namewright:** Confirm names for "The Galvanized Horror".
