from game_systems.combat.damage_formula import DamageFormula

stats_dict = {"STR": 208, "DEX": 50, "MAG": 50, "LCK": 10, "END": 10, "DEF": 10}
monster = {"DEF": 0}

skill = {
    "scaling_stat": "STR",
    "scaling_factor": 2.7,
    "power_multiplier": 1.5
}

normal_dmg, _, _ = DamageFormula.player_attack(stats_dict, monster)
skill_dmg, _, _ = DamageFormula.player_skill(stats_dict, monster, skill, 1)

print(f"Normal Attack: {normal_dmg}")
print(f"Power Strike: {skill_dmg}")
