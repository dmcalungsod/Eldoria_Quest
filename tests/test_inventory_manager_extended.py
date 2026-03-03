import unittest
from unittest.mock import MagicMock
from game_systems.items.inventory_manager import InventoryManager

class TestInventoryManagerExtended(unittest.TestCase):
    def setUp(self):
        self.mock_db = MagicMock()
        self.manager = InventoryManager(self.mock_db)

    def test_get_player_inventory(self):
        self.mock_db.get_inventory_items.return_value = [{"id": 1, "name": "Item"}]
        inv = self.manager.get_inventory(123)
        self.assertEqual(len(inv), 1)

    def test_add_item(self):
        self.manager.add_item(123, "iron_sword", "Iron Sword", "equipment")
        self.mock_db.add_inventory_item.assert_called()

if __name__ == "__main__":
    unittest.main()
