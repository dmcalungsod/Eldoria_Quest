"""
skills_data.py

Contains all skill definitions for Eldoria Quest.
This data is imported by populate_database.py.
"""

SKILLS = {
    # === WARRIOR (Class 1) ===
    "power_strike": {
        "key_id": "power_strike",
        "name": "Power Strike",
        "description": "A heavy, focused blow that aims to break an enemy's guard. Scales heavily with STR.",
        "type": "Active",
        "class_id": 1,
        "mp_cost": 5,
        "power_multiplier": 1.5,
        "learn_cost": 0,  # Default skill
        "upgrade_cost": 200,  # Base Vestige cost
        "scaling_stat": "STR",
        "scaling_factor": 3.0,
    },
    "cleave": {
        "key_id": "cleave",
        "name": "Cleave",
        "description": "A wide, sweeping attack that strikes all foes.",
        "type": "Active",
        "class_id": 1,
        "mp_cost": 10,
        "power_multiplier": 1.1,  # Lower multiplier, but hits all
        "learn_cost": 2000,
        "upgrade_cost": 300,
        "scaling_stat": "STR",
        "scaling_factor": 2.7,
    },
    "endure": {
        "key_id": "endure",
        "name": "Endure",
        "description": "Brace for impact, temporarily boosting your END.",
        "type": "Active",
        "class_id": 1,
        "mp_cost": 8,
        "buff": {"END_percent": 0.25, "duration": 3},  # +25% END for 3 turns
        "learn_cost": 1500,
        "upgrade_cost": 250,
        "scaling_stat": "END",
        "scaling_factor": 1.0,
    },
    # === MAGE (Class 2) ===
    "fireball": {
        "key_id": "fireball",
        "name": "Fireball",
        "description": "A basic incantation that hurls a sphere of fire.",
        "type": "Active",
        "class_id": 2,
        "mp_cost": 5,
        "power_multiplier": 1.2,
        "learn_cost": 0,  # Default skill
        "upgrade_cost": 200,
        "scaling_stat": "MAG",
        "scaling_factor": 2.8,
    },
    "ice_lance": {
        "key_id": "ice_lance",
        "name": "Ice Lance",
        "description": "Forms a spear of magical ice and hurls it at one foe.",
        "type": "Active",
        "class_id": 2,
        "mp_cost": 8,
        "power_multiplier": 1.4,
        "learn_cost": 2000,
        "upgrade_cost": 300,
        "scaling_stat": "MAG",
        "scaling_factor": 2.8,
    },
    "mana_shield": {
        "key_id": "mana_shield",
        "name": "Mana Shield",
        "description": "Create a barrier that converts damage taken from HP to MP.",
        "type": "Active",
        "class_id": 2,
        "mp_cost": 15,  # Cost to activate
        "buff": {"mana_shield": True, "duration": 5},
        "learn_cost": 3000,
        "upgrade_cost": 400,
        "scaling_stat": "MAG",
        "scaling_factor": 1.0,
    },
    "explosion": {
        "key_id": "explosion",
        "name": "Explosion",
        "description": "The ultimate offensive magic. Annihilates the target.",
        "type": "Active",
        "class_id": 2,
        "mp_cost": 25,
        "power_multiplier": 2.5,
        "learn_cost": 10000,
        "upgrade_cost": 800,
        "scaling_stat": "MAG",
        "scaling_factor": 2.8,
    },
    # === ROGUE (Class 3) ===
    "stealth": {
        "key_id": "stealth",
        "name": "Stealth",
        "description": "Fade into the shadows, becoming harder to detect.",
        "type": "Passive",
        "class_id": 3,
        "mp_cost": 0,
        "passive_bonus": {"AGI_percent": 0.1},  # +10% AGI
        "learn_cost": 0,  # Default skill
        "upgrade_cost": 500,
        "scaling_stat": "AGI",
        "scaling_factor": 1.0,
    },
    "double_strike": {
        "key_id": "double_strike",
        "name": "Double Strike",
        "description": "A rapid two-hit attack that scales with DEX.",
        "type": "Active",
        "class_id": 3,
        "mp_cost": 10,
        "power_multiplier": 1.8,  # Scaled with DEX
        "learn_cost": 2500,
        "upgrade_cost": 350,
        "scaling_stat": "DEX",
        "scaling_factor": 2.6,
    },
    "toxic_blade": {
        "key_id": "toxic_blade",
        "name": "Toxic Blade",
        "description": "A weak strike that applies a potent poison.",
        "type": "Active",
        "class_id": 3,
        "mp_cost": 12,
        "power_multiplier": 0.8,
        "debuff": {"poison": 5, "duration": 3},  # 5 damage per turn for 3 turns
        "learn_cost": 2000,
        "upgrade_cost": 300,
        "scaling_stat": "DEX",
        "scaling_factor": 2.6,
    },
    # === CLERIC (Class 4) ===
    "heal": {
        "key_id": "heal",
        "name": "Heal",
        "description": "A gentle prayer that mends minor wounds.",
        "type": "Active",
        "class_id": 4,
        "mp_cost": 10,
        # --- BUFFED: 30 -> 45 ---
        "heal_power": 45,
        "learn_cost": 0,  # Default skill
        "upgrade_cost": 200,
        "scaling_stat": "MAG",
        "scaling_factor": 1.5,
    },
    "smite": {
        "key_id": "smite",
        "name": "Smite",
        "description": "Call down holy energy to strike a foe. Scales with MAG.",
        "type": "Active",
        "class_id": 4,
        "mp_cost": 8,
        # --- BUFFED: 1.5 -> 1.7 ---
        "power_multiplier": 1.7,
        "learn_cost": 1500,
        "upgrade_cost": 250,
        "scaling_stat": "MAG",
        "scaling_factor": 2.8,
    },
    "blessing": {
        "key_id": "blessing",
        "name": "Blessing",
        "description": "Grants a divine blessing, increasing all stats temporarily.",
        "type": "Active",
        "class_id": 4,
        "mp_cost": 15,
        "buff": {"all_stats_percent": 0.1, "duration": 3},  # +10% all stats
        "learn_cost": 3000,
        "upgrade_cost": 400,
        "scaling_stat": "MAG",
        "scaling_factor": 1.0,
    },
    # === RANGER (Class 5) ===
    "true_shot": {
        "key_id": "true_shot",
        "name": "True Shot",
        "description": "A focused arrow shot that pierces vital points.",
        "type": "Active",
        "class_id": 5,
        "mp_cost": 8,
        "power_multiplier": 1.4,
        "learn_cost": 0,  # Default skill
        "upgrade_cost": 200,
        "scaling_stat": "DEX",
        "scaling_factor": 2.6,
    },
    "multi_shot": {
        "key_id": "multi_shot",
        "name": "Multi-Shot",
        "description": "Fire a spray of arrows at all foes.",
        "type": "Active",
        "class_id": 5,
        "mp_cost": 12,
        "power_multiplier": 1.1,  # Lower multiplier, hits all
        "learn_cost": 2000,
        "upgrade_cost": 300,
        "scaling_stat": "DEX",
        "scaling_factor": 2.6,
    },
    "survivalist": {
        "key_id": "survivalist",
        "name": "Survivalist",
        "description": "Your knowledge of the wild hardens your resolve.",
        "type": "Passive",
        "class_id": 5,
        "mp_cost": 0,
        "passive_bonus": {"END_percent": 0.1, "AGI_percent": 0.05},  # +10% END, +5% AGI
        "learn_cost": 3000,
        "upgrade_cost": 500,
        "scaling_stat": "END",
        "scaling_factor": 1.0,
    },
}
