"""
monster_skills.py

Definitions for monster-specific skills.
Used to populate monster data in game_systems/data/monsters.py.
"""

MONSTER_SKILLS = {
    # Physical Attacks
    "heavy_blow": {
        "key_id": "heavy_blow",
        "name": "Heavy Blow",
        "power": 1.5,
        "mp_cost": 5,
        "type": "physical",
        "desc_key": "special_hit"
    },
    "rapid_strike": {
        "key_id": "rapid_strike",
        "name": "Rapid Strike",
        "power": 1.2,
        "mp_cost": 3,
        "type": "physical",
        "desc_key": "special_hit"
    },
    "crushing_slam": {
        "key_id": "crushing_slam",
        "name": "Crushing Slam",
        "power": 1.8,
        "mp_cost": 8,
        "type": "physical",
        "desc_key": "special_hit"
    },
    "vicious_bite": {
        "key_id": "vicious_bite",
        "name": "Vicious Bite",
        "power": 1.3,
        "mp_cost": 4,
        "type": "physical",
        "desc_key": "bite"
    },
    "crystal_shard": {
        "key_id": "crystal_shard",
        "name": "Crystal Shard",
        "power": 1.4,
        "mp_cost": 6,
        "type": "physical",
        "desc_key": "special_hit"
    },

    # Magical / Elemental
    "prism_beam": {
        "key_id": "prism_beam",
        "name": "Prism Beam",
        "power": 1.8,
        "mp_cost": 12,
        "type": "magical",
        "desc_key": "magic"
    },
    "ember": {
        "key_id": "ember",
        "name": "Ember",
        "power": 1.4,
        "mp_cost": 5,
        "type": "magical",
        "desc_key": "fire"
    },
    "flame_breath": {
        "key_id": "flame_breath",
        "name": "Flame Breath",
        "power": 1.7,
        "mp_cost": 10,
        "type": "magical",
        "desc_key": "fire"
    },
    "poison_spit": {
        "key_id": "poison_spit",
        "name": "Poison Spit",
        "power": 1.1,
        "mp_cost": 5,
        "type": "physical",
        "desc_key": "poison"
    },

    # Healing
    "mend": {
        "key_id": "mend",
        "name": "Mend",
        "heal_power": 30,  # Flat heal, can be scaled in DamageFormula if needed
        "mp_cost": 8,
        "type": "heal",
        "desc_key": "heal"
    },
    "regenerate": {
        "key_id": "regenerate",
        "name": "Regenerate",
        "heal_power": 60,
        "mp_cost": 15,
        "type": "heal",
        "desc_key": "heal"
    }
}
