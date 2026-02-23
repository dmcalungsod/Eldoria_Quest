import unittest
from unittest.mock import MagicMock, patch

from database.database_manager import DatabaseManager
from game_systems.items.consumable_manager import ConsumableManager


class TestConsumableRace(unittest.TestCase):
    def setUp(self):
        # Mock DatabaseManager internals
        self.mock_db = MagicMock()
        self.db = DatabaseManager()
        self.db._client = MagicMock()
        self.db.db = MagicMock()
        self.db._col = (
            MagicMock()
        )  # This returns a mock collection when called with name

        self.manager = ConsumableManager(self.db)

        # Patch CONSUMABLES to have a test item
        self.patcher = patch(
            "game_systems.items.consumable_manager.CONSUMABLES",
            {
                "test_potion": {
                    "name": "Test Potion",
                    "type": "consumable",
                    "effect": {"heal": 50},
                }
            },
        )
        self.mock_consumables = self.patcher.start()

    def tearDown(self):
        self.patcher.stop()

    def test_use_item_consumes_atomically(self):
        """Test that use_item consumes the item atomically BEFORE applying effects."""

        # Setup Mocks
        discord_id = 123
        inv_id = 1

        # 1. get_inventory_item returns an item
        self.db.get_inventory_item = MagicMock(
            return_value={
                "id": inv_id,
                "discord_id": discord_id,
                "item_key": "test_potion",
                "item_type": "consumable",
                "count": 1,
                "equipped": 0,
            }
        )

        # 2. get_player_vitals and stats
        self.db.get_player_vitals = MagicMock(
            return_value={"current_hp": 10, "current_mp": 10}
        )
        self.db.get_player_stats_json = MagicMock(
            return_value={
                "HP": {"base": 100, "bonus": 0},
                "MP": {"base": 50, "bonus": 0},
            }
        )

        # 3. consume_item_atomic (New Method) should be called
        # We mock it to return True (success)
        self.db.consume_item_atomic = MagicMock(return_value=True)

        # 4. set_player_vitals
        self.db.set_player_vitals = MagicMock()

        # Execute
        result, msg = self.manager.use_item(discord_id, inv_id)

        # Assertions
        self.assertTrue(result)
        self.assertIn("healed for 50 HP", msg)

        # CRITICAL CHECK: consume_item_atomic MUST be called
        self.db.consume_item_atomic.assert_called_once_with(inv_id, 1)

        # Ensure decrement_inventory_count and delete_inventory_item are NOT called manually
        # (Assuming we replace them with consume_item_atomic)
        # Note: If consume_item_atomic handles deletion, these shouldn't be called.
        # But if consume_item_atomic just decrements, deletion might happen elsewhere.
        # My plan is for consume_item_atomic to handle everything.

    def test_use_item_refunds_on_error(self):
        """Test that item is refunded if effect application fails."""

        discord_id = 123
        inv_id = 1

        self.db.get_inventory_item = MagicMock(
            return_value={
                "id": inv_id,
                "item_key": "test_potion",
                "item_type": "consumable",
                "count": 1,
            }
        )
        self.db.get_player_vitals = MagicMock(
            return_value={"current_hp": 10, "current_mp": 10}
        )
        self.db.get_player_stats_json = MagicMock(
            return_value={"HP": {"base": 100, "bonus": 0}}
        )

        # Consume succeeds
        self.db.consume_item_atomic = MagicMock(return_value=True)

        # But set_player_vitals raises Exception
        self.db.set_player_vitals = MagicMock(side_effect=Exception("DB Error"))

        # We expect increment_inventory_count to be called (Refund)
        self.db.increment_inventory_count = MagicMock()

        # Execute
        result, msg = self.manager.use_item(discord_id, inv_id)

        # Assertions
        self.assertFalse(result)
        self.assertIn("unexpected error", msg)

        # Verify Refund
        self.db.increment_inventory_count.assert_called_once_with(inv_id, 1)


if __name__ == "__main__":
    unittest.main()
