import os
import sys
import unittest
from unittest.mock import MagicMock, patch

# Add repo root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Mock pymongo completely
mock_pymongo = MagicMock()
mock_pymongo_errors = MagicMock()
mock_pymongo.errors = mock_pymongo_errors
sys.modules["pymongo"] = mock_pymongo
sys.modules["pymongo.errors"] = mock_pymongo_errors

# Now import modules under test
from database.database_manager import DatabaseManager  # noqa: E402
from game_systems.guild_system.guild_exchange import GuildExchange  # noqa: E402


class TestGuildExchangeSecurity(unittest.TestCase):
    def setUp(self):
        # We need to re-instantiate because DatabaseManager is a singleton
        DatabaseManager._instance = None

        self.mock_db = MagicMock(spec=DatabaseManager)
        # Mock the _col method to return a mock collection
        self.mock_collection = MagicMock()
        self.mock_db._col.return_value = self.mock_collection
        self.mock_db.db = MagicMock()  # Mock the db attribute
        self.mock_db.db.__getitem__.return_value = (
            self.mock_collection
        )  # Mock db['collection']

        # Patch DatabaseManager to avoid actual init
        with patch("database.database_manager.MongoClient"):
            self.exchange = GuildExchange(self.mock_db)

    def test_exchange_all_materials_race_condition_fix(self):
        """
        Test that exchange_all_materials uses atomic find_one_and_delete
        instead of calculate-then-delete_many to prevent race conditions.
        """
        discord_id = 12345

        # Setup mock items
        item1 = {"id": 1, "item_key": "iron_ore", "count": 5, "item_type": "material"}
        item2 = {"id": 2, "item_key": "gold_ore", "count": 2, "item_type": "material"}

        # Mock find to return items (initial scan)
        self.mock_collection.find.return_value = [item1, item2]

        # Mock find_one_and_delete to return the item (successful delete)
        # We simulate that item1 is successfully deleted, but item2 was already deleted by another process (returns None)
        self.mock_collection.find_one_and_delete.side_effect = [item1, None]

        # Mock increment_player_fields
        self.mock_db.increment_player_fields = MagicMock()

        # Mock MATERIALS data
        with patch(
            "game_systems.guild_system.guild_exchange.MATERIALS",
            {"iron_ore": {"value": 10}, "gold_ore": {"value": 50}},
        ):
            # Set db on exchange object (it's set in init but let's be sure)
            self.exchange.db = self.mock_db

            total_value, items = self.exchange.exchange_all_materials(discord_id)

            # Verify results
            # Only item1 should contribute to value: 5 * 10 = 50
            # item2 (2 * 50 = 100) should NOT contribute because find_one_and_delete returned None
            self.assertEqual(
                total_value,
                50,
                f"Expected 50 but got {total_value}. This confirms race condition fix is needed.",
            )
            self.assertEqual(len(items), 1)
            self.assertEqual(items[0]["id"], 1)

            # Verify DB calls
            # 1. find called to get IDs
            self.mock_collection.find.assert_called_with(
                {"discord_id": discord_id, "item_type": "material"}
            )

            # 2. find_one_and_delete called for each item
            self.mock_collection.find_one_and_delete.assert_any_call(
                {"id": 1, "discord_id": discord_id}
            )
            self.mock_collection.find_one_and_delete.assert_any_call(
                {"id": 2, "discord_id": discord_id}
            )

            # 3. increment_player_fields called with correct amount
            self.mock_db.increment_player_fields.assert_called_with(
                discord_id, aurum=50
            )


if __name__ == "__main__":
    unittest.main()
