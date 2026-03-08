# Architect Journal

## 2025-10-28 — Expansion Design: The Frostfall Expanse

**Design Choice:**
Chosen "Major Content Expansion" over "New Class" or "Skill Tree Expansion".
**Reasoning:**
- The game currently has a solid class foundation (Warrior, Mage, Rogue, Cleric, Ranger) but lacks high-tier content beyond Rank B (Crystal Caverns).
- An expansion provides a concrete goal for players and integrates multiple systems (Combat, Crafting, Exploration).

**Theme Alignment:**
- "The Frostfall Expanse" reinforces the "Grim Survival" tone.
- The "Sheer Cold" mechanic adds a layer of survival pressure beyond simple HP management, forcing strategic preparation (potions/warm gear).

**Integration Notes:**
- **Security:** The new "Cold Damage" mechanic must be calculated server-side in `AdventureSession` to prevent client-side negation.
- **Economy:** High-value drops (Wyrm Heart) should be rare to prevent inflation.
- **Lore:** Connects to the "Sundering" via the cracked Elemental Plane.

**Next Steps:**
- Monitor implementation by Tactician (Environment Mechanics) and GameForge (Assets).
- Consider a future class "Cryomancer" or "Survivor" that utilizes this zone's mechanics specifically.

## Class Design: The Alchemist

**Design Choice:**
New Class: Alchemist (Survivor/Pragmatist).

**Reasoning:**
- The "Frostfall Expanse" design suggested a "Survivor" class.
- The current class roster lacks a "Debuffer/Controller" or "Item Specialist".
- Fits the "Material-driven survival" theme perfectly.
- Forces the implementation of Player Debuffs in `CombatEngine`, which benefits all future designs.

**Theme Alignment:**
- Grim, scientific, desperate. "While mages study stars, I study dirt."
- Uses monster parts, reinforcing the core gameplay loop (Kill -> Loot -> Use).

**Integration Notes:**
- **CombatEngine Limitation Identified**: Player skills currently lack `debuff` support (only Monsters use it via `MonsterAI`). This is a critical gap.
- **Solution**: Explicitly requested `Tactician` to add `debuff` parsing for player skills.
- **GameForge**: Needs new weapon types or re-skinned daggers ("Scalpels").

**Next Steps:**
- Coordinate with Tactician to unlock the `debuff` mechanic.
- Once implemented, verify "Acid Flask" applies "Defense Down".

## 2026-02-24 — System Design: The Eldoria Codex

**Design Choice:**
Major Content Expansion: The Eldoria Codex (Bestiary, Atlas, Armory).

**Reasoning:**
- **Player Demand:** "More Lore" is a top request in `feedback.md`.
- **Engagement:** Moves the game from "grind to level up" to "grind to collect".
- **Roadmap:** Explicitly listed as a "Future Concept" in `roadmap.md`.
- **Timing:** With Frostfall Expanse and Alchemist in progress, a meta-system is needed to tie content together.

**Theme Alignment:**
- "Knowledge is Survival": Fits the pragmatic tone.
- Rewards are practical (Damage %, XP %) rather than just cosmetic.

**Integration Notes:**
- **Database:** Requires a new `player_codex` collection. Schema designed to be extensible.
- **Combat:** `CombatEngine` needs a hook for kill tracking.
- **Exploration:** `AdventureSession` needs a hook for location visits.

**Next Steps:**
- Notify `DatabaseManager` to implement schema.
- Notify `CodexKeeper` (or `ChronicleKeeper`) to begin UI implementation.

## 2026-03-15 — Blueprint Finalization: Alchemist Class

**Deliverable:**
Detailed Design Document: `.Jules/architect_designs/class_alchemist.md`

**Key Mechanics:**
- **Hybrid Stats:** High MAG (Potency) + DEX (Accuracy). Breaks the single-stat dependency seen in Warrior/Mage.
- **Potion Efficiency:** Introduced "Field Medic" passive to scale item healing, adding value to the Crafting loop.
- **Resource Management:** Skills consume MP *and* Items (conceptually), reinforcing the survival theme.

**Integration Directives:**
- **Tactician:** Provided exact JSON schema for `corrosive_flask` (Debuff: END -10%) and `volatile_mixture` (AoE Stun).
- **GameForge:** Specified "Alchemist's Satchel" accessory to boost potion duration.
- **Quest:** "The Magnum Opus" designed to gate the class ultimate behind a crafting challenge.

**Status:**
Blueprint ready for implementation.

## 2026-03-27 — Class Expansion: Warrior Skill Tree

**Design Choice:**
Skill Tree Expansion for the Warrior Class.

**Reasoning:**
- **Depth:** Current classes are shallow (3 skills). A skill tree adds meaningful progression and choice.
- **Identity:** Splits the generic "Warrior" into distinct "Juggernaut" (Tank) and "Berserker" (DPS) archetypes.
- **Foundation:** Establishes a pattern for other classes (Mage: Pyromancer vs Cryomancer, etc.).

