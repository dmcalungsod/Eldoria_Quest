# Expansion Blueprint: Auto-Adventure Overhaul (Skill Tree Integrations)

## 📖 Concept
As the game transitions to a time-based auto-adventure system, existing classes need their abilities adapted or expanded to function within this new paradigm. This blueprint details how class skills translate into the deterministic combat formula and what new skills should be added to round out class identities.

## 🎯 Design Goals
1. Ensure all classes have distinct advantages in the auto-adventure system.
2. Translate turn-based mechanics (like Stun or Evasion) into time-saving or damage-reducing passives for auto-combat.
3. Provide missing subclasses/paths for existing base classes.

## ⚔️ Skill Tree Blueprints

### 1. The Paladin (Cleric Path)
- **Concept:** A heavy-armored healer who focuses on flat damage reduction and sustained healing over long expeditions.
- **Auto-Adventure Translation:**
  - `divine_shield`: Translated to a 10% reduction in `base_monster_damage` per combat iteration.
  - `aura_of_vitality`: Replaces the need for frequent resting by recovering 2% of Max HP between combat encounters during the background simulation.

### 2. The Elementalist (Mage Path)
- **Concept:** A raw damage dealer focusing on AoE to clear out "swarm" type enemies faster.
- **Auto-Adventure Translation:**
  - `meteor_swarm`: When calculating encounter duration, Elementalist's high AoE potential reduces the "time to kill" for non-elite encounters by 15%, allowing more encounters per hour.
  - `mana_shield`: Acts as a secondary HP bar in the deterministic formula.

### 3. The Beastmaster (Ranger Path)
- **Concept:** A ranged fighter who brings a companion into battle to split aggro.
- **Auto-Adventure Translation:**
  - `summon_companion`: Adds a flat +20% to the player's total HP pool during the deterministic clash calculation, simulating the companion taking hits.
  - `pack_tactics`: Increases total damage output by 10% when fighting single targets (bosses).

## 🔗 Integration Notes
- **Foreman Assignment:** These skill tree blueprints are specifically designed for the auto-adventure overhaul, ensuring that class abilities work in time-based expeditions.
- **Tactician:** Update `AutoCombatFormula.resolve_clash` to check for these new mechanics (`aura_of_vitality`, `meteor_swarm` time reduction, etc.).
- **GameForge:** Add the new paths to `classes.json` and the specific skills to `skills_data.py`.
