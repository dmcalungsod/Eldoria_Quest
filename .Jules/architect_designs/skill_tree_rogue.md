# Class Expansion: Rogue Skill Tree

## 🗡️ Concept
To refine the Rogue from a generic thief into a master of lethal precision and elusive movement, offering two distinct playstyles:
1.  **The Assassin (DPS/DoT):** Focuses on maximizing damage output through critical hits, poisons, and capitalizing on weakened foes.
2.  **The Phantom (Evasion/Utility):** Focuses on survival through avoidance, misdirection, and crowd control.

## 📜 Lore (for StoryWeaver)
"To be seen is to fail. To be heard is to die. The true masters of the blade are not those who swing the hardest, but those who strike before the enemy even knows they are there."
— *Sylas, The Shadow of the Spire*

## 🌑 Skill Tree Expansion

### Tier 1 (Rank F) - Foundations
**1. Double Strike (Active) - Assassin Path**
*Description:* A rapid two-hit attack that overwhelms the enemy with speed.
*Mechanics:* Deals two instances of damage, each scaling with DEX.
```python
"double_strike": {
    "key_id": "double_strike",
    "name": "Double Strike",
    "description": "A rapid two-hit attack that scales with DEX.",
    "type": "Active",
    "class_id": 3,
    "mp_cost": 10,
    "power_multiplier": 1.8,
    "learn_cost": 2500,
    "upgrade_cost": 350,
    "scaling_stat": "DEX",
    "scaling_factor": 2.6,
}
```

**2. Stealth (Passive) - Phantom Path**
*Description:* Fade into the shadows, becoming harder to detect and harder to hit.
*Mechanics:* Increases Agility (Evasion) permanently.
```python
"stealth": {
    "key_id": "stealth",
    "name": "Stealth",
    "description": "Fade into the shadows, becoming harder to detect.",
    "type": "Passive",
    "class_id": 3,
    "mp_cost": 0,
    "passive_bonus": {"AGI_percent": 0.1},
    "learn_cost": 0,
    "upgrade_cost": 500,
    "scaling_stat": "AGI",
    "scaling_factor": 1.0,
}
```

### Tier 2 (Rank D) - Specialization
**3. Toxic Blade (Active) - Assassin Path**
*Description:* Coats the weapon in a potent neurotoxin before striking.
*Mechanics:* Deals minor damage but inflicts a strong Poison effect.
```python
"toxic_blade": {
    "key_id": "toxic_blade",
    "name": "Toxic Blade",
    "description": "A weak strike that applies a potent poison.",
    "type": "Active",
    "class_id": 3,
    "mp_cost": 12,
    "power_multiplier": 0.8,
    "debuff": {"poison": 5, "duration": 3},
    "learn_cost": 2000,
    "upgrade_cost": 300,
    "scaling_stat": "DEX",
    "scaling_factor": 2.6,
}
```

**4. Shadow Step (Active) - Phantom Path**
*Description:* Move through the shadows to reappear behind the enemy.
*Mechanics:* Grants a temporary boost to Evasion and guarantees the next attack is a Critical Hit.
```python
"shadow_step": {
    "key_id": "shadow_step",
    "name": "Shadow Step",
    "description": "Dash through shadows to evade attacks and prepare a critical strike.",
    "type": "Active",
    "class_id": 3,
    "mp_cost": 15,
    "buff": {
        "AGI_percent": 0.5,
        "next_hit_crit": True, # New mechanic for Tactician
        "duration": 2
    },
    "learn_cost": 1500,
    "upgrade_cost": 300,
    "scaling_stat": "AGI",
    "scaling_factor": 1.5,
}
```

### Tier 3 (Rank C) - Mastery
**5. Venomous Strike (Active) - Assassin Path**
*Description:* Exploits the weakness of a poisoned foe to deliver a devastating blow.
*Mechanics:* Deals bonus damage if the target is already Poisoned.
```python
"venomous_strike": {
    "key_id": "venomous_strike",
    "name": "Venomous Strike",
    "description": "Deals massive damage to poisoned targets.",
    "type": "Active",
    "class_id": 3,
    "mp_cost": 20,
    "power_multiplier": 1.5,
    "conditional_multiplier": {"condition": "target_poisoned", "multiplier": 2.0}, # New mechanic for Tactician
    "learn_cost": 3000,
    "upgrade_cost": 450,
    "scaling_stat": "DEX",
    "scaling_factor": 2.8,
}
```

**6. Flash Powder (Active) - Phantom Path**
*Description:* Throw a pouch of blinding powder to disorient enemies.
*Mechanics:* AoE attack that deals no damage but has a high chance to Blind enemies (reducing their Accuracy).
```python
"flash_powder": {
    "key_id": "flash_powder",
    "name": "Flash Powder",
    "description": "Blinds all enemies, reducing their accuracy.",
    "type": "Active",
    "class_id": 3,
    "mp_cost": 18,
    "power_multiplier": 0.0,
    "is_aoe": True,
    "debuff": {"accuracy_percent": -0.4, "duration": 3}, # New mechanic for Tactician
    "learn_cost": 3000,
    "upgrade_cost": 400,
    "scaling_stat": "AGI",
    "scaling_factor": 2.0,
}
```

### Ultimate (Rank A) - Legend
**7. Death Blossom (Active)**
*Description:* Spin in a blur of blades, striking every enemy with lethal precision.
*Mechanics:* High damage AoE attack that applies Bleed to all targets.
```python
"death_blossom": {
    "key_id": "death_blossom",
    "name": "Death Blossom",
    "description": "Unleash a storm of blades, damaging and bleeding all foes.",
    "type": "Active",
    "class_id": 3,
    "mp_cost": 50,
    "power_multiplier": 2.5,
    "is_aoe": True,
    "status_effect": {"bleed": 10, "duration": 3},
    "learn_cost": 10000,
    "upgrade_cost": 1000,
    "scaling_stat": "DEX",
    "scaling_factor": 3.0,
}
```

## 🔗 Integration Notes

### 🛠️ For GameForge
1.  **Update `skills_data.py`**: Add `shadow_step`, `venomous_strike`, `flash_powder`, and `death_blossom`.
2.  **Verify Existing Skills**: Ensure `double_strike`, `stealth`, and `toxic_blade` match these specs (update if necessary).

### 🧠 For Tactician
1.  **Implement `next_hit_crit`**: In `CombatEngine`, if this flag is present in active buffs, force a critical hit on the next attack and consume the buff.
2.  **Implement `conditional_multiplier`**: In `CombatEngine.calculate_damage`, check for conditions (like `target_poisoned`) and apply the multiplier.
3.  **Implement `accuracy_percent`**: Ensure accuracy checks in `CombatEngine` respect this debuff.

### 📚 For ChronicleKeeper
1.  **Title:** "Assassin" - Unlock all Assassin path skills.
2.  **Title:** "Phantom" - Unlock all Phantom path skills.
3.  **Achievement:** "Unseen Death" - Win a battle without taking damage while using a Rogue class.