**Theme Alignment:**
- "Survive or Destroy": Fits the grim tone.
- **Risk/Reward:** The Berserker path introduces self-damage mechanics, reinforcing the survival aspect.

**Integration Notes:**
- **CombatEngine:** Requires new mechanics: `self_damage_percent` (Recoil) and `kill_heal_percent` (Lifesteal on kill).
- **GameForge:** Needs 7 new skills added to `skills_data.py`.
- **ChronicleKeeper:** Titles for mastering paths encourage replayability.

**Deliverable:**
Detailed Design Document: `.Jules/architect_designs/skill_tree_warrior.md`

## 2026-02-25 — Expansion Blueprint: Survival & Logistics

**Design Choice:**
Major Content Expansion: The Survival & Logistics Update.

**Reasoning:**
- **Strategic Depth:** Moves long adventures from passive waiting to active preparation.
- **Economy:** Supply consumption creates a necessary material/gold sink.
- **Theme:** Directly supports the "Grim Survival" pillar—the world itself is dangerous.

**Key Mechanics:**
- **Fatigue System:** Soft cap on adventure length (16+ steps) via stacking monster buffs.
- **Regional Hazards:** Environmental debuffs (Cold, Heat, Corruption) requiring specific mitigation.
- **Supply System:** New loadout slot for consumable tools (Torches, Climbing Kits, Bedrolls).

**Integration Notes:**
- **Tactician:** Needs to update `AdventureSession` to apply Hazard debuffs and check supply triggers (e.g., auto-rest).
- **GameForge:** Requires 8 new items and associated crafting recipes.
- **Palette:** UI needs a "Supply Selection" screen before adventure start.

**Deliverable:**
Detailed Design Document: `.Jules/architect_designs/expansion_survival_logistics.md`


## 2026-02-28
- **Focus:** Mage Skill Tree Expansion
- **Outcome:** Designed the Elementalist (DPS/AoE) and Arcanist (Utility/Control) paths.
- **Key Insight:** Balancing MP cost and AoE is crucial for mages, introduced a passive (Mana Syphon) to help sustain high MP costs in long fights.
- **Artifact:** `.Jules/architect_designs/skill_tree_mage.md`

## 2026-03-01 — Class Expansion: Cleric Skill Tree

**Design Choice:**
Skill Tree Expansion for the Cleric Class.

**Reasoning:**
- **Depth:** Like the Warrior, the Cleric needs branching paths for varied playstyles. The current "just a healer" identity is too basic.
- **Identity:** Establishes the "Zealot" (DPS/Debuffer) and "Penitent" (Healer/Support) archetypes, offering an aggressive holy caster playstyle and a dedicated self-sacrificing healer playstyle.

**Theme Alignment:**
- "Grim Survival": The Light is described not as gentle, but as a "searing flame." Penitent healing is themed around self-sacrifice, tying into the broader game philosophy.

**Integration Notes:**
- **CombatEngine:** Requires new mechanics: `conditional_multiplier` (for healing based on low HP), `regen_percent` (heal over time), `cure_status: ["all"]`, and `invulnerable` status.
- **GameForge:** Needs 5 new skills added to `skills_data.py`.
- **ChronicleKeeper:** Titles for mastering paths and a new achievement encourage replayability and thematic engagement.

**Deliverable:**
Detailed Design Document: `.Jules/architect_designs/skill_tree_cleric.md`

## 2026-03-02 — Expansion Blueprint: Guild Halls

**Design Choice:**
Major Content Expansion: Guild Halls (Player Housing & Shared Resources).

**Reasoning:**
- **Economy:** Players accumulate massive stockpiles of common and uncommon materials from auto-adventures. We need a meaningful, long-term material sink.
- **Engagement:** Provides a tangible, upgradable representation of a player's progress and a hub for displaying Codex/Bestiary achievements (Trophies).
- **Roadmap:** Fulfills the "Guild Halls" concept listed in the future roadmap.
- **Multiplayer Foundation:** Establishes the infrastructure for true "Companies" (multiplayer guilds) sharing a physical space and pooled resources.

**Theme Alignment:**
- "Grim Survival": Halls are not luxury estates; they are fortified strongholds reclaimed from the Sundering. Upgrades directly impact survival (Infirmary, Apothecary) rather than just being cosmetic.
- The cost to maintain them (upkeep) reinforces the constant pressure of Eldoria.

**Integration Notes:**
- **Economy:** Requires new crafted "Building Materials" (GameForge) and exponential upgrade costs to drain the economy (GameBalancer).
- **Combat/Exploration:** The Infirmary provides a small pre-expedition shield and reduces rest penalties, directly hooking into `AdventureSession`.
- **UI:** The Hall interface needs to follow the One UI Policy, acting as a persistent management screen (Palette).

**Deliverable:**
Detailed Design Document: `.Jules/architect_designs/expansion_guild_halls.md`

## 2026-03-10 — Expansion Blueprint: The Lost Tomes (Skill Books)

