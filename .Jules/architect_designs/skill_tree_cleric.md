# Class Expansion: Cleric Skill Tree

## ⛪ Concept
To evolve the Cleric from a generic healer into a survival-focused religious zealot with two distinct playstyles:
1.  **The Zealot (DPS/Debuffer):** Focuses on offensive magic, punishing enemies, and drawing strength from righteous fury.
2.  **The Penitent (Healer/Support):** Focuses on self-sacrifice to protect and heal others, utilizing powerful buffs and damage mitigation.

## 📜 Lore (for StoryWeaver)
"The gods of old are dead or sleeping, their temples reduced to ash and rubble. But faith? Faith remains. We do not pray for miracles; we forge them in the crucible of suffering. The Light is not a gentle warmth—it is a searing flame that burns away the corruption of the Veil."
— *High Inquisitor Thorne, The Ashen Order*

## 🕊️ Skill Tree Expansion

### Tier 1 (Rank F) - Foundations
**1. Smite (Active) - Zealot Path**
*Description:* Call down a searing ray of holy light to strike a foe.
*Mechanics:* High single-target damage that scales well with MAG.
```python
"smite": {
    "key_id": "smite",
    "name": "Smite",
    "description": "Call down holy energy to strike a foe. Scales with MAG.",
    "type": "Active",
    "class_id": 4,
    "mp_cost": 8,
    "power_multiplier": 1.7,
    "learn_cost": 0,  # Default skill
    "upgrade_cost": 250,
    "scaling_stat": "MAG",
    "scaling_factor": 2.8,
}
```

**2. Heal (Active) - Penitent Path**
*Description:* A gentle prayer that mends minor wounds and stabilizes the injured.
*Mechanics:* Single-target heal scaling with MAG.
```python
"heal": {
    "key_id": "heal",
    "name": "Heal",
    "description": "A gentle prayer that mends minor wounds.",
    "type": "Active",
    "class_id": 4,
    "mp_cost": 10,
    "heal_power": 45,
    "learn_cost": 0,  # Default skill
    "upgrade_cost": 200,
    "scaling_stat": "MAG",
    "scaling_factor": 1.5,
}
```

### Tier 2 (Rank D) - Specialization
**3. Condemnation (Active) - Zealot Path**
*Description:* Utter a holy word that cripples the enemy's will to fight.
*Mechanics:* Deals moderate damage and debuffs the target's Attack and Defense.
```python
"condemnation": {
    "key_id": "condemnation",
    "name": "Condemnation",
    "description": "A word of power that weakens the enemy's resolve and armor.",
    "type": "Active",
    "class_id": 4,
    "mp_cost": 15,
    "power_multiplier": 1.2,
    "debuff": {
        "ATK_percent": -0.15,
        "DEF_percent": -0.15,
        "duration": 3
    },
    "learn_cost": 1500,
    "upgrade_cost": 300,
    "scaling_stat": "MAG",
    "scaling_factor": 2.0,
}
```

**4. Martyr's Grace (Passive) - Penitent Path**
*Description:* Your selfless dedication grants you strength when you need it most to protect others.
*Mechanics:* Increases healing power significantly when your HP is low.
```python
"martyrs_grace": {
    "key_id": "martyrs_grace",
    "name": "Martyr's Grace",
    "description": "Healing skills are 50% more effective when you are below 30% HP.",
    "type": "Passive",
    "class_id": 4,
    "conditional_multiplier": {"condition": "hp_below_30", "heal_multiplier": 1.5}, # New mechanic for Tactician
    "learn_cost": 1500,
    "scaling_stat": "END",
    "scaling_factor": 1.0,
}
```

### Tier 3 (Rank C) - Mastery
**5. Purifying Flames (Active) - Zealot Path**
*Description:* Conjure a wave of holy fire that incinerates all enemies.
*Mechanics:* AoE damage that deals bonus damage to Undead or Void enemies (if tags exist, otherwise flat bonus).
```python
"purifying_flames": {
    "key_id": "purifying_flames",
    "name": "Purifying Flames",
    "description": "A wave of holy fire that scorches all enemies.",
    "type": "Active",
    "class_id": 4,
    "mp_cost": 25,
    "power_multiplier": 1.4,
    "is_aoe": True,
    "learn_cost": 3000,
    "upgrade_cost": 450,
    "scaling_stat": "MAG",
    "scaling_factor": 2.5,
}
```

**6. Sanctuary (Active) - Penitent Path**
*Description:* Bless the ground, creating a safe haven that protects allies and heals them over time.
*Mechanics:* Grants a massive defensive buff and applies a Regeneration effect.
```python
"sanctuary": {
    "key_id": "sanctuary",
    "name": "Sanctuary",
    "description": "Creates a protective ward granting Defense and Regeneration.",
    "type": "Active",
    "class_id": 4,
    "mp_cost": 30,
    "buff": {
        "DEF_percent": 0.4,
        "regen_percent": 0.05, # Heals 5% Max HP per turn
        "duration": 3
    },
    "learn_cost": 3000,
    "upgrade_cost": 400,
    "scaling_stat": "MAG",
    "scaling_factor": 1.0,
}
```

### Ultimate (Rank A) - Legend
**7. Divine Intervention (Active)**
*Description:* Beseech the heavens for a miracle. Resurrects fallen allies (if in party play) or fully restores HP and MP while granting temporary invulnerability.
*Mechanics:* Fully restores HP and MP, clears all debuffs, and grants "Invulnerable" status for 1 turn.
```python
"divine_intervention": {
    "key_id": "divine_intervention",
    "name": "Divine Intervention",
    "description": "A miraculous prayer that fully restores the caster and grants brief invulnerability.",
    "type": "Active",
    "class_id": 4,
    "mp_cost": 60,
    "heal_power": 9999,
    "mp_heal": 9999,
    "cure_status": ["all"], # Clears all negative status effects
    "buff": {
        "invulnerable": True, # New mechanic for Tactician
        "duration": 1
    },
    "learn_cost": 10000,
    "upgrade_cost": 1000,
    "scaling_stat": "MAG",
    "scaling_factor": 1.0,
}
```

## 🔗 Integration Notes

### 🛠️ For GameForge
1.  **Update `skills_data.py`**: Add `condemnation`, `martyrs_grace`, `purifying_flames`, `sanctuary`, and `divine_intervention`.
2.  **Verify Existing Skills**: Ensure `smite` and `heal` match these specs (update if necessary). Note: `blessing` from current game can be kept as a general Cleric skill or retired in favor of the specialized paths.

### 🧠 For Tactician
1.  **Implement `conditional_multiplier` for healing**: In `CombatEngine.execute_skill`, if the skill is a heal and the caster's HP is below 30%, apply the `heal_multiplier`.
2.  **Implement `regen_percent`**: In `CombatEngine` turn logic, if an entity has a buff with `regen_percent`, heal them by that percentage of their Max HP at the start or end of their turn.
3.  **Implement `cure_status: ["all"]`**: Ensure the logic can clear all negative status effects and debuffs from the target.
4.  **Implement `invulnerable`**: In `CombatEngine.calculate_damage` or `apply_damage`, if the target has an `invulnerable` buff, reduce incoming damage to 0 and prevent new debuffs/status effects.

### 📚 For ChronicleKeeper
1.  **Title:** "Zealot" - Unlock all Zealot path skills.
2.  **Title:** "Penitent" - Unlock all Penitent path skills.
3.  **Achievement:** "Miracle Worker" - Use Divine Intervention when below 10% HP.
