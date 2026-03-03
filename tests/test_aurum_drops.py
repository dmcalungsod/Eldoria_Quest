"""
Tests for Aurum Drops
---------------------
Verifies that monsters now drop Aurum based on tier/level.
"""

import os
import sys
import unittest
from unittest.mock import MagicMock, patch

# Add repo root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from game_systems.rewards.aurum_calculator import AurumCalculator


class TestAurumDrops(unittest.TestCase):
    def test_aurum_calculator_normal(self):
        # Level 1 Normal
        # Base = 2. Mult = 1.5. = 3. Range 2-4.
        drops = [AurumCalculator.calculate_drop(1, "Normal") for _ in range(50)]
        self.assertTrue(all(d >= 1 for d in drops))
        self.assertTrue(any(d == 3 for d in drops))

        # Level 10 Normal
        # Base = 20. Mult = 1.5. = 30. Range 24-36.
        drops = [AurumCalculator.calculate_drop(10, "Normal") for _ in range(50)]
        avg = sum(drops) / len(drops)
        self.assertGreater(avg, 20)
        self.assertLess(avg, 40)

    def test_aurum_calculator_elite(self):
        # Level 10 Elite
        # Base = 20. Mult = 5.0. = 100. Range 80-120.
        drops = [AurumCalculator.calculate_drop(10, "Elite") for _ in range(50)]
        avg = sum(drops) / len(drops)
        self.assertGreater(avg, 80)
        self.assertLess(avg, 120)

    def test_aurum_calculator_boss(self):
        # Level 10 Boss
        # Base = 20. Mult = 20.0. = 400. Range 320-480.
        drops = [AurumCalculator.calculate_drop(10, "Boss") for _ in range(50)]
        avg = sum(drops) / len(drops)
        self.assertGreater(avg, 320)
        self.assertLess(avg, 480)

    def test_luck_bonus(self):
        # Level 10 Normal (30 base)
        # Luck 500 (+50% bonus? No, 1% per 10 luck. 500/1000 = 0.5. 1.0+0.5 = 1.5x)
        # Wait, formula is: 1.0 + min(0.5, luck / 1000.0)
        # So 500 luck -> 1.5x multiplier.
        # 30 * 1.5 = 45. Range 36-54.

        drop_no_luck = AurumCalculator.calculate_drop(10, "Normal", luck=0)
        drop_luck = AurumCalculator.calculate_drop(10, "Normal", luck=500)

        # Randomness might mess this up if we compare single values.
        # Let's check potential bounds.
        # No luck max: 30 * 1.2 = 36.
        # Luck min: 30 * 0.8 * 1.5 = 36.
        # So Luck 500 should almost always be >= No Luck.

        # Deterministic check? We can patch random.uniform.
        with patch("random.uniform", return_value=1.0):
            val_0 = AurumCalculator.calculate_drop(10, "Normal", luck=0)
            val_500 = AurumCalculator.calculate_drop(10, "Normal", luck=500)

            # 20 * 1.5 * 1.0 * 1.0 = 30
            self.assertEqual(val_0, 30)

            # 20 * 1.5 * 1.0 * 1.5 = 45
            self.assertEqual(val_500, 45)

    def test_combat_engine_integration(self):
        """Test that CombatEngine returns aurum in result."""
        from game_systems.combat.combat_engine import CombatEngine

        # Mock dependencies
        player = MagicMock()
        player.level = 5
        # Fix: Ensure hp_current behaves like an int for comparisons
        player.hp_current = 100
        player.is_stunned = False
        player.is_silenced = False
        player.stats.get_total_stats_dict.return_value = {"LCK": 0}
        monster = {"name": "Test", "level": 5, "tier": "Normal", "HP": 10, "drops": []}

        engine = CombatEngine(player, monster, [], 10, 1, stats_dict={"LCK": 0})

        # Force kill
        engine.monster_hp = 0

        result = engine.run_combat_turn()

        self.assertIn("aurum", result)
        self.assertGreater(result["aurum"], 0)
        # Level 5 Normal -> ~15 Aurum
        self.assertTrue(10 <= result["aurum"] <= 20)


if __name__ == "__main__":
    unittest.main()