**Design Choice:**
Major Content Expansion/System: The Lost Tomes (Consumable Skill Books).

**Reasoning:**
- **Progression:** The game needs horizontal progression for players who reach max level or complete all base skill trees.
- **Engagement:** High-level bosses needed better chase items besides just `magic_stone_flawless` or stat sticks.
- **Class Parity:** Specifically addresses Foreman's assignment to ensure Alchemist and Rogue are competitive with the 100% popularity Warrior class, without issuing direct nerfs to the Warrior.

**Theme Alignment:**
- "Grim Survival": Recovering forbidden/lost knowledge from dangerous beasts fits the post-Sundering world perfectly.

**Integration Notes:**
- **CombatEngine/Items:** Requires updates to `ConsumableManager` to handle skill unlocks and `CombatEngine` to support the new conditional passives.
- **Economy:** Must ensure these books are either untradeable or heavily weighted so as not to break zone EV.

**Deliverable:**
Detailed Design Document: `.Jules/architect_designs/expansion_skill_books.md`

## 2026-03-12 — Expansion Blueprint: Auto-Adventure Overhaul (Skill Tree Integrations)

**Design Choice:**
Skill Tree Blueprints for the auto-adventure overhaul.

**Reasoning:**
- **Foreman Assignment:** Created skill tree blueprints for the auto-adventure overhaul to ensure class abilities work in time-based expeditions.
- **System Parity:** The deterministic combat formula currently lacks nuance for many class skills, especially utility or AoE effects.

**Key Mechanics:**
- **Translation:** Turn-based mechanics are translated into time-saving (AoE) or damage-reducing (Stun/Shields) passives for the background simulation.
- **New Archetypes:** Designed the Paladin (Cleric), Elementalist (Mage), and Beastmaster (Ranger) paths to flesh out the missing archetypes and provide concrete examples of the new deterministic scaling.

**Integration Notes:**
- **CombatEngine:** `AutoCombatFormula.resolve_clash` needs hooks for `aura_of_vitality` (healing between encounters) and `meteor_swarm` (reducing encounter time).

**Deliverable:**
Detailed Design Document: `.Jules/architect_designs/expansion_auto_adventure_overhaul.md`

## 2026-03-13 — Class Expansion Blueprint: Necromancer

**Design Choice:**
New Class Design: The Necromancer.

**Reasoning:**
- **Foreman Assignment:** While not explicitly assigned in `.Jules/foreman_plan.md` right now, designing new classes for major expansions was a listed favorite activity. I've designed this new class as a unique magical alternative to the Mage and Cleric.
- **Identity:** Introduces a summoner/attrition playstyle to the game. Focuses on manipulating life force and utilizing dead enemies.
- **Theme:** Directly supports the "Grim Survival" pillar—viewing death not as an end, but as a resource.

**Key Mechanics:**
- **Summons:** Added mechanics for raising temporary minions (`skeleton`, `undead_horde`) to absorb hits.
- **Corpse Utilization:** Introduced `requires_corpse` mechanic for AoE damage (Corpse Explosion).
- **Sustain:** Blends self-healing (`kill_heal_percent`) and MP regeneration on kill.

**Integration Notes:**
- **Tactician:** Needs to update `CombatEngine` to support allied summoned entities, track `dead_enemies_count` for corpse-based skills, and add hooks for passive debuffs/on-kill effects.
- **GameForge:** Requires adding Class ID 7, 7 new skills, a new "scythe" weapon type, and "Grave Dust" consumables.
- **Auto-Adventure Translation:** Summons should translate into flat HP buffers in the deterministic formula.

**Deliverable:**
Detailed Design Document: `.Jules/architect_designs/class_necromancer.md`

## 2026-03-15 — Expansion Blueprint: Companion System

**Design Choice:**
Major Content Expansion: Companion System (Taming and Upkeep).

**Reasoning:**
- **Economy:** We need more permanent sinks for low-tier materials (`feral_meat`, `wild_herbs`) to keep them relevant in the late game. A constant "Beast Feed" requirement solves this.
- **Engagement:** Fulfills the "Taming" archetype that players often request in RPGs, but adapted for Eldoria's grim setting.
- **Auto-Adventure Integration:** Fits perfectly into the new time-based auto-adventures, where a companion can act as a stat block modifier (e.g., Scout lowers encounter rate).

**Theme Alignment:**
- "Grim Survival": Companions are not pets; they are tools of survival. If you don't feed them, they turn on you or leave. The taming process requires weakening a beast, emphasizing dominance rather than friendship.

**Integration Notes:**
- **Database:** Requires a `player_companions` collection.
- **CombatEngine/Auto-Adventure:** Companions need to be integrated into `CombatEngine` to absorb hits or deal extra damage, and into `AutoCombatFormula` to affect session outcomes.
- **Economy:** GameBalancer must tune the upkeep costs so it's a persistent drain but not debilitating.

**Deliverable:**
Detailed Design Document: `.Jules/architect_designs/expansion_companion_system.md`
