# Class Expansion: Ranger Skill Tree

## 🏹 Concept
To evolve the Ranger from a simple ranged attacker into a versatile survivalist with two distinct playstyles:
1.  **The Deadeye (Sniper):** Focuses on precision, critical hits, and overwhelming single-target damage from afar.
2.  **The Warden (Trapper/Survival):** Focuses on battlefield control, traps, self-sustain, and environmental adaptability.

## 📜 Lore (for StoryWeaver)
"The wild does not forgive mistakes. Neither do I. One shot to end it, or a thousand cuts to bleed them dry—the choice is yours, but the result is always the same."
— *Kaela, First Ranger of the Grey Ward*

## 🌲 Skill Tree Expansion

### Tier 1 (Rank F) - Foundations
**1. True Shot (Active) - Deadeye Path**
*Description:* A focused arrow shot that pierces vital points.
*Mechanics:* High single-target damage with a bonus to accuracy/hit rate.
```python
"true_shot": {
    "key_id": "true_shot",
    "name": "True Shot",
    "description": "A focused arrow shot that never misses its mark.",
    "type": "Active",
    "class_id": 5,
    "mp_cost": 8,
    "power_multiplier": 1.4,
    "learn_cost": 0,  # Default skill
    "upgrade_cost": 200,
    "scaling_stat": "DEX",
    "scaling_factor": 2.6,
}
```

**2. Snare Trap (Active) - Warden Path**
*Description:* Deploys a hidden trap that snaps shut on the first enemy to approach.
*Mechanics:* Deals minor damage and applies a "Slow" or "Root" effect (reducing enemy Turn Speed or Evasion).
```python
"snare_trap": {
    "key_id": "snare_trap",
    "name": "Snare Trap",
    "description": "Deploys a trap that cripples enemy movement.",
    "type": "Active",
    "class_id": 5,
    "mp_cost": 10,
    "power_multiplier": 0.5,
    "status_effect": {"slow": 0.3, "duration": 2}, # Reduces enemy speed/evasion by 30%
    "learn_cost": 500,
    "upgrade_cost": 150,
    "scaling_stat": "DEX",
    "scaling_factor": 1.5,
}
```

### Tier 2 (Rank D) - Specialization
**3. Eagle Eye (Passive) - Deadeye Path**
*Description:* Your vision is honed to spot the slightest weakness in armor.
*Mechanics:* Increases Critical Hit Chance by 10%.
```python
"eagle_eye": {
    "key_id": "eagle_eye",
    "name": "Eagle Eye",
    "description": "Increases Critical Hit Chance by 10%.",
    "type": "Passive",
    "class_id": 5,
    "passive_bonus": {"crit_chance": 0.1},
    "learn_cost": 1500,
    "scaling_stat": "DEX",
    "scaling_factor": 1.0,
}
```

**4. Survivalist (Passive) - Warden Path**
*Description:* Living off the land has toughened your body and sharpened your instincts.
*Mechanics:* Increases Endurance and Agility.
```python
"survivalist": {
    "key_id": "survivalist",
    "name": "Survivalist",
    "description": "Your knowledge of the wild hardens your resolve.",
    "type": "Passive",
    "class_id": 5,
    "passive_bonus": {"END_percent": 0.1, "AGI_percent": 0.05},
    "learn_cost": 1500,
    "upgrade_cost": 250,
    "scaling_stat": "END",
    "scaling_factor": 1.0,
}
```

### Tier 3 (Rank C) - Mastery
**5. Piercing Shot (Active) - Deadeye Path**
*Description:* A powerful shot charged with enough force to punch through plate armor.
*Mechanics:* Deals damage that ignores a percentage of the target's Defense.
```python
"piercing_shot": {
    "key_id": "piercing_shot",
    "name": "Piercing Shot",
    "description": "A powerful shot that ignores 30% of enemy defense.",
    "type": "Active",
    "class_id": 5,
    "mp_cost": 15,
    "power_multiplier": 1.6,
    "ignore_defense_percent": 0.3, # New mechanic for Tactician
    "learn_cost": 3000,
    "upgrade_cost": 400,
    "scaling_stat": "DEX",
    "scaling_factor": 2.8,
}
```

**6. Mending Poultice (Active) - Warden Path**
*Description:* Quickly apply a herbal remedy to staunch bleeding and neutralize toxins.
*Mechanics:* Heals the user and removes negative status effects (Bleed, Poison).
```python
"mending_poultice": {
    "key_id": "mending_poultice",
    "name": "Mending Poultice",
    "description": "Heals wounds and cures poison or bleeding.",
    "type": "Active",
    "class_id": 5,
    "mp_cost": 12,
    "heal_power": 30,
    "cure_status": ["poison", "bleed"], # New mechanic for Tactician
    "learn_cost": 3000,
    "upgrade_cost": 350,
    "scaling_stat": "MAG", # Herbal knowledge (Intelligence/Magic)
    "scaling_factor": 1.5,
}
```

### Ultimate (Rank A) - Legend
**7. Apex Predator (Active)**
*Description:* Enter a state of primal focus, moving with unnatural speed and striking with lethal precision.
*Mechanics:* Grants "Apex" buff: +30% DEX, +30% AGI, +20% Crit Chance for 3 turns.
```python
"apex_predator": {
    "key_id": "apex_predator",
    "name": "Apex Predator",
    "description": "Unleash your primal instincts to dominate the battlefield.",
    "type": "Active",
    "class_id": 5,
    "mp_cost": 40,
    "buff": {
        "DEX_percent": 0.3,
        "AGI_percent": 0.3,
        "crit_chance": 0.2,
        "duration": 3
    },
    "learn_cost": 10000,
    "upgrade_cost": 800,
    "scaling_stat": "DEX",
    "scaling_factor": 1.0,
}
```

## 🔗 Integration Notes

### 🛠️ For GameForge
1.  **Update `skills_data.py`**: Add/Update these 7 skills for Class ID 5 (Ranger).
    - Note: `true_shot` and `survivalist` already exist; verify values match this design.
2.  **Validation**: Ensure no ID conflicts with other class skills.

### 🧠 For Tactician
1.  **Implement `ignore_defense_percent`**: In `CombatEngine.calculate_damage`, reduce target DEF by this percentage before calculation.
2.  **Implement `cure_status`**: In `CombatEngine.execute_skill` (Heal logic), remove specified status effects from the target.
3.  **Implement `slow` status**: Ensure `CombatEngine` handles Turn Order/Speed reduction if `AGI` is debuffed.

### 📚 For ChronicleKeeper
1.  **Title:** "Deadeye" - Unlock all Deadeye path skills (True Shot, Eagle Eye, Piercing Shot).
2.  **Title:** "Warden" - Unlock all Warden path skills (Snare Trap, Survivalist, Mending Poultice).
3.  **Achievement:** "One Shot, One Kill" - Deal over 500 damage in a single hit with a Ranger skill.
