
import sys
import unittest
from unittest.mock import MagicMock, call, ANY

# Mock pymongo modules BEFORE importing database_manager
sys.modules["pymongo"] = MagicMock()
sys.modules["pymongo.errors"] = MagicMock()

# Ensure we can import game modules
sys.path.append(".")

from database.database_manager import DatabaseManager

class TestBuffBulkOptimization(unittest.TestCase):
    def setUp(self):
        # Reset singleton
        DatabaseManager._instance = None
        DatabaseManager._initialized = False
        self.db = DatabaseManager(mongo_uri="mongodb://mock")
        self.mock_col = MagicMock()
        self.db._col = MagicMock(return_value=self.mock_col)

    def tearDown(self):
        DatabaseManager._instance = None

    def test_add_active_buffs_bulk_ops_count(self):
        """Verify bulk add performs exactly 1 delete and 1 insert for multiple buffs."""
        buffs = [
            {"buff_id": "b1", "name": "Blessing", "stat": "STR", "amount": 10, "duration_s": 60},
            {"buff_id": "b2", "name": "Blessing", "stat": "DEX", "amount": 10, "duration_s": 60},
            {"buff_id": "b3", "name": "Shield", "stat": "DEF", "amount": 5, "duration_s": 60},
        ]
        discord_id = 12345

        self.db.add_active_buffs_bulk(discord_id, buffs)

        # Verify calls
        delete_calls = self.mock_col.delete_many.call_count
        insert_calls = self.mock_col.insert_many.call_count

        print(f"\nDelete Calls: {delete_calls}")
        print(f"Insert Calls: {insert_calls}")

        self.assertEqual(delete_calls, 1, "Should only call delete_many once")
        self.assertEqual(insert_calls, 1, "Should only call insert_many once")

        # Verify Logic
        # Delete should target all names: "Blessing" and "Shield"
        # Since set order is not guaranteed, we check that $in contains both
        call_args = self.mock_col.delete_many.call_args
        query = call_args[0][0]
        self.assertEqual(query["discord_id"], discord_id)
        self.assertIn("Blessing", query["name"]["$in"])
        self.assertIn("Shield", query["name"]["$in"])
        self.assertEqual(len(query["name"]["$in"]), 2)

        # Insert should contain 3 documents
        insert_args = self.mock_col.insert_many.call_args
        docs = insert_args[0][0]
        self.assertEqual(len(docs), 3)
        # Note: Order depends on input list order, which is preserved
        self.assertEqual(docs[0]["name"], "Blessing")
        self.assertEqual(docs[1]["name"], "Blessing")
        self.assertEqual(docs[2]["name"], "Shield")

if __name__ == "__main__":
    unittest.main()
