"""
test_loot_calculator.py

Verifies the drop rate calculation and RNG.
"""

import unittest
from unittest.mock import patch

from game_systems.rewards.loot_calculator import LootCalculator


class TestLootCalculator(unittest.TestCase):

    def test_calculate_drop_chance_common(self):
        # Common item: No Luck scaling (multiplier only from boost)
        base = 10.0
        rarity = "Common"
        luck = 999
        boost = 1.0

        chance = LootCalculator.calculate_drop_chance(base, rarity, luck, boost)
        self.assertEqual(chance, 10.0)

    def test_calculate_drop_chance_epic(self):
        # Epic item: Luck scaling applies
        base = 10.0
        rarity = "Epic"
        luck = 500
        boost = 1.0

        # Formula: 1 + (500/1000) = 1.5x
        # 10 * 1.5 = 15.0
        chance = LootCalculator.calculate_drop_chance(base, rarity, luck, boost)
        self.assertEqual(chance, 15.0)

    def test_calculate_drop_chance_max_luck(self):
        # Mythical item: Max Luck scaling (2.0x at 1000 Luck)
        base = 1.0
        rarity = "Mythical"
        luck = 1000
        boost = 1.0

        # 1 + (1000/1000) = 2.0x
        # 1 * 2.0 = 2.0
        chance = LootCalculator.calculate_drop_chance(base, rarity, luck, boost)
        self.assertEqual(chance, 2.0)

    def test_calculate_drop_chance_boost(self):
        # Boost multiplier applies to all
        base = 10.0
        rarity = "Common"
        luck = 0
        boost = 2.0

        chance = LootCalculator.calculate_drop_chance(base, rarity, luck, boost)
        self.assertEqual(chance, 20.0)

    def test_cap_at_100(self):
        # Chance should never exceed 100%
        base = 60.0
        rarity = "Common"
        luck = 0
        boost = 2.0 # 120%

        chance = LootCalculator.calculate_drop_chance(base, rarity, luck, boost)
        self.assertEqual(chance, 100.0)

    @patch("game_systems.rewards.loot_calculator.random.uniform")
    @patch("game_systems.rewards.loot_calculator.MATERIALS", {"test_item": {"rarity": "Common"}})
    def test_roll_drops_success(self, mock_uniform):
        # Mock roll to be low enough (5 < 10)
        mock_uniform.return_value = 5.0

        drops = [("test_item", 10.0)]
        luck = 0
        boost = 1.0

        result = LootCalculator.roll_drops(drops, luck, boost)
        self.assertEqual(result, ["test_item"])

    @patch("game_systems.rewards.loot_calculator.random.uniform")
    @patch("game_systems.rewards.loot_calculator.MATERIALS", {"test_item": {"rarity": "Common"}})
    def test_roll_drops_failure(self, mock_uniform):
        # Mock roll to be too high (15 > 10)
        mock_uniform.return_value = 15.0

        drops = [("test_item", 10.0)]
        luck = 0
        boost = 1.0

        result = LootCalculator.roll_drops(drops, luck, boost)
        self.assertEqual(result, [])

if __name__ == "__main__":
    unittest.main()
