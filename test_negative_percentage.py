import unittest
from unittest.mock import MagicMock
from game_systems.combat.combat_effects import CombatEffects

class TestNegativePercentage(unittest.TestCase):
    def test_negative_percentage_debuff(self):
        monster = {
            "name": "Test Monster",
            "HP": 100,
            "max_hp": 100,
            "ATK": 10,
            "DEF": 50,
            "END": 50,
        }
        skill = {
            "name": "Vitriol Bomb",
            "debuff": {"DEF_percent": -0.1, "END_percent": -0.1, "duration": 3}
        }
        stats_dict = {"DEX": 10}

        msg = CombatEffects.apply_monster_debuff(monster, skill, stats_dict)
        print("Debuff applied msg:", msg)
        print("Monster debuffs:", monster["debuffs"])

        eff_monster = CombatEffects.get_effective_monster_stats(monster)
        print("Effective DEF:", eff_monster.get("DEF"))
        print("Effective END:", eff_monster.get("END"))

if __name__ == "__main__":
    unittest.main()
