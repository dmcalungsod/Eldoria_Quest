"""
test_crafting_experiment.py

Tests for the Alchemy Experimentation System.
"""

import sys
import os
import unittest
from unittest.mock import MagicMock, patch

# Mock pymongo BEFORE imports
sys.modules["pymongo"] = MagicMock()
sys.modules["pymongo.errors"] = MagicMock()

# Add repo root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))  # noqa: E402

from game_systems.crafting.crafting_system import CraftingSystem  # noqa: E402


class TestCraftingExperiment(unittest.TestCase):
    def setUp(self):
        self.mock_db = MagicMock()
        self.system = CraftingSystem(self.mock_db)
        self.discord_id = 12345

    def test_experiment_success(self):
        """Test a successful experiment using the 'volatile_brew' recipe."""
        # Recipe: slime_gel + fire_essence + obsidian_shard -> volatile_brew

        # Mock Inventory Items
        self.mock_db.get_inventory_item.side_effect = [
            {"item_key": "slime_gel", "item_type": "material", "id": 1, "count": 5},
            {"item_key": "fire_essence", "item_type": "material", "id": 2, "count": 2},
            {"item_key": "obsidian_shard", "item_type": "material", "id": 3, "count": 10},
        ]

        # Mock Consume Success
        self.mock_db.consume_item_atomic.return_value = True

        # Execute
        material_ids = [1, 2, 3]
        success, msg, result = self.system.experiment(self.discord_id, material_ids)

        # Verify
        self.assertTrue(success)
        self.assertIn("volatile_brew", result["id"])
        self.assertIn("Volatile Brew", msg)

        # Verify DB calls
        # 3 consumptions
        self.assertEqual(self.mock_db.consume_item_atomic.call_count, 3)
        # 1 addition
        self.mock_db.add_inventory_item.assert_called_with(
            self.discord_id, "volatile_brew", "Volatile Brew", "consumable", "Rare", 1
        )

    def test_experiment_failure_slag(self):
        """Test a failed experiment resulting in slag."""
        # Random inputs: slime_gel + iron_ore

        self.mock_db.get_inventory_item.side_effect = [
            {"item_key": "slime_gel", "item_type": "material", "id": 1},
            {"item_key": "iron_ore", "item_type": "material", "id": 4},
        ]
        self.mock_db.consume_item_atomic.return_value = True

        material_ids = [1, 4]
        success, msg, result = self.system.experiment(self.discord_id, material_ids)

        self.assertFalse(success)
        self.assertIn("slag", msg)

        # Verify Slag added
        self.mock_db.add_inventory_item.assert_called_with(
            self.discord_id, "slag", "Alchemical Slag", "material", "Common", 1
        )

    def test_experiment_duplicate_ids(self):
        """Test using the same item stack twice."""
        material_ids = [1, 1]
        success, msg, result = self.system.experiment(self.discord_id, material_ids)

        self.assertFalse(success)
        self.assertIn("Cannot use the same item stack", msg)
        self.mock_db.consume_item_atomic.assert_not_called()

    def test_experiment_invalid_type(self):
        """Test using equipment."""
        self.mock_db.get_inventory_item.return_value = {
            "item_key": "sword", "item_type": "equipment", "id": 99
        }

        success, msg, result = self.system.experiment(self.discord_id, [99])

        self.assertFalse(success)
        self.assertIn("Only materials", msg)

if __name__ == '__main__':
    unittest.main()
