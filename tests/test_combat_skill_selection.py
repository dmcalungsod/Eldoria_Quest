import os
import sys
import unittest
from unittest.mock import MagicMock, patch

# Add repo root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Mock external dependencies
sys.modules["pymongo"] = MagicMock()
sys.modules["discord"] = MagicMock()

from game_systems.combat.combat_engine import CombatEngine  # noqa: E402
from game_systems.player.level_up import LevelUpSystem  # noqa: E402
from game_systems.player.player_stats import PlayerStats  # noqa: E402


class TestCombatSkillSelection(unittest.TestCase):
    def setUp(self):
        self.stats = PlayerStats(str_base=10, end_base=10, dex_base=10, agi_base=10, mag_base=10)
        self.player_wrapper = MagicMock(spec=LevelUpSystem)
        self.player_wrapper.stats = self.stats
        self.player_wrapper.level = 1
        self.player_wrapper.hp_current = 50
        self.player_wrapper.hp_max = 100

        self.monster = {
            "name": "Test Monster",
            "HP": 1000,
            "max_hp": 1000,
            "MP": 10,
            "ATK": 20,
            "DEF": 0,
            "level": 1,
            "tier": "Normal",
            "skills": [],
        }

        self.fireball_skill = {
            "key_id": "fireball",
            "name": "Fireball",
            "type": "Active",
            "skill_level": 1,
            "mp_cost": 10,
            "power_multiplier": 1.5,
            "heal_power": 0,
            "buff_data": None,
            "scaling_stat": "MAG",
            "scaling_factor": 1.0,
        }

        self.heal_skill = {
            "key_id": "minor_heal",
            "name": "Minor Heal",
            "type": "Active",
            "skill_level": 1,
            "mp_cost": 5,
            "power_multiplier": 0,
            "heal_power": 20,
            "buff_data": None,
            "scaling_stat": "MAG",
            "scaling_factor": 1.0,
        }

    def test_explicit_skill_usage(self):
        """Test that action='skill:fireball' uses the skill correctly."""
        current_mp = 20
        stats = {"MP": 100, "HP": 100, "MAG": 20}

        engine = CombatEngine(
            player=self.player_wrapper,
            monster=self.monster.copy(),
            player_skills=[self.fireball_skill],
            player_mp=current_mp,
            player_class_id=2,  # Mage
            stats_dict=stats,
            action="skill:fireball",
        )

        with patch("random.random", return_value=0.9):
            with patch("random.uniform", return_value=1.0):
                result = engine.run_combat_turn()

        # Check MP Deduction
        self.assertEqual(result["mp_current"], 10, "Fireball should cost 10 MP")

        # Check that skill was used (log or damage)
        self.assertIn("mag_hits", result["turn_report"], "Fireball should register as mag_hit")
        self.assertTrue(result["turn_report"]["skills_used"] > 0, "Skill usage should be tracked")

        # Verify damage > 0
        self.assertTrue(result["monster_hp"] < 1000, "Monster should take damage from fireball")

    def test_explicit_heal_usage(self):
        """Test that action='skill:minor_heal' heals the player."""
        current_mp = 20
        stats = {"MP": 100, "HP": 100, "MAG": 20}
        self.player_wrapper.hp_current = 50

        engine = CombatEngine(
            player=self.player_wrapper,
            monster=self.monster.copy(),
            player_skills=[self.heal_skill],
            player_mp=current_mp,
            player_class_id=4,  # Cleric
            stats_dict=stats,
            action="skill:minor_heal",
        )

        with patch("random.random", return_value=0.9):
            with patch("random.uniform", return_value=1.0):
                result = engine.run_combat_turn()

        # Check MP Deduction
        self.assertEqual(result["mp_current"], 15, "Heal should cost 5 MP")

        # Check Healing
        self.assertTrue(result["hp_current"] > 50, "Player should be healed")
        self.assertIn("Minor Heal", str(result["phrases"]), "Log should mention restoration")

    def test_insufficient_mp_fallback(self):
        """Test fallback to basic attack if MP is insufficient."""
        current_mp = 5  # Fireball costs 10
        stats = {"MP": 100, "HP": 100, "MAG": 20}

        engine = CombatEngine(
            player=self.player_wrapper,
            monster=self.monster.copy(),
            player_skills=[self.fireball_skill],
            player_mp=current_mp,
            player_class_id=2,
            stats_dict=stats,
            action="skill:fireball",
        )

        with patch("random.random", return_value=0.9):
            with patch("random.uniform", return_value=1.0):
                result = engine.run_combat_turn()

        # MP should NOT be deducted (or maybe just for basic attack? Basic attack is 0 MP)
        self.assertEqual(result["mp_current"], 5, "MP should not change on fallback")

        # Should be a basic attack (str_hits or mag_hits depending on class default attack, Mage is mag)
        # But specifically not a skill usage
        self.assertEqual(result["turn_report"]["skills_used"], 0, "Skill should not be used")

        # Log should mention failure
        log_str = "".join([str(p) for p in result["phrases"]])
        self.assertIn("Not enough MP", log_str, "Log should warn about MP")

    def test_unknown_skill_fallback(self):
        """Test fallback if skill key is not found."""
        current_mp = 20
        stats = {"MP": 100, "HP": 100, "MAG": 20}

        engine = CombatEngine(
            player=self.player_wrapper,
            monster=self.monster.copy(),
            player_skills=[self.fireball_skill],
            player_mp=current_mp,
            player_class_id=2,
            stats_dict=stats,
            action="skill:unknown_skill",
        )

        with patch("random.random", return_value=0.9):
            with patch("random.uniform", return_value=1.0):
                result = engine.run_combat_turn()

        self.assertEqual(result["mp_current"], 20, "MP should not change")
        self.assertEqual(result["turn_report"]["skills_used"], 0, "Skill should not be used")

        log_str = "".join([str(p) for p in result["phrases"]])
        self.assertIn("Skill Failed", log_str, "Log should warn about unknown skill")

if __name__ == "__main__":
    unittest.main()
