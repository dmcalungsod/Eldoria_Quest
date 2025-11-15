"""
skills_data.py

Contains all skill definitions for Eldoria Quest.
This data is imported by populate_database.py.
"""

SKILLS = {
    # Mage Skills
    "fireball": {
        "key_id": "fireball",
        "name": "Fireball",
        "description": "A basic incantation that hurls a sphere of fire.",
        "type": "Active",
        "class_id": 2,  # Mage
        "mp_cost": 5,
        "power_multiplier": 1.2,
    },
    "explosion": {
        "key_id": "explosion",
        "name": "Explosion",
        "description": "The ultimate offensive magic. Annihilates the target with a devastating blast.",
        "type": "Active",
        "class_id": 2,  # Mage
        "mp_cost": 25,
        "power_multiplier": 2.5,
    },
    # Warrior Skills
    "power_strike": {
        "key_id": "power_strike",
        "name": "Power Strike",
        "description": "A heavy, focused blow that aims to break an enemy's guard.",
        "type": "Active",
        "class_id": 1,  # Warrior
        "mp_cost": 5,
        "power_multiplier": 1.5,  # We'll make this STR-based in damage_formula
    },
    # Rogue Skills
    "stealth": {
        "key_id": "stealth",
        "name": "Stealth",
        "description": "Fade into the shadows, becoming harder to detect.",
        "type": "Passive",  # Passive for now, no MP cost
        "class_id": 3,  # Rogue
        "mp_cost": 0,
    },
    # Cleric Skills
    "heal": {
        "key_id": "heal",
        "name": "Heal",
        "description": "A gentle prayer that mends minor wounds.",
        "type": "Active",
        "class_id": 4,  # Cleric
        "mp_cost": 10,
        "heal_power": 30,  # Base heal
    },
    # Ranger Skills
    "true_shot": {
        "key_id": "true_shot",
        "name": "True Shot",
        "description": "A focused arrow shot that pierces vital points.",
        "type": "Active",
        "class_id": 5,  # Ranger
        "mp_cost": 8,
        "power_multiplier": 1.4,  # We'll make this DEX-based
    },
}
