# Class Expansion: Mage Skill Tree

## 🔮 Concept
To elevate the Mage from a simple spell-slinger into a master of the arcane arts with two distinct playstyles:
1.  **The Elementalist (DPS/AoE):** Focuses on mastering the raw destructive forces of nature (Fire, Ice, Lightning) to obliterate groups of enemies and exploit elemental weaknesses.
2.  **The Arcanist (Utility/Control):** Focuses on manipulating the Veil itself, bending time, space, and magical energy to control the battlefield, protect allies, and sustain their own power.

## 📜 Lore (for StoryWeaver)
"Magic is not a gift; it is a discipline. The careless are consumed by the very flames they conjure. True mastery lies not just in power, but in precision and understanding the intricate weave of the Veil."
— *Archmage Vaelen, The Cobalt Spire*

## ✨ Skill Tree Expansion

### Tier 1 (Rank F) - Foundations
**1. Ignite (Active) - Elementalist Path**
*Description:* A concentrated burst of fire that leaves the enemy burning.
*Mechanics:* Deals moderate damage and applies a "Burn" effect (DoT).
```python
"ignite": {
    "key_id": "ignite",
    "name": "Ignite",
    "description": "Sets the target ablaze, causing damage over time.",
    "type": "Active",
    "class_id": 2,
    "mp_cost": 8,
    "power_multiplier": 1.0,
    "status_effect": {"burn": 5, "duration": 3},
    "learn_cost": 500,
    "upgrade_cost": 150,
    "scaling_stat": "MAG",
    "scaling_factor": 2.5,
}
```

**2. Arcane Focus (Passive) - Arcanist Path**
*Description:* Deep meditation allows you to draw more power from the Veil.
*Mechanics:* Increases Max MP by 15%.
```python
"arcane_focus": {
    "key_id": "arcane_focus",
    "name": "Arcane Focus",
    "description": "Increases Max MP by 15%.",
    "type": "Passive",
    "class_id": 2,
    "passive_bonus": {"MP_percent": 0.15},
    "learn_cost": 500,
    "scaling_stat": "MAG",
    "scaling_factor": 1.0,
}
```

### Tier 2 (Rank D) - Specialization
**3. Chain Lightning (Active) - Elementalist Path**
*Description:* Unleashes a bolt of lightning that arcs between multiple enemies.
*Mechanics:* AoE damage that hits all enemies with a chance to Paralyze.
```python
"chain_lightning": {
    "key_id": "chain_lightning",
    "name": "Chain Lightning",
    "description": "Lightning arcs across all foes, potentially paralyzing them.",
    "type": "Active",
    "class_id": 2,
    "mp_cost": 18,
    "power_multiplier": 1.1,
    "is_aoe": True,
    "status_effect": {"paralyze_chance": 0.25},
    "learn_cost": 1500,
    "upgrade_cost": 300,
    "scaling_stat": "MAG",
    "scaling_factor": 2.2,
}
```

**4. Chrono Shift (Active) - Arcanist Path**
*Description:* Briefly warp time to hasten yourself or an ally.
*Mechanics:* Grants a temporary boost to Agility and reduces cooldowns.
```python
"chrono_shift": {
    "key_id": "chrono_shift",
    "name": "Chrono Shift",
    "description": "Warps time to significantly boost speed.",
    "type": "Active",
    "class_id": 2,
    "mp_cost": 20,
    "buff": {
        "AGI_percent": 0.3,
        "duration": 3
    },
    "learn_cost": 1500,
    "upgrade_cost": 300,
    "scaling_stat": "MAG",
    "scaling_factor": 1.5,
}
```

### Tier 3 (Rank C) - Mastery
**5. Blizzard (Active) - Elementalist Path**
*Description:* Summons a localized freezing storm to devastate the battlefield.
*Mechanics:* High AoE damage that reduces enemy Agility.
```python
"blizzard": {
    "key_id": "blizzard",
    "name": "Blizzard",
    "description": "A freezing storm that damages and slows all enemies.",
    "type": "Active",
    "class_id": 2,
    "mp_cost": 25,
    "power_multiplier": 1.5,
    "is_aoe": True,
    "debuff": {"AGI_percent": -0.2, "duration": 2},
    "learn_cost": 3000,
    "upgrade_cost": 450,
    "scaling_stat": "MAG",
    "scaling_factor": 2.8,
}
```

**6. Mana Syphon (Passive) - Arcanist Path**
*Description:* Your spells are so efficient that they draw residual magic from enemies.
*Mechanics:* Recover 5% Max MP whenever you kill an enemy.
```python
"mana_syphon": {
    "key_id": "mana_syphon",
    "name": "Mana Syphon",
    "description": "Heal 5% MP on enemy kill.",
    "type": "Passive",
    "class_id": 2,
    "passive_bonus": {"kill_mana_heal_percent": 0.05}, # New mechanic for CombatEngine
    "learn_cost": 3000,
    "scaling_stat": "MAG",
    "scaling_factor": 1.0,
}
```

### Ultimate (Rank A) - Legend
**7. Meteor Swarm (Active)**
*Description:* Tear the sky open, calling down flaming meteors upon your foes.
*Mechanics:* Massive AoE damage with a high MP cost.
```python
"meteor_swarm": {
    "key_id": "meteor_swarm",
    "name": "Meteor Swarm",
    "description": "Calls down a devastating shower of meteors.",
    "type": "Active",
    "class_id": 2,
    "mp_cost": 60,
    "power_multiplier": 3.0,
    "is_aoe": True,
    "learn_cost": 10000,
    "upgrade_cost": 1000,
    "scaling_stat": "MAG",
    "scaling_factor": 3.5,
}
```

## 🔗 Integration Notes

### 🛠️ For GameForge
1.  **Update `skills_data.py`**: Add all 7 new skills with the definitions above. Replace `fireball`, `ice_lance`, `mana_shield` and `explosion` with these or integrate them as options.
2.  **Validation**: Ensure `class_id: 2` matches Mage.

### 🧠 For Tactician
1.  **Implement `kill_mana_heal_percent`**: In `CombatEngine.on_kill`, check for this passive and apply MP recovery.
2.  **Verify `is_aoe` scaling**: Ensure AoE spells properly calculate damage across multiple targets without crashing.

### 📚 For ChronicleKeeper
1.  **Title:** "Elementalist" - Unlock all Elementalist path skills.
2.  **Title:** "Arcanist" - Unlock all Arcanist path skills.
3.  **Achievement:** "Master of the Veil" - Deal over 10,000 damage in a single spell cast.