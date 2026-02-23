import os
import sys
import unittest
from unittest.mock import MagicMock

# Add repo root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from game_systems.combat.combat_engine import CombatEngine


class TestCombatCounter(unittest.TestCase):
    def setUp(self):
        self.player = MagicMock()
        self.player.hp_current = 100
        self.player.stats.max_hp = 100
        self.player.stats.get_total_stats_dict.return_value = {
            "HP": 100,
            "MP": 100,
            "ATK": 10,
            "DEF": 10,
        }
        self.player.level = 1

        self.monster = {
            "name": "Test Monster",
            "HP": 100,
            "max_hp": 100,
            "MP": 100,
            "ATK": 20,
            "DEF": 5,
            "skills": [],
        }

    def test_parry_physical_charge(self):
        # Setup Physical Charge
        self.monster["charged_skill"] = {
            "name": "Smash",
            "type": "physical",
            "power": 2.0,
        }

        engine = CombatEngine(
            player=self.player,
            monster=self.monster,
            player_skills=[],
            player_mp=100,
            player_class_id=1,
            action="defend",
        )

        result = engine.run_combat_turn()

        # Verify Parry
        phrases = " ".join(result["phrases"])
        self.assertIn("PARRIED!", phrases)
        self.assertIn("Reflected!", phrases)
        self.assertIn("misses its turn", phrases)  # Monster should be stunned
        self.assertLess(result["monster_hp"], 100)  # Monster took reflect damage
        self.assertNotIn("unleashes **Smash**", phrases)  # Charge cancelled

    def test_interrupt_magical_charge(self):
        # Setup Magical Charge
        self.monster["charged_skill"] = {
            "name": "Doom",
            "type": "magical",
            "power": 2.0,
        }

        engine = CombatEngine(
            player=self.player,
            monster=self.monster,
            player_skills=[],
            player_mp=100,
            player_class_id=1,
            action="attack",
        )

        result = engine.run_combat_turn()

        # Verify Interrupt
        phrases = " ".join(result["phrases"])
        self.assertIn("INTERRUPTED!", phrases)
        self.assertIn("misses its turn", phrases)
        self.assertNotIn("unleashes **Doom**", phrases)
        # Should be a crit
        self.assertEqual(result["turn_report"]["player_crit"], 1)

    def test_fail_counter_wrong_action(self):
        # Setup Physical Charge but Player Attacks (Wrong)
        self.monster["charged_skill"] = {
            "name": "Smash",
            "type": "physical",
            "power": 2.0,
        }

        engine = CombatEngine(
            player=self.player,
            monster=self.monster,
            player_skills=[],
            player_mp=100,
            player_class_id=1,
            action="attack",
        )

        result = engine.run_combat_turn()

        phrases = " ".join(result["phrases"])
        self.assertNotIn("PARRIED!", phrases)
        self.assertNotIn("INTERRUPTED!", phrases)
        # Monster should execute charge
        self.assertIn("unleashes **Smash**", phrases)


if __name__ == "__main__":
    unittest.main()
