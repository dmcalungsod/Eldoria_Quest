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
    },
    "explosion": {
        "key_id": "explosion",
        "name": "Explosion",
        "description": "The ultimate offensive magic. Annihilates the target with a devastating blast.",
        "type": "Active",
        "class_id": 2,  # Mage
    },
    # Warrior Skills
    "power_strike": {
        "key_id": "power_strike",
        "name": "Power Strike",
        "description": "A heavy, focused blow that aims to break an enemy's guard.",
        "type": "Active",
        "class_id": 1,  # Warrior
    },
    # Rogue Skills
    "stealth": {
        "key_id": "stealth",
        "name": "Stealth",
        "description": "Fade into the shadows, becoming harder to detect.",
        "type": "Active",
        "class_id": 3,  # Rogue
    },
    # Cleric Skills
    "heal": {
        "key_id": "heal",
        "name": "Heal",
        "description": "A gentle prayer that mends minor wounds.",
        "type": "Active",
        "class_id": 4,  # Cleric
    },
    # Ranger Skills
    "true_shot": {
        "key_id": "true_shot",
        "name": "True Shot",
        "description": "A focused arrow shot that pierces vital points.",
        "type": "Active",
        "class_id": 5,  # Ranger
    },
}
