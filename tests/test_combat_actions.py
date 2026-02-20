import unittest
from unittest.mock import MagicMock, patch
import sys
import os

# Add repo root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Mock external dependencies
sys.modules['pymongo'] = MagicMock()
sys.modules['discord'] = MagicMock()

from game_systems.combat.combat_engine import CombatEngine
from game_systems.player.player_stats import PlayerStats
from game_systems.player.level_up import LevelUpSystem

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
            "HP": 50,
            "max_hp": 50,
            "MP": 10,
            "ATK": 20, # High attack to test mitigation
            "DEF": 0,
            "level": 1,
            "tier": "Normal",
            "skills": []
        }

    def test_defend_action(self):
        """Test that Defend action reduces damage and restores MP."""
        current_mp = 10
        max_mp = 100
        self.stats.get_total_stats_dict = MagicMock(return_value={"MP": max_mp, "HP": 100, "END": 10, "AGI": 10})

        engine = CombatEngine(
            player=self.player_wrapper,
            monster=self.monster,
            player_skills=[],
            player_mp=current_mp,
            player_class_id=1,
            stats_dict={"MP": max_mp, "END": 10, "AGI": 10},
            action="defend"
        )

        # Mock RNG to ensure monster hits (no dodge)
        # Monster attack uses random.random() < dodge_chance (0.001 * agi)
        # If random() > dodge_chance, it hits.
        with patch('random.random', return_value=0.9):
            # Mock variance to 1.0
            with patch('random.uniform', return_value=1.0):
                result = engine.run_combat_turn()

        # Verify MP Restoration (5% of 100 = 5)
        expected_mp = 15
        self.assertEqual(result["mp_current"], expected_mp, "Defend should restore 5% MP")

        # Verify Damage Mitigation
        # Monster ATK 20. Player DEF (END 10 -> Bonus 15).
        # Def Reduction = 15 * (0.3 + 0.2 * 0.15) = 15 * 0.33 = ~5.
        # Base Damage = 20 - 5 = 15.
        # Defend halves it -> 7.
        # Wait, let's just check if damage is roughly half of what it would be.

        # Run again with "attack" to compare
        engine_attack = CombatEngine(
            player=self.player_wrapper,
            monster=self.monster.copy(),
            player_skills=[],
            player_mp=current_mp,
            player_class_id=1,
            stats_dict={"MP": max_mp, "END": 10, "AGI": 10},
            action="attack"
        )
        with patch('random.random', return_value=0.9):
             with patch('random.uniform', return_value=1.0):
                # Mock _decide_player_skill to return None (Basic Attack)
                with patch.object(CombatEngine, '_decide_player_skill', return_value={"skill": None, "reason": "forced"}):
                    result_attack = engine_attack.run_combat_turn()

        damage_defended = result["turn_report"]["damage_taken"]
        damage_attacked = result_attack["turn_report"]["damage_taken"]

        # print(f"Defended Dmg: {damage_defended}, Attacked Dmg: {damage_attacked}")
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
            action="flee_failed"
        )

        with patch('random.random', return_value=0.9):
            with patch('random.uniform', return_value=1.0):
                result = engine.run_combat_turn()

        self.assertEqual(result["turn_report"]["str_hits"], 0, "Player should not attack on flee fail")
        self.assertTrue(result["turn_report"]["damage_taken"] > 0, "Monster should attack")

if __name__ == '__main__':
    unittest.main()
