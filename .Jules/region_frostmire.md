# Region Design: Frostmire

## Core Identity
- **Name:** Frostmire
- **Theme:** A desolate, frozen permafrost swamp where the biting cold and treacherous sinking ice create a relentless struggle for survival. The atmosphere is quiet, oppressive, and hauntingly still.
- **History:** Once a thriving marshland, it was instantly frozen over during a massive magical backlash related to The Sundering. The sudden deep freeze trapped ancient magic and beasts alike beneath the ice.
- **Cultural Flavor:** Avoided by most, except for desperate scavengers and seasoned hunters looking for preserved ancient relics and rare, cold-adapted flora.

## Geography & Locations
- **The Hoarfrost Fens:** The outer edges where the ground is a mix of brittle ice and freezing mud.
- **The Shimmering Bogs:** Deeper areas where the ice is thin, hiding deep pools of freezing, magical water.
- **The Frozen Hollows:** The heart of the region, characterized by massive, jagged ice formations and preserved, ancient trees trapped in ice.

## Inhabitants
- **Factions:**
    - **The Iceborn Trackers:** A small band of survivalists who have adapted to the harsh conditions, offering guidance for a steep price.
- **Monsters:**
    - **Frostbite Crawler (Lvl 26):** Giant arthropods adapted to the cold, capable of blending in with the snow.
    - **Rime-Bound Ghoul (Lvl 27):** Undead preservation of ancient inhabitants, their bodies preserved and hardened by the frost.
    - **Glacial Weaver (Lvl 28):** Arachnids that spin webs of magically infused ice.
    - **The Permafrost Behemoth (Lvl 30 Boss):** A massive, ancient beast awakened from the deep freeze, covered in thick, icy armor.

## Gameplay Elements
- **Access Requirements:** Rank B (Level 26) and completion of "The Chill of the North" quest.
- **Exploration Mechanics:** Cold management (requires thermal gear to prevent gradual HP drain); careful navigation to avoid falling through thin ice (random agility checks).
- **Resources:**
    - **Frost-Touched Kelp:** Rare herb used in potent cooling draughts and potions.
    - **Rime Core:** Dropped by local monsters, used in cold-elemental crafting.
    - **Ancient Frozen Relic:** Rare drops with high exchange value or used in unique crafting recipes.
- **Dangers:**
    - **Extreme Cold:** Gradual HP drain without proper gear (`thermal_insulation`).
    - **Thin Ice:** Random events that can cause significant damage or require immediate supply usage to escape.

## Integration with Existing Systems
- **Guild Ranks:** Fits into the mid-to-high progression tier (Rank B), offering a challenging alternative to other Rank B locations.
- **Quests:** "The Chill of the North" serves as an introduction. Follow-up quests could involve recovering ancient relics or hunting the Permafrost Behemoth.
- **Crafting:** Introduces new cold-themed materials for mid-to-late game gear.

## Agent Coordination
- **GameForge:** Implement the new monsters (`frostbite_crawler`, `rime_bound_ghoul`, `glacial_weaver`, `permafrost_behemoth`) and gatherables (`frost_touched_kelp`, `rime_core`, `ancient_frozen_relic`).
- **StoryWeaver:** Write atmospheric, chilling flavor text for exploration and quest dialogue.
- **Grimwarden:** Balance the Cold survival mechanics and the "Thin Ice" random events.
- **GameBalancer:** Tune the drop rates and EV for the new resources to fit the Rank B economy.
- **Equipper:** Ensure players have access to `thermal_insulation` gear appropriate for this level.
- **Namewright:** Refine the names of the locations and specific NPCs.
- **ChronicleKeeper:** Add achievements for surviving the cold and defeating the Permafrost Behemoth.
