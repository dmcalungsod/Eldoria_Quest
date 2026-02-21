import sys
import unittest
from unittest.mock import MagicMock

# Mock dependencies BEFORE importing modules that use them
sys.modules["pymongo"] = MagicMock()
sys.modules["pymongo.errors"] = MagicMock()
sys.modules["discord"] = MagicMock()
sys.modules["discord.ext"] = MagicMock()
sys.modules["discord.ui"] = MagicMock()
sys.modules["discord.app_commands"] = MagicMock()

# Mocking cogs/ui_helpers.py might be tricky if it imports something else
# But let's try importing MERCHANT_INVENTORY from cogs.merchant_cog
from cogs.merchant_cog import MERCHANT_INVENTORY  # noqa: E402
from database.database_manager import DatabaseManager  # noqa: E402
from game_systems.events.world_event_system import WorldEventSystem  # noqa: E402


class TestMerchantEvent(unittest.TestCase):
    def setUp(self):
        # Mock DatabaseManager methods
        self.db = MagicMock(spec=DatabaseManager)

        # Mock the real methods we want to test if we were integration testing,
        # but since we don't have a real DB, we should mock the behavior of `purchase_item`
        # OR better yet, we can't easily test `purchase_item` logic without a real DB or heavy mocking of internal DB calls.

        # However, we CAN test that `purchase_item` is CALLED correctly by the view (if we tested the view).
        # But here I want to test that `purchase_item` handles the new argument.

        # Actually, since I can't instantiate a real DatabaseManager without pymongo,
        # I have to rely on the fact that I modified `purchase_item` signature.

        # Let's verify `purchase_item` signature in `DatabaseManager` class itself
        import inspect
        sig = inspect.signature(DatabaseManager.purchase_item)
        self.assertIn("item_type", sig.parameters)
        self.assertEqual(sig.parameters["item_type"].default, "consumable")

        # Create WorldEventSystem with mocked DB
        self.event_system = WorldEventSystem(self.db)

        # Mock db.set_active_world_event
        self.db.set_active_world_event = MagicMock()
        self.db.get_active_world_event = MagicMock(return_value=None)
        self.db.end_active_world_event = MagicMock()

    def test_start_merchant_event(self):
        # Start event
        success = self.event_system.start_event(WorldEventSystem.MYSTIC_MERCHANT, 1)
        self.assertTrue(success)

        # Verify DB call
        self.db.set_active_world_event.assert_called_once()
        args, _ = self.db.set_active_world_event.call_args
        self.assertEqual(args[0], WorldEventSystem.MYSTIC_MERCHANT)

    def test_merchant_event_config(self):
        # Check config exists
        config = self.event_system.EVENT_CONFIGS.get(WorldEventSystem.MYSTIC_MERCHANT)
        self.assertIsNotNone(config)
        self.assertEqual(config["name"], "The Void Trader")
        self.assertIn("luck_boost", config["modifiers"])

    def test_inventory_contains_items(self):
        # Check inventory items
        self.assertIn("elixir_luck", MERCHANT_INVENTORY)
        self.assertIn("void_heart", MERCHANT_INVENTORY)
        self.assertIn("mythic_amber", MERCHANT_INVENTORY)

if __name__ == "__main__":
    unittest.main()
