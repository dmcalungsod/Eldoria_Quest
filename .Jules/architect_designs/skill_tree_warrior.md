# Class Expansion: Warrior Skill Tree

## 🛡️ Concept
To transform the Warrior from a simple "hit and get hit" class into a nuanced fighter with two distinct playstyles:
1.  **The Juggernaut (Tank):** Focuses on damage mitigation, crowd control, and protecting allies (or self-sustain).
2.  **The Berserker (DPS):** Focuses on high risk/high reward, trading health for damage, and overwhelming offense.

## 📜 Lore (for StoryWeaver)
"Some warriors survive by becoming the mountain—immovable, unyielding. Others survive by becoming the avalanche—unstoppable, destructive. The path you choose defines not just how you fight, but how you die."
— *General Kaelen, The Iron Wall*

## ⚔️ Skill Tree Expansion

### Tier 1 (Rank F) - Foundations
**1. Shield Bash (Active) - Juggernaut Path**
*Description:* Slams the enemy with a shield, dealing minor damage with a chance to stun.
*Mechanics:* Low damage, 30% chance to stun target for 1 turn.
```python
"shield_bash": {
    "key_id": "shield_bash",
    "name": "Shield Bash",
    "description": "A concussive blow that may stun the enemy.",
    "type": "Active",
    "class_id": 1,
    "mp_cost": 8,
    "power_multiplier": 0.8,
    "status_effect": {"stun_chance": 0.3},
    "learn_cost": 500,
    "upgrade_cost": 150,
    "scaling_stat": "STR",
    "scaling_factor": 2.0,
}
```

**2. Reckless Swing (Active) - Berserker Path**
*Description:* A wild, powerful strike that leaves the user open to attack.
*Mechanics:* High damage (1.8x), but user takes 10% of damage dealt as recoil.
```python
"reckless_swing": {
    "key_id": "reckless_swing",
    "name": "Reckless Swing",
    "description": "Sacrifice safety for power. Deals massive damage but hurts the user.",
    "type": "Active",
    "class_id": 1,
    "mp_cost": 10,
    "power_multiplier": 1.8,
    "self_damage_percent": 0.1, # New mechanic for Tactician
    "learn_cost": 500,
    "upgrade_cost": 150,
    "scaling_stat": "STR",
    "scaling_factor": 3.0,
}
```

### Tier 2 (Rank D) - Specialization
**3. Iron Skin (Passive) - Juggernaut Path**
*Description:* Years of combat have hardened your flesh.
*Mechanics:* Increases physical defense (END) by 10%.
```python
"iron_skin": {
    "key_id": "iron_skin",
    "name": "Iron Skin",
    "description": "Increases Endurance by 10%.",
    "type": "Passive",
    "class_id": 1,
    "passive_bonus": {"END_percent": 0.1},
    "learn_cost": 1500,
    "scaling_stat": "END",
    "scaling_factor": 1.0,
}
```

**4. Bloodlust (Passive) - Berserker Path**
*Description:* The thrill of battle fuels you.
*Mechanics:* Recover 5% Max HP whenever you kill an enemy.
```python
"bloodlust": {
    "key_id": "bloodlust",
    "name": "Bloodlust",
    "description": "Heal 5% HP on enemy kill.",
    "type": "Passive",
    "class_id": 1,
    "passive_bonus": {"kill_heal_percent": 0.05}, # New mechanic for CombatEngine
    "learn_cost": 1500,
    "scaling_stat": "STR",
    "scaling_factor": 1.0,
}
```

### Tier 3 (Rank C) - Mastery
**5. Taunt (Active) - Juggernaut Path**
*Description:* Challenges the enemy, forcing their attention and lowering their attack.
*Mechanics:* Debuffs enemy ATK by 20% for 3 turns.
```python
"taunt": {
    "key_id": "taunt",
    "name": "Taunt",
    "description": "Intimidate foes, reducing their attack power.",
    "type": "Active",
    "class_id": 1,
    "mp_cost": 12,
    "debuff": {"ATK_percent": -0.2, "duration": 3},
    "learn_cost": 3000,
    "scaling_stat": "END",
    "scaling_factor": 1.5,
}
```

**6. Whirlwind (Active) - Berserker Path**
*Description:* Spin with your weapon, striking all nearby enemies.
*Mechanics:* AoE damage (1.2x) to all foes.
```python
"whirlwind": {
    "key_id": "whirlwind",
    "name": "Whirlwind",
    "description": "A spinning attack that hits all enemies.",
    "type": "Active",
    "class_id": 1,
    "mp_cost": 20,
    "power_multiplier": 1.2,
    "is_aoe": True,
    "learn_cost": 3000,
    "scaling_stat": "STR",
    "scaling_factor": 2.5,
}
```

### Ultimate (Rank A) - Legend
**7. Unstoppable Force (Active)**
*Description:* Channel pure rage to become immune to pain.
*Mechanics:* Grants "Unstoppable" buff: +50% ATK, +50% DEF, Immune to Stun for 3 turns. Costs 50 MP.
```python
"unstoppable_force": {
    "key_id": "unstoppable_force",
    "name": "Unstoppable Force",
    "description": "Become a juggernaut of destruction for a short time.",
    "type": "Active",
    "class_id": 1,
    "mp_cost": 50,
    "buff": {
        "ATK_percent": 0.5,
        "DEF_percent": 0.5,
        "status_immunity": ["stun", "slow"],
        "duration": 3
    },
    "learn_cost": 10000,
    "scaling_stat": "STR",
    "scaling_factor": 1.0,
}
```

## 🔗 Integration Notes

### 🛠️ For GameForge
1.  **Update `skills_data.py`**: Add all 7 new skills with the definitions above.
2.  **Validation**: Ensure `class_id: 1` matches Warrior.

### 🧠 For Tactician
1.  **Implement `self_damage_percent`**: In `CombatEngine.execute_skill`, add logic to deduct HP from user if this key exists.
2.  **Implement `kill_heal_percent`**: In `CombatEngine.on_kill`, check for this passive and apply healing.
3.  **Implement `status_immunity`**: In `CombatEngine.apply_status`, check if target has immunity buff.

### 📚 For ChronicleKeeper
1.  **Title:** "Ironclad" - Unlock all Juggernaut path skills.
2.  **Title:** "Ravager" - Unlock all Berserker path skills.
3.  **Achievement:** "Unstoppable" - Use the Ultimate skill for the first time.
