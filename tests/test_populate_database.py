import sys
import os
import unittest
from unittest.mock import MagicMock, patch, call

# Add repo root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

class TestPopulateDatabase(unittest.TestCase):
    def setUp(self):
        self.modules_patcher = patch.dict(sys.modules)
        self.modules_patcher.start()

        # Mock pymongo
        mock_pymongo = MagicMock()
        mock_pymongo.MongoClient = MagicMock()
        mock_pymongo.UpdateOne = MagicMock()
        mock_pymongo.errors = MagicMock()
        sys.modules["pymongo"] = mock_pymongo
        sys.modules["pymongo.errors"] = mock_pymongo.errors

        # Mock data modules to avoid dependency on actual data files and ensure controlled testing
        # We need to mock game_systems.data.*
        # But populate_database.py imports them at top level (inside try block).
        # We can just let it import real data OR mock them.
        # Mocking is safer to test logic.

        mock_data = MagicMock()
        mock_data.consumables.CONSUMABLES = {"potion": {"name": "Potion"}}
        mock_data.materials.MATERIALS = {"iron": {"name": "Iron", "description": "Metal", "rarity": "Common", "value": 10}}
        mock_data.monsters.MONSTERS = {"slime": {"name": "Slime"}}
        mock_data.quest_data.ALL_QUESTS = [{"id": 1, "title": "Quest 1", "tier": 1, "quest_giver": "NPC", "location": "Loc", "summary": "Sum", "description": "Desc", "objectives": [], "rewards": {}}]
        mock_data.quest_items.QUEST_ITEMS = {"key": {"name": "Key"}}
        mock_data.skills_data.SKILLS = {"fireball": {"key_id": "fireball", "name": "Fireball", "description": "Burn", "type": "Active"}}

        mock_data.class_data.CLASSES = {"Warrior": {"id": 1, "description": "Strong"}}
        mock_data.class_equipments.CLASS_EQUIPMENTS = {"sword": {"class": "Warrior", "name": "Sword"}}
        mock_data.equipments.EQUIPMENT_DATA = {"ring": {"name": "Ring"}}

        sys.modules["game_systems.data"] = mock_data
        sys.modules["game_systems.data.consumables"] = mock_data.consumables
        sys.modules["game_systems.data.materials"] = mock_data.materials
        sys.modules["game_systems.data.monsters"] = mock_data.monsters
        sys.modules["game_systems.data.quest_data"] = mock_data.quest_data
        sys.modules["game_systems.data.quest_items"] = mock_data.quest_items
        sys.modules["game_systems.data.skills_data"] = mock_data.skills_data
        sys.modules["game_systems.data.class_data"] = mock_data.class_data
        sys.modules["game_systems.data.class_equipments"] = mock_data.class_equipments
        sys.modules["game_systems.data.equipments"] = mock_data.equipments

        # Import
        import database.populate_database
        importlib = __import__('importlib')
        # Reload explicitly using sys.modules if attribute access fails
        importlib.reload(sys.modules["database.populate_database"])
        self.populate = sys.modules["database.populate_database"]

    def tearDown(self):
        self.modules_patcher.stop()

    def test_upsert_many(self):
        col = MagicMock()
        docs = [{"id": 1, "val": "a"}, {"id": 2, "val": "b"}]
        self.populate._upsert_many(col, "id", docs)

        col.bulk_write.assert_called_once()
        ops = col.bulk_write.call_args[0][0]
        self.assertEqual(len(ops), 2)

    def test_main(self):
        # Setup Client Mock
        mock_client = sys.modules["pymongo"].MongoClient.return_value
        mock_db = mock_client.__getitem__.return_value

        # Call main
        self.populate.main()

        # Verify db access
        # It accesses many collections
        # Check some inserts
        mock_db["monsters"].delete_many.assert_called()
        mock_db["monsters"].insert_many.assert_called()

        mock_db["consumables"].insert_many.assert_called()

        # Check upserts
        # upsert_many calls bulk_write on collection
        mock_db["classes"].bulk_write.assert_called()
        mock_db["quests"].bulk_write.assert_called()
        mock_db["materials"].bulk_write.assert_called()

    def test_insert_functions(self):
        # We can test individual functions too
        mock_db = MagicMock()

        self.populate.insert_classes(mock_db)
        mock_db["classes"].bulk_write.assert_called_once()

        self.populate.insert_monsters(mock_db)
        mock_db["monsters"].insert_many.assert_called_once()

if __name__ == "__main__":
    unittest.main()
