import unittest
from unittest.mock import MagicMock
from game_systems.items.item_manager import ItemManager

class TestItemManagerExtended(unittest.TestCase):
    def setUp(self):
        self.mock_db = MagicMock()
        self.manager = ItemManager()
        self.manager.db = self.mock_db # Inject mock if needed, though ItemManager might use a global or internal db

    def test_get_equipment_by_id(self):
        # Mock database response
        self.mock_db._col.return_value.find_one.return_value = {"id": 101, "name": "Iron Sword", "rarity": "Common"}
        
        item = self.manager.get_equipment_by_id(101)
        self.assertEqual(item["name"], "Iron Sword")

    def test_search_items(self):
        self.mock_db._col.return_value.find.return_value = [
            {"name": "Iron Sword", "id": 101}
        ]
        
        results = self.manager.search_items("Iron")
        self.assertGreater(len(results), 0)
        self.assertEqual(results[0]["name"], "Iron Sword")

if __name__ == "__main__":
    unittest.main()
