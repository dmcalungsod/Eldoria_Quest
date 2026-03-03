import unittest
from unittest.mock import MagicMock

from game_systems.items.consumable_manager import ConsumableManager


class TestConsumableManagerExtended(unittest.TestCase):
    def setUp(self):
        self.mock_db = MagicMock()
        self.manager = ConsumableManager(self.mock_db)

    def test_use_consumable_success(self):
        player_id = 123
        # Mock item in inventory
        item = {"id": 201, "item_key": "health_potion", "count": 2, "item_type": "consumable"}
        self.mock_db.get_inventory_item.return_value = item
        # Mock consumable data
        from game_systems.data import consumables

        consumables.CONSUMABLES["health_potion"] = {
            "id": "health_potion",
            "effect": {"heal": 20},
            "name": "Health Potion",
        }
        self.mock_db.get_player_vitals.return_value = {"current_hp": 50, "current_mp": 50}
        self.mock_db.get_player_stats_json.return_value = {"END": {"base": 10, "bonus": 0}}
        self.mock_db.consume_item_atomic.return_value = True

        success, msg = self.manager.use_item(player_id, 201)

        self.assertTrue(success)
        self.assertIn("healed", msg)
        self.mock_db.consume_item_atomic.assert_called()

    def test_use_consumable_not_found(self):
        self.mock_db.get_inventory_item.return_value = None
        success, msg = self.manager.use_item(123, 999)
        self.assertFalse(success)
        self.assertIn("not found", msg)


if __name__ == "__main__":
    unittest.main()
