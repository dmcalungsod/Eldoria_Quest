# Major Content Expansion: Companion System Blueprint

## Concept
A robust Companion System that allows players to tame, train, and utilize creatures encountered in the wild. Companions provide passive bonuses during exploration, active support in combat, and introduce a new layer of resource management (Companion Food/Upkeep).

## Narrative Hook (for StoryWeaver)
The Sundering didn't just break the land; it shattered the natural order. Some beasts have grown too feral to control, but others—scarred and desperate—seek alliance with those strong enough to survive. Taming is not about subjugation; it is a brutal pact of mutual survival in Eldoria's unforgiving wastes.

## Core Mechanics
- **Taming:** Players can attempt to tame weakened monsters (e.g., under 20% HP) using specific tools (e.g., "Tethering Rope", "Lure"). Success depends on the player's level vs. the monster's rank and the specific lure used.
- **Companion Slots:** Players start with 1 active companion slot and can unlock a second via high-rank progression or Guild Halls upgrades.
- **Roles:** Companions are categorized into roles:
  - *Vanguard (Tank):* Generates aggro, absorbs hits (e.g., Rock-Shell Tortoise).
  - *Striker (DPS):* Adds raw damage to combat turns (e.g., Frostfang Wolf).
  - *Scout (Utility):* Increases item discovery rate and lowers encounter frequency during auto-adventures (e.g., Ember Hawk).
- **Upkeep (The Survival Element):** Companions consume "Rations" or specific "Beast Feed." If a companion is unfed, its bonuses are disabled, and it may eventually abandon the player. This introduces a persistent material sink.

## Required Assets & Task Allocation

### Phase 1: Foundation (Database & Engine)
- **DataSteward / SystemSmith:**
  - Create a new `player_companions` collection/schema in the database to store tamed beasts (ID, species, level, bond level, current_hp).
  - Add logic to handle Companion Upkeep in `AdventureSession` (deducting feed per step).
- **Tactician:**
  - Update `CombatEngine.run_combat_turn` to handle companion actions (dealing damage or absorbing hits).
  - Update `AutoCombatFormula.resolve_clash` to translate companion roles into deterministic auto-adventure bonuses (e.g., Striker adds to `player_net_dps`).

### Phase 2: Content Generation
- **GameForge:**
  - Create the first batch of tamable beasts in a new data file (`game_systems/data/companions.json` or similar) based on existing low-mid tier monsters.
  - Implement the "Taming Lure" and "Beast Feed" items in `consumables.json`.
- **Equipper:**
  - Design companion-specific gear (e.g., Spiked Collars, Reinforced Barding) that players can craft to boost their companion's stats.
- **GameBalancer:**
  - Balance the Taming success rate formula.
  - Tune the economy impact of "Beast Feed" to ensure it drains excess low-tier materials without bankrupting new players.

### Phase 3: Polish & Integration
- **StoryWeaver:**
  - Write flavor text for taming successes/failures and companion actions in combat.
- **Palette:**
  - Design a new UI View ("Companion Management") following the One UI Policy to feed, equip, and swap active companions.
- **ChronicleKeeper:**
  - Add achievements for taming first beast, maxing bond level, and taming specific rare boss-tier creatures.
- **Grimwarden:**
  - Review mechanics to ensure the "Taming" feels earned and dangerous, maintaining the dark fantasy atmosphere (no "cute pets").

## Integration Points
- **Auto-Adventures:** Companions directly modify the duration/success of auto-adventures. A Scout companion makes expeditions safer.
- **Guild Halls:** Guild Halls can be upgraded with a "Menagerie" or "Beast Pens" to store additional inactive companions.
- **Economy:** Constant need for "Beast Feed" adds a permanent sink for common materials (e.g., `feral_meat`).

## Success Criteria
- Players actively seek out and utilize companions.
- The economy shows a healthy, consistent drain on low-tier "meat/plant" materials due to upkeep.
- Auto-adventure win rates and session lengths reflect the intended impact of companion roles.
- Combat logs correctly display companion interventions without breaking existing turn logic.
