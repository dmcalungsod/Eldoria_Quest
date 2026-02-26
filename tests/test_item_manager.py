import json
import os
import sys
import unittest
from unittest.mock import MagicMock, patch

# Add repo root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

class TestItemManager(unittest.TestCase):
    def setUp(self):
        # Patch sys.modules to mock dependencies
        self.modules_patcher = patch.dict(sys.modules)
        self.modules_patcher.start()

        mock_pymongo = MagicMock()
        sys.modules["pymongo"] = mock_pymongo
        sys.modules["pymongo.errors"] = MagicMock()

        # Mock DatabaseManager
        self.mock_db_cls = MagicMock()
        self.mock_db = self.mock_db_cls.return_value

        # We need to patch DatabaseManager where it is imported in item_manager
        # Or better, patch it before import
        sys.modules["database.database_manager"] = MagicMock()
        sys.modules["database.database_manager"].DatabaseManager = self.mock_db_cls

        # Import ItemManager
        import game_systems.items.item_manager
        # Reload to ensure mocks are used
        import importlib
        importlib.reload(game_systems.items.item_manager)

        self.ItemManager = game_systems.items.item_manager.ItemManager
        self.item_manager_module = game_systems.items.item_manager

        # The module instantiates a singleton 'item_manager' at the end.
        # We can test the class directly or the singleton.
        # Since the singleton uses the mocked DB (because we mocked the class before import),
        # it should be fine.
        self.manager = self.item_manager_module.item_manager
        # Override db instance just in case
        self.manager.db = self.mock_db

    def tearDown(self):
        self.modules_patcher.stop()

    def test_get_equipment_stats_valid(self):
        # Setup mock return
        col_mock = MagicMock()
        self.mock_db._col.return_value = col_mock
        col_mock.find_one.return_value = {"id": 1, "str_bonus": 5, "dex_bonus": 0}

        stats = self.manager.get_equipment_stats("1", "equipment")

        self.assertEqual(stats, {"STR": 5})
        col_mock.find_one.assert_called_with({"id": 1}, {"_id": 0})

    def test_get_equipment_stats_invalid_table(self):
        stats = self.manager.get_equipment_stats("1", "invalid_table")
        self.assertEqual(stats, {})

    def test_get_equipment_stats_invalid_id(self):
        stats = self.manager.get_equipment_stats("abc", "equipment")
        self.assertEqual(stats, {})

    def test_get_equipment_by_id(self):
        col_mock = MagicMock()
        self.mock_db._col.return_value = col_mock
        col_mock.find_one.return_value = {"name": "Sword"}

        item = self.manager.get_equipment_by_id(10)

        self.assertEqual(item, {"name": "Sword"})
        self.mock_db._col.assert_called_with("equipment")
        col_mock.find_one.assert_called_with({"id": 10}, {"_id": 0})

    def test_search_items(self):
        col_mock = MagicMock()
        self.mock_db._col.return_value = col_mock

        # Setup find returns for different calls
        # 1. Equipment
        # 2. Class Equipment
        # 3. Consumables
        # 4. Quest Items

        # We need check side_effect of _col to return different mocks or handle calls
        # Or just same mock returning different things?
        # The manager calls _col("equipment"), then _col("class_equipment"), etc.

        equip_mock = MagicMock()
        class_mock = MagicMock()
        consu_mock = MagicMock()
        quest_mock = MagicMock()

        def col_side_effect(name):
            if name == "equipment": return equip_mock
            if name == "class_equipment": return class_mock
            if name == "consumables": return consu_mock
            if name == "quest_items": return quest_mock
            return MagicMock()

        self.mock_db._col.side_effect = col_side_effect

        equip_mock.find.return_value = [{"name": "Sword", "id": 1}]
        class_mock.find.return_value = []
        consu_mock.find.return_value = [{"name": "Potion", "id": 2}]
        quest_mock.find.return_value = []

        results = self.manager.search_items("foo")

        self.assertEqual(len(results), 2)
        self.assertEqual(results[0]["name"], "Sword")
        self.assertEqual(results[0]["table_name"], "equipment")
        self.assertEqual(results[1]["name"], "Potion")
        self.assertEqual(results[1]["table_name"], "consumables")

    def test_generate_monster_loot_success(self):
        col_mock = MagicMock()
        self.mock_db._col.return_value = col_mock

        # Mock random to pass the 20% check (randint > 20 -> return loot if false? No.)
        # Code: if random.randint(1, 100) > 20: return loot (which is empty list)
        # Wait, the code says:
        # if random.randint(1, 100) > 20: return loot  (Empty!)
        # So only 20% chance to GET loot?
        # Yes.

        with patch("random.randint", return_value=10): # <= 20
            # Mock aggregate
            col_mock.aggregate.return_value = [{"id": 99, "name": "Rare Drop", "rarity": "Rare", "slot": "hand"}]

            loot = self.manager.generate_monster_loot({"level": 5})

            self.assertEqual(len(loot), 1)
            self.assertEqual(loot[0]["name"], "Rare Drop")
            self.assertEqual(loot[0]["source"], "equipment")

    def test_generate_monster_loot_fail_roll(self):
        with patch("random.randint", return_value=50): # > 20
            loot = self.manager.generate_monster_loot({"level": 5})
            self.assertEqual(len(loot), 0)

    def test_format_consumable_effect_json(self):
        effect = '{"hp": 10, "mp": 5}'
        result = self.manager.format_consumable_effect(effect)
        self.assertEqual(result, "hp: 10, mp: 5")

    def test_format_consumable_effect_plain(self):
        effect = "Restores HP"
        result = self.manager.format_consumable_effect(effect)
        self.assertEqual(result, "Restores HP")

if __name__ == "__main__":
    unittest.main()
