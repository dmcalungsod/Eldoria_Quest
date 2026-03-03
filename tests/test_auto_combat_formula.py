import unittest
import math
from game_systems.combat.auto_combat_formula import AutoCombatFormula


class MockPlayerStats:
    def __init__(self, **kwargs):
        self._stats = kwargs

    def get(self, k, default=0):
        return self._stats.get(k, default)

    @property
    def strength(self):
        return self._stats.get("STR", 0)

    @property
    def dexterity(self):
        return self._stats.get("DEX", 0)

    @property
    def agility(self):
        return self._stats.get("AGI", 0)

    @property
    def magic(self):
        return self._stats.get("MAG", 0)

    @property
    def endurance(self):
        return self._stats.get("END", 0)

    @property
    def luck(self):
        return self._stats.get("LCK", 0)

    @property
    def defense(self):
        return self._stats.get("DEF", 0)


class TestAutoCombatFormula(unittest.TestCase):
    def setUp(self):
        self.player_stats = MockPlayerStats(STR=20, END=15, AGI=10, LCK=5, DEF=5)
        self.monster = {
            "name": "Goblin",
            "HP": 50,
            "ATK": 15,
            "DEF": 5,
            "accuracy_percent": 0.0,
        }

    def test_calculate_player_dps(self):
        dps = AutoCombatFormula.calculate_player_dps(self.player_stats)
        self.assertGreater(dps, 0)

    def test_calculate_monster_mitigation(self):
        mitigation = AutoCombatFormula.calculate_monster_mitigation(self.monster)
        self.assertEqual(mitigation, 5 * (0.3 + (0.2 * min(1, 5 / 100))))

    def test_resolve_clash(self):
        result = AutoCombatFormula.resolve_clash(self.player_stats, self.monster)

        self.assertIn("turns_to_kill", result)
        self.assertIn("damage_taken", result)
        self.assertIn("player_dps", result)
        self.assertIn("monster_dps", result)

        self.assertGreater(result["turns_to_kill"], 0)
        self.assertGreaterEqual(result["damage_taken"], 0)

    def test_stance_impact(self):
        # Aggressive should take fewer turns but maybe more damage per turn
        agg = AutoCombatFormula.resolve_clash(
            self.player_stats, self.monster, stance="aggressive"
        )
        dfn = AutoCombatFormula.resolve_clash(
            self.player_stats, self.monster, stance="defensive"
        )

        self.assertGreater(agg["player_dps"], dfn["player_dps"])
        # In this specific setup, aggressive will kill much faster
        self.assertLessEqual(agg["turns_to_kill"], dfn["turns_to_kill"])


if __name__ == "__main__":
    unittest.main()
