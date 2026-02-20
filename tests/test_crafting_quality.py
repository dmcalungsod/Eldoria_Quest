import os
import sys
import unittest
from unittest.mock import MagicMock, patch

# Ensure repo root is in path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Mock dependencies before import
sys.modules["pymongo"] = MagicMock()
sys.modules["pymongo.errors"] = MagicMock()

from database.database_manager import DatabaseManager  # noqa: E402
from game_systems.crafting.crafting_system import CraftingSystem  # noqa: E402
from game_systems.items.equipment_manager import EquipmentManager  # noqa: E402


class TestCraftingQuality(unittest.TestCase):
    def setUp(self):
        self.mock_db = MagicMock(spec=DatabaseManager)
        self.crafting = CraftingSystem(self.mock_db)
        self.equipment_manager = EquipmentManager(self.mock_db)
        self.discord_id = 12345

        # Mock Equipment Data lookup
        self.mock_db.get_equipment_id_by_name.return_value = 101
        self.mock_db.get_player.return_value = {"class_id": 1} # For allowed slots check if needed, though mostly for crafting

    @patch("random.random")
    def test_roll_quality_upgrade(self, mock_random):
        # Force upgrade: first roll < 0.1, second roll >= 0.1 (stop cascade)
        mock_random.side_effect = [0.05, 0.5]

        new_rarity = self.crafting._roll_quality("Common")
        self.assertEqual(new_rarity, "Uncommon")

    @patch("random.random")
    def test_roll_quality_no_upgrade(self, mock_random):
        # No upgrade: roll >= 0.1
        mock_random.return_value = 0.5

        new_rarity = self.crafting._roll_quality("Common")
        self.assertEqual(new_rarity, "Common")

    @patch("random.random")
    def test_roll_quality_cascade(self, mock_random):
        # Upgrade twice: 0.05, 0.05, 0.5
        mock_random.side_effect = [0.05, 0.05, 0.5]

        new_rarity = self.crafting._roll_quality("Common")
        self.assertEqual(new_rarity, "Rare")

    @patch("game_systems.crafting.crafting_system.EQUIPMENT_DATA", {
        "gen_sword_001": {
            "name": "Rusted Sword",
            "rarity": "Common",
            "slot": "sword",
            "stats_bonus": {"STR": 10},
        }
    })
    @patch("game_systems.crafting.crafting_system.EQUIPMENT_RECIPES", {
        "craft_rusted_sword": {
            "output_key": "gen_sword_001",
            "type": "equipment",
            "cost": 10,
            "materials": {"iron_ore": 1}
        }
    })
    @patch("random.random")
    def test_craft_item_quality_upgrade(self, mock_random):
        # Setup checks
        self.mock_db.get_player.return_value = {"aurum": 100}
        self.mock_db.get_inventory_item_count.return_value = 10
        self.mock_db.remove_inventory_item.return_value = True

        # Force upgrade to Uncommon
        mock_random.side_effect = [0.05, 0.5]

        success, msg, item = self.crafting.craft_item(self.discord_id, "craft_rusted_sword")

        self.assertTrue(success)
        self.assertIn("Critical Success", msg)
        self.assertIn("Uncommon", msg)

        # Verify DB add
        self.mock_db.add_inventory_item.assert_called()
        args = self.mock_db.add_inventory_item.call_args[0]
        # args: (discord_id, item_key, item_name, item_type, rarity, amount, slot, source)
        self.assertEqual(args[2], "Fine Rusted Sword") # Name prefixed
        self.assertEqual(args[4], "Uncommon") # Rarity updated

    def test_equipment_manager_quality_scaling(self):
        # Setup static data
        static_item = {
            "name": "Rusted Sword",
            "rarity": "Common",
            "str_bonus": 10,
        }
        self.mock_db._col.return_value.find_one.return_value = static_item
        self.mock_db.get_player_stats_json.return_value = {} # Empty stats

        # Mock get_player_vitals to prevent clamping error
        self.mock_db.get_player_vitals.return_value = {"current_hp": 100, "current_mp": 50}

        # Setup inventory item (Upgraded to Uncommon)
        inventory_item = {
            "item_key": "101",
            "item_source_table": "equipment",
            "rarity": "Uncommon", # Higher than base
        }
        self.mock_db.get_equipped_items.return_value = [inventory_item]

        # Run recalculation
        stats = self.equipment_manager.recalculate_player_stats(self.discord_id)

        # Verify stats
        # Common (1.0) -> Uncommon (1.1). 10 * 1.1 = 11.
        # Base STR is 1, so total is 1 + 11 = 12
        self.assertEqual(stats.strength, 12)

    def test_dismantle_upgraded_item(self):
        # Inventory item has prefixed name
        inv_item = {
            "id": 1,
            "item_key": "101", # ID of Rusted Sword
            "item_name": "Fine Rusted Sword",
            "item_type": "equipment",
            "rarity": "Uncommon",
            "equipped": 0,
            "item_source_table": "equipment"
        }
        self.mock_db.get_inventory_item_by_id.return_value = inv_item

        # Static data has original name
        self.mock_db.get_item_from_source_table.return_value = {
            "name": "Rusted Sword"
        }

        # Mock consume
        self.mock_db.consume_item_atomic.return_value = True

        # Recipe exists for "Rusted Sword"
        with patch("game_systems.crafting.crafting_system.EQUIPMENT_RECIPES", {
            "craft_rusted_sword": {
                "name": "Rusted Sword",
                "materials": {"iron_ore": 2} # Return 1
            }
        }):
            success, msg, rewards = self.crafting.dismantle_item(self.discord_id, 1)

            self.assertTrue(success)
            self.assertEqual(rewards.get("iron_ore"), 1)
            # Should have used ID lookup to find original name "Rusted Sword"
            self.mock_db.get_item_from_source_table.assert_called_with("equipment", 101)

if __name__ == "__main__":
    unittest.main()
