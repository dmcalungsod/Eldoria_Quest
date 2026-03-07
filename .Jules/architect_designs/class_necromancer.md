# Class Design: Necromancer

## Concept
A dark spellcaster who manipulates life force and commands the dead. Unlike Mages who channel the Veil, Necromancers draw power from the remnants of the Sundering itself, viewing death not as an end, but as a resource. They are pragmatic, sinister, and focused on attrition and summoning.

## Lore (for StoryWeaver)
"The Sundering broke the world, and in its breaking, it left a stain. We do not fear the rot; we harvest it. When a body falls, its story is not over—it simply awaits new direction."
— *Malakor, First Voice of the Hollowed Choir*

Necromancers are often shunned or feared, operating on the fringes of the Grey Ward. They are scholars of the macabre, using forbidden rites to sustain themselves and overwhelm their enemies with numbers and decay.

## Base Stats (for GameBalancer)
- **STR:** 2 (Physically weak)
- **END:** 4 (Sustained by dark magic)
- **DEX:** 3 (Average agility)
- **AGI:** 3 (Average speed)
- **MAG:** 8 (High spellcasting power)
- **LCK:** 4 (A strange connection to fate)

**Total:** 24 (Matches other classes)

## Starting Equipment (for GameForge & Equipper)
- **Weapon:** Bone Wand (Low damage, boosts MAG)
- **Armor:** Tattered Robes (Light armor)
- **Misc:** Grave Dust x5 (Consumable, required for some summons)

## Allowed Slots
- **Weapons:** `staff`, `wand`, `tome`, `scythe` (New weapon type)
- **Armor:** `hood`, `robe`, `gloves`, `boots`, `legs` (Light Armor)
- **Misc:** `belt`, `accessory`

## Skill Tree: The Master of Bones Path

### Tier 1 (Rank F) - Foundations
**1. Life Drain (Active)**
*Description:* Siphons the life essence from the target, dealing damage and healing the caster.
*Mechanics:* Deals moderate magic damage; heals the caster for 50% of the damage dealt.
```python
"life_drain": {
    "key_id": "life_drain",
    "name": "Life Drain",
    "description": "Siphons life essence, dealing damage and healing the caster.",
    "type": "Active",
    "class_id": 7, # Assuming next available ID is 7
    "mp_cost": 10,
    "power_multiplier": 1.0,
    "kill_heal_percent": 0.5, # Reusing Lifesteal mechanic from Warrior
    "learn_cost": 0,
    "upgrade_cost": 200,
    "scaling_stat": "MAG",
    "scaling_factor": 1.5,
}
```

**2. Raise Skeleton (Active)**
*Description:* Animates a pile of bones to fight alongside you.
*Mechanics:* Summons a Skeleton minion that acts independently in combat, absorbing hits and dealing minor damage.
```python
"raise_skeleton": {
    "key_id": "raise_skeleton",
    "name": "Raise Skeleton",
    "description": "Summons a skeletal minion to absorb hits and attack.",
    "type": "Active",
    "class_id": 7,
    "mp_cost": 15,
    "summon": "skeleton", # Requires new 'summon' mechanic in Tactician
    "learn_cost": 500,
    "upgrade_cost": 300,
    "scaling_stat": "MAG",
    "scaling_factor": 1.0,
}
```

### Tier 2 (Rank D) - Specialization
**3. Corpse Explosion (Active)**
*Description:* Detonates the residual energy in a fallen enemy, damaging all remaining foes.
*Mechanics:* AoE damage that requires an enemy to have died in the current battle.
```python
"corpse_explosion": {
    "key_id": "corpse_explosion",
    "name": "Corpse Explosion",
    "description": "Detonates a fallen enemy, dealing massive AoE damage.",
    "type": "Active",
    "class_id": 7,
    "mp_cost": 20,
    "power_multiplier": 2.0,
    "requires_corpse": True, # New mechanic for Tactician
    "aoe": True,
    "learn_cost": 1500,
    "upgrade_cost": 500,
    "scaling_stat": "MAG",
    "scaling_factor": 2.0,
}
```

