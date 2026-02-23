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


class TestCombatActions(unittest.TestCase):
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
            "ATK": 20,  # High attack to test mitigation
            "DEF": 0,
            "level": 1,
            "tier": "Normal",
            "skills": [],
        }

    def test_defend_action(self):
        """Test that Defend action reduces damage and restores MP."""
        current_mp = 10
        max_mp = 100
        stats = {"MP": 100, "HP": 100, "END": 10, "AGI": 10}

        # Instantiate CombatEngine
        engine = CombatEngine(
            player=self.player_wrapper,
            monster=self.monster.copy(),
            player_skills=[],
            player_mp=current_mp,
            player_class_id=1,
            stats_dict=stats,
            action="defend",
        )

        # Mock RNG
        with patch("random.random", return_value=0.9):
            with patch("random.uniform", return_value=1.0):
                result = engine.run_combat_turn()

        # Verify MP Restoration (5% of 100 = 5)
        # Note: If previous logic was correct, MP becomes 15
        expected_mp = 15
        self.assertEqual(result["mp_current"], expected_mp, "Defend should restore 5% MP")

        # Verify Damage Mitigation
        damage_defended = result["turn_report"]["damage_taken"]

        # Run again with "attack" to compare
        engine_attack = CombatEngine(
            player=self.player_wrapper,
            monster=self.monster.copy(),
            player_skills=[],
            player_mp=current_mp,
            player_class_id=1,
            stats_dict=stats,
            action="attack",
        )

        # Patch _decide_player_skill so we force a basic attack
        engine_attack._decide_player_skill = MagicMock(return_value={"skill": None})

        with patch("random.random", return_value=0.9):
            with patch("random.uniform", return_value=1.0):
                result_attack = engine_attack.run_combat_turn()

        damage_attacked = result_attack["turn_report"]["damage_taken"]

        self.assertTrue(damage_defended < damage_attacked, "Defend should reduce damage")
        self.assertAlmostEqual(damage_defended, int(damage_attacked * 0.5), delta=1)

    def test_flee_failed_action(self):
        """Test that Flee Failed results in player skip and monster attack."""
        engine = CombatEngine(
            player=self.player_wrapper,
            monster=self.monster,
            player_skills=[],
            player_mp=10,
            player_class_id=1,
            stats_dict={"MP": 100, "END": 10, "AGI": 10},
            action="flee_failed",
        )

        with patch("random.random", return_value=0.9):
            with patch("random.uniform", return_value=1.0):
                result = engine.run_combat_turn()

        self.assertEqual(
            result["turn_report"]["str_hits"],
            0,
            "Player should not attack on flee fail",
        )
        self.assertTrue(result["turn_report"]["damage_taken"] > 0, "Monster should attack")

    def test_special_ability_action(self):
        """Test that Special Ability action uses MP and deals boosted damage."""
        current_mp = 50
        max_mp = 100
        stats = {
            "MP": 100,
            "HP": 100,
            "STR": 20,
            "END": 10,
            "AGI": 10,
            "MAG": 10,
            "LCK": 10,
        }

        # Warrior (Class 1) -> Cleave (1.5x DMG)
        engine = CombatEngine(
            player=self.player_wrapper,
            monster=self.monster.copy(),
            player_skills=[],
            player_mp=current_mp,
            player_class_id=1,
            stats_dict=stats,
            action="special_ability",
        )

        # Mock RNG to ensure hit and standard variance
        with patch("random.random", return_value=0.9):  # No crit
            with patch("random.uniform", return_value=1.0):  # No variance
                # Run Special
                result_special = engine.run_combat_turn()

        # Check MP Deduction (Cost 20)
        self.assertEqual(result_special["mp_current"], 30, "Special Ability should cost 20 MP")

        # Check Damage
        # Compare with normal attack
        engine_normal = CombatEngine(
            player=self.player_wrapper,
            monster=self.monster.copy(),
            player_skills=[],
            player_mp=current_mp,
            player_class_id=1,
            stats_dict=stats,
            action="attack",
        )

        # Force basic attack
        engine_normal._decide_player_skill = MagicMock(return_value={"skill": None})

        with patch("random.random", return_value=0.9):
            with patch("random.uniform", return_value=1.0):
                result_normal = engine_normal.run_combat_turn()

        dmg_special = 1000 - result_special["monster_hp"]
        dmg_normal = 1000 - result_normal["monster_hp"]

        # Verify damage happened
        self.assertTrue(dmg_special > 0, "Special attack should deal damage")
        self.assertTrue(dmg_normal > 0, "Normal attack should deal damage")

        # Expected: Special ~ 1.5 * Normal
        # Allow small delta for integer rounding
        self.assertAlmostEqual(dmg_special, int(dmg_normal * 1.5), delta=1)


if __name__ == "__main__":
    unittest.main()