**4. Aura of Decay (Passive)**
*Description:* A sickening miasma surrounds you, weakening those who approach.
*Mechanics:* Reduces the END and STR of all enemies by 5% at the start of combat.
```python
"aura_of_decay": {
    "key_id": "aura_of_decay",
    "name": "Aura of Decay",
    "description": "Weakens the END and STR of all enemies by 5%.",
    "type": "Passive",
    "class_id": 7,
    "aura_debuff": {"END_percent": -0.05, "STR_percent": -0.05}, # New mechanic for Tactician
    "learn_cost": 1500,
    "scaling_stat": "MAG",
    "scaling_factor": 1.0,
}
```

### Tier 3 (Rank C) - Mastery
**5. Bone Spear (Active)**
*Description:* Conjures a jagged spear of bone that pierces through multiple enemies.
*Mechanics:* Deals high damage to a target and moderate damage to a secondary target (Cleave).
```python
"bone_spear": {
    "key_id": "bone_spear",
    "name": "Bone Spear",
    "description": "A jagged bone spear that strikes multiple targets.",
    "type": "Active",
    "class_id": 7,
    "mp_cost": 25,
    "power_multiplier": 1.8,
    "cleave": 0.5, # Deals 50% damage to an additional target
    "learn_cost": 3000,
    "upgrade_cost": 600,
    "scaling_stat": "MAG",
    "scaling_factor": 2.2,
}
```

**6. Soul Harvest (Passive)**
*Description:* You draw power from the dying breaths of your foes.
*Mechanics:* Restores MP whenever an enemy is defeated.
```python
"soul_harvest": {
    "key_id": "soul_harvest",
    "name": "Soul Harvest",
    "description": "Restores MP when an enemy is defeated.",
    "type": "Passive",
    "class_id": 7,
    "on_kill_effect": {"restore_mp": 10}, # New mechanic for Tactician
    "learn_cost": 3000,
    "scaling_stat": "MAG",
    "scaling_factor": 1.0,
}
```

### Ultimate (Rank A) - Legend
**7. Army of the Dead (Active)**
*Description:* Channels immense dark energy to summon a horde of restless spirits and skeletal warriors.
*Mechanics:* Summons multiple minions and applies a "Fear" debuff (reducing enemy damage output) to all enemies.
```python
"army_of_the_dead": {
    "key_id": "army_of_the_dead",
    "name": "Army of the Dead",
    "description": "Summons a horde of undead and terrifies enemies.",
    "type": "Active",
    "class_id": 7,
    "mp_cost": 60,
    "summon": "undead_horde",
    "status_effect": {"fear": 0.2, "duration": 3}, # Reduces enemy damage by 20%
    "aoe_status": True,
    "learn_cost": 10000,
    "upgrade_cost": 1000,
    "scaling_stat": "MAG",
    "scaling_factor": 3.0,
}
```

## Integration Notes

### 🛠️ For GameForge
1.  **Update `class_data.py`**: Add the Necromancer class definition (Class ID 7).
2.  **Update `skills_data.py`**: Add the 7 new Necromancer skills.
3.  **New Weapon Type**: Add "scythe" to allowed slots and create base scythe items in `equipments.json`.
4.  **Consumables**: Add "Grave Dust" to `consumables.json` as a drop from undead enemies.

### 🧠 For Tactician
1.  **Implement `summon` mechanic**: Update `CombatEngine` to handle allied summoned entities (adding them to the player's side of the battle, managing their HP/actions, and removing them after combat).
2.  **Implement `requires_corpse`**: Update `CombatEngine` to track `dead_enemies_count` and only allow `corpse_explosion` if `dead_enemies_count > 0`.
3.  **Implement `aura_debuff`**: Update combat initialization to apply passive debuffs to enemies before turn 1.
4.  **Implement `on_kill_effect`**: Add a hook in `CombatEngine._process_death` to trigger player passives like MP restoration.
5.  **Auto-Adventure Translation**: In `AutoCombatFormula.resolve_clash`, translate `summon` into a flat HP buffer (like Beastmaster) and `corpse_explosion` into an AoE damage multiplier against swarms.

### 📚 For ChronicleKeeper
1.  **Title:** "Gravewalker" - Unlock all Necromancer skills.
2.  **Achievement:** "One Foot in the Grave" - Defeat a boss while at less than 5% HP using a Necromancer skill.

### ⚖️ For GameBalancer
1.  Ensure the `kill_heal_percent` on `Life Drain` isn't overpowered in prolonged fights.
2.  Balance the stats and scaling of the `skeleton` and `undead_horde` summons to ensure they remain relevant at higher ranks but don't trivialize encounters.
